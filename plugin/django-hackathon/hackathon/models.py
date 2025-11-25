from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.apps import apps
from django.conf import settings


# Dynamic Organization model handling
# Check if external Organization model exists in parent project
def get_organization_model():
    """
    Get Organization model from parent project if available.
    Returns None if not found, making organization features optional.
    """
    try:
        # Try to get Organization model from various possible app names
        for app_name in ['website', 'organization', 'organizations', 'core']:
            try:
                return apps.get_model(app_name, 'Organization')
            except LookupError:
                continue
        return None
    except Exception:
        return None


# Check if organization features are enabled
HAS_ORGANIZATION = get_organization_model() is not None
Organization = get_organization_model()


class Repository(models.Model):
    """
    Repository model for storing GitHub repository information.
    TODO: Make this configurable to use external Repo model if available.
    """
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    repo_url = models.URLField()
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["owner", "name"]
        unique_together = ("owner", "name")
        indexes = [
            models.Index(fields=["owner", "name"], name="hackathon_repo_owner_name_idx"),
        ]
    
    def __str__(self):
        return f"{self.owner}/{self.name}"


class Contributor(models.Model):
    """
    Contributor model for storing GitHub contributor information.
    TODO: Make this configurable to use external Contributor model if available.
    """
    CONTRIBUTOR_TYPES = [
        ("User", "User"),
        ("Bot", "Bot"),
        ("Organization", "Organization"),
    ]
    
    name = models.CharField(max_length=255)
    github_id = models.CharField(max_length=50, unique=True)
    github_url = models.URLField()
    avatar_url = models.URLField(blank=True, null=True)
    contributor_type = models.CharField(max_length=20, choices=CONTRIBUTOR_TYPES, default="User")
    contributions = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-contributions", "name"]
    
    def __str__(self):
        return self.name


class GitHubIssue(models.Model):
    """
    GitHub Issue/PR model for tracking contributions.
    TODO: Make this configurable to use external GitHubIssue model if available.
    """
    ISSUE_TYPES = [
        ("issue", "Issue"),
        ("pull_request", "Pull Request"),
    ]
    
    issue_id = models.PositiveIntegerField()
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="issues")
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=ISSUE_TYPES, default="issue")
    contributor = models.ForeignKey(Contributor, on_delete=models.SET_NULL, null=True, blank=True)
    user_profile = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    is_merged = models.BooleanField(default=False)
    github_url = models.URLField()
    
    class Meta:
        ordering = ["-created_at"]
        unique_together = ("issue_id", "repo")
        indexes = [
            models.Index(fields=["type", "is_merged"], name="hackathon_issue_type_merged_idx"),
            models.Index(fields=["created_at"], name="hackathon_issue_created_idx"),
            models.Index(fields=["merged_at"], name="hackathon_issue_merged_idx"),
        ]
    
    def __str__(self):
        return f"#{self.issue_id} - {self.title}"


class Hackathon(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    description = models.TextField()
    # Organization field - only available if Organization model exists in parent project
    organization = models.ForeignKey(
        'website.Organization' if HAS_ORGANIZATION else 'auth.User',
        on_delete=models.CASCADE,
        related_name="hackathons" if HAS_ORGANIZATION else "owned_hackathons",
        help_text="Organization hosting the hackathon" if HAS_ORGANIZATION else "User hosting the hackathon"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    banner_image = models.ImageField(upload_to="hackathon_banners", null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    rules = models.TextField(blank=True, null=True)
    registration_open = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    # Link to repositories that are part of this hackathon
    repositories = models.ManyToManyField(Repository, related_name="hackathons", blank=True)
    # Sponsor information
    sponsor_note = models.TextField(
        blank=True, null=True, help_text="Additional information about sponsorship opportunities"
    )
    sponsor_link = models.URLField(blank=True, null=True, help_text="Link to sponsorship information or application")

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["start_time"], name="hackathon_start_idx"),
            models.Index(fields=["organization"], name="hackathon_org_idx"),
        ]
        constraints = [models.UniqueConstraint(fields=["slug"], name="unique_hackathon_slug")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    @property
    def has_ended(self):
        return timezone.now() > self.end_time

    @property
    def has_started(self):
        return timezone.now() >= self.start_time

    @property
    def time_remaining(self):
        if self.has_ended:
            return "Ended"
        elif not self.has_started:
            return f"Starts in {(self.start_time - timezone.now()).days} days"
        else:
            remaining = self.end_time - timezone.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            return f"{days} days, {hours} hours remaining"

    @property
    def status_badge_class(self):
        """Returns CSS classes for the status badge based on hackathon status."""
        if self.is_ongoing:
            return "bg-green-100 text-green-800"
        elif self.has_ended:
            return "bg-gray-100 text-gray-800"
        else:
            return "bg-blue-100 text-blue-800"

    @property
    def status_text(self):
        """Returns the status text for display."""
        if self.is_ongoing:
            return "Ongoing"
        elif self.has_ended:
            return "Ended"
        else:
            return "Upcoming"

    def get_leaderboard(self):
        """
        Generate a leaderboard of contributors based on merged pull requests
        during the hackathon timeframe.
        """
        # Get all merged pull requests from the hackathon's repositories within the timeframe
        pull_requests = GitHubIssue.objects.filter(
            repo__in=self.repositories.all(),
            type="pull_request",
            is_merged=True,
            merged_at__gte=self.start_time,
            merged_at__lte=self.end_time,
        )

        # Group by user_profile and count PRs
        leaderboard = {}
        for pr in pull_requests:
            if pr.user_profile:
                user_id = pr.user_profile.id
                if user_id in leaderboard:
                    leaderboard[user_id]["count"] += 1
                    leaderboard[user_id]["prs"].append(pr)
                else:
                    leaderboard[user_id] = {"user": pr.user_profile, "count": 1, "prs": [pr]}
            elif pr.contributor and pr.contributor.github_id:
                # Skip bot accounts - check contributor_type field (primary) and name patterns (fallback)
                if pr.contributor.contributor_type == "Bot":
                    continue
                github_username = pr.contributor.name
                if github_username and (github_username.endswith("[bot]") or "bot" in github_username.lower()):
                    continue

                # If no user profile but has contributor, use contributor as key
                contributor_id = f"contributor_{pr.contributor.id}"
                if contributor_id in leaderboard:
                    leaderboard[contributor_id]["count"] += 1
                    leaderboard[contributor_id]["prs"].append(pr)
                else:
                    leaderboard[contributor_id] = {
                        "user": {
                            "username": pr.contributor.name or pr.contributor.github_id,
                            "email": "",
                            "id": contributor_id,
                        },
                        "count": 1,
                        "prs": [pr],
                        "is_contributor": True,
                        "contributor": pr.contributor,  # Include the contributor object
                    }

        # Convert to list and sort by count (descending)
        leaderboard_list = list(leaderboard.values())
        leaderboard_list.sort(key=lambda x: x["count"], reverse=True)

        return leaderboard_list


class HackathonSponsor(models.Model):
    SPONSOR_LEVELS = [
        ("platinum", "Platinum"),
        ("gold", "Gold"),
        ("silver", "Silver"),
        ("bronze", "Bronze"),
        ("partner", "Partner"),
    ]
    
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, related_name="sponsors")
    # Sponsor name field (always available)
    sponsor_name = models.CharField(max_length=255, help_text="Sponsor organization name")
    sponsor_level = models.CharField(max_length=20, choices=SPONSOR_LEVELS, default="partner")
    logo = models.ImageField(upload_to="hackathon_sponsor_logos", null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sponsor_level", "created"]
        unique_together = ("hackathon", "sponsor_name")

    def __str__(self):
        return f"{self.sponsor_name} - {self.get_sponsor_level_display()} sponsor for {self.hackathon.name}"

    def get_display_name(self):
        """Return the sponsor name, preferring organization name if available."""
        if HAS_ORGANIZATION and hasattr(self, 'organization') and self.organization:
            return self.organization.name
        return self.sponsor_name


# Add Organization field dynamically if Organization model exists
if HAS_ORGANIZATION:
    HackathonSponsor.add_to_class(
        'organization',
        models.ForeignKey(
            Organization,
            on_delete=models.CASCADE,
            related_name="sponsored_hackathons",
            null=True, blank=True,
            help_text="Link to organization if available"
        )
    )


class HackathonPrize(models.Model):
    PRIZE_POSITIONS = [
        (1, "First Place"),
        (2, "Second Place"),
        (3, "Third Place"),
        (4, "Special Prize"),
    ]
    
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, related_name="prizes")
    position = models.PositiveIntegerField(choices=PRIZE_POSITIONS)
    title = models.CharField(max_length=255)
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sponsor = models.ForeignKey(
        HackathonSponsor, on_delete=models.SET_NULL, null=True, blank=True, related_name="prizes"
    )

    class Meta:
        ordering = ["position"]
        unique_together = ("hackathon", "position")

    def __str__(self):
        return f"{self.get_position_display()} - {self.title} ({self.hackathon.name})"