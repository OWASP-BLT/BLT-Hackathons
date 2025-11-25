"""
Django Hackathon Plugin - Admin Configuration

This module configures Django admin interface for hackathon models.
It handles optional Organization model dependency.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Hackathon,
    HackathonSponsor, 
    HackathonPrize,
    Contributor,
    GitHubIssue,
    HAS_ORGANIZATION
)


@admin.register(Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    """Admin interface for Hackathon model."""
    
    list_display = ['name', 'start_time', 'end_time', 'max_participants', 'is_ongoing', 'has_ended']
    list_filter = ['start_time', 'end_time', 'is_online', 'registration_open']
    search_fields = ['name', 'description', 'theme', 'location']
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'start_time'
    ordering = ['-start_time']
    
    # Add organization to display and filters only if available
    if HAS_ORGANIZATION:
        list_display.insert(1, 'get_organization_name')
        list_filter.append('organization')
        search_fields.append('organization__name')
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug', 'description', 'theme']
        }),
        ('Schedule', {
            'fields': ['start_time', 'end_time', 'location', 'is_online']
        }),
        ('Settings', {
            'fields': ['max_participants', 'max_team_size', 'registration_open']
        }),
        ('Content', {
            'fields': ['image', 'rules', 'prizes_total']
        }),
        ('Links', {
            'fields': ['registration_link', 'submission_link', 'sponsor_link', 'sponsor_note']
        }),
    ]
    
    # Add organization field only if available
    if HAS_ORGANIZATION:
        fieldsets[0][1]['fields'].insert(-1, 'organization')
    else:
        fieldsets[0][1]['fields'].insert(-1, 'owner')
    
    def get_organization_name(self, obj):
        """Display organization name if available."""
        if HAS_ORGANIZATION and hasattr(obj, 'organization') and obj.organization:
            return obj.organization.name
        elif hasattr(obj, 'owner'):
            return f"Owner: {obj.owner.username}"
        return "No organization"
    get_organization_name.short_description = 'Organization'
    
    def is_ongoing(self, obj):
        """Display if hackathon is currently ongoing."""
        return obj.is_ongoing
    is_ongoing.boolean = True
    is_ongoing.short_description = 'Ongoing'
    
    def has_ended(self, obj):
        """Display if hackathon has ended.""" 
        return obj.has_ended
    has_ended.boolean = True
    has_ended.short_description = 'Ended'


@admin.register(HackathonSponsor)
class HackathonSponsorAdmin(admin.ModelAdmin):
    """Admin interface for HackathonSponsor model."""
    
    list_display = ['sponsor_name', 'hackathon', 'sponsor_level', 'website']
    list_filter = ['sponsor_level', 'hackathon', 'created']
    search_fields = ['sponsor_name', 'hackathon__name']
    date_hierarchy = 'created'
    ordering = ['hackathon', 'sponsor_level', 'sponsor_name']
    
    # Add organization to display only if available
    if HAS_ORGANIZATION:
        list_display.insert(1, 'get_organization_name')
        list_filter.append('organization')
        search_fields.append('organization__name')
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['hackathon', 'sponsor_name', 'sponsor_level']
        }),
        ('Details', {
            'fields': ['logo', 'website']
        }),
    ]
    
    # Add organization field only if available
    if HAS_ORGANIZATION:
        fieldsets[0][1]['fields'].insert(-2, 'organization')
    
    def get_organization_name(self, obj):
        """Display organization name if available."""
        if HAS_ORGANIZATION and hasattr(obj, 'organization') and obj.organization:
            return obj.organization.name
        return "Direct sponsor"
    get_organization_name.short_description = 'Organization'


@admin.register(HackathonPrize)
class HackathonPrizeAdmin(admin.ModelAdmin):
    """Admin interface for HackathonPrize model."""
    
    list_display = ['title', 'hackathon', 'get_position_display', 'value', 'sponsor']
    list_filter = ['position', 'hackathon']
    search_fields = ['title', 'description', 'hackathon__name']
    ordering = ['hackathon', 'position']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['hackathon', 'position', 'title']
        }),
        ('Details', {
            'fields': ['description', 'value', 'sponsor']
        }),
    ]


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    """Admin interface for Contributor model."""
    
    list_display = ['name', 'github_id', 'contributor_type', 'contributions', 'created']
    list_filter = ['contributor_type', 'created']
    search_fields = ['name', 'github_id', 'github_url']
    date_hierarchy = 'created'
    ordering = ['-contributions', 'name']
    
    fieldsets = [
        ('GitHub Information', {
            'fields': ['name', 'github_id', 'github_url', 'avatar_url']
        }),
        ('Stats', {
            'fields': ['contributor_type', 'contributions']
        }),
    ]
    
    def github_link(self, obj):
        """Display clickable GitHub link."""
        if obj.github_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.github_url, obj.name)
        return obj.name
    github_link.short_description = 'GitHub Profile'


@admin.register(GitHubIssue)
class GitHubIssueAdmin(admin.ModelAdmin):
    """Admin interface for GitHubIssue model."""
    
    list_display = ['title', 'github_id', 'issue_type', 'state', 'author', 'created_at']
    list_filter = ['issue_type', 'state', 'created_at', 'updated_at']
    search_fields = ['title', 'github_id', 'github_url', 'author__name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = [
        ('GitHub Information', {
            'fields': ['title', 'github_id', 'github_url', 'issue_type']
        }),
        ('Status', {
            'fields': ['state', 'author', 'closed_by']
        }),
        ('Metadata', {
            'fields': ['labels', 'created_at', 'updated_at', 'closed_at']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def github_link(self, obj):
        """Display clickable GitHub link."""
        if obj.github_url:
            return format_html('<a href="{}" target="_blank">#{}</a>', obj.github_url, obj.github_id)
        return f"#{obj.github_id}"
    github_link.short_description = 'GitHub Link'


# Admin site configuration
admin.site.site_header = 'Hackathon Plugin Administration'
admin.site.site_title = 'Hackathon Plugin Admin'
admin.site.index_title = 'Welcome to Hackathon Plugin Administration'