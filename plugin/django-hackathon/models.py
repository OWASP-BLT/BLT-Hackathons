from django.db import models
from django.utils import timezone
from django.utils.text import slugify   
from organization.models import Organization

class Hackathon(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    description = models.TextField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="hackathons")
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
    repositories = models.ManyToManyField(Repo, related_name="hackathons", blank=True)
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
                user_id = pr.user_profile.user.id
                if user_id in leaderboard:
                    leaderboard[user_id]["count"] += 1
                    leaderboard[user_id]["prs"].append(pr)
                else:
                    leaderboard[user_id] = {"user": pr.user_profile.user, "count": 1, "prs": [pr]}
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
