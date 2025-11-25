from django.urls import path, include

from .views import (
    HackathonListView,
    HackathonDetailView,    
    HackathonCreateView,
    HackathonUpdateView,
    HackathonSponsorCreateView,
    HackathonPrizeCreateView,
    refresh_repository_data,
    refresh_all_hackathon_repositories,
    add_org_repos_to_hackathon,
)

urlPatterns = [
     path(
        "/",
        include(
            [
                path("", HackathonListView.as_view(), name="hackathons"),
                path("create/", HackathonCreateView.as_view(), name="hackathon_create"),
                path("<slug:slug>/", HackathonDetailView.as_view(), name="hackathon_detail"),
                path("<slug:slug>/edit/", HackathonUpdateView.as_view(), name="hackathon_update"),
                path("<slug:slug>/add-sponsor/", HackathonSponsorCreateView.as_view(), name="hackathon_sponsor_create"),
                path("<slug:slug>/add-prize/", HackathonPrizeCreateView.as_view(), name="hackathon_prize_create"),
                # Add the new URL pattern for refreshing repository data
                path(
                    "<slug:hackathon_slug>/refresh-repo/<int:repo_id>/",
                    refresh_repository_data,
                    name="refresh_repository_data",
                ),
                path(
                    "<slug:slug>/refresh-all-repos/",
                    refresh_all_hackathon_repositories,
                    name="refresh_all_hackathon_repositories",
                ),
                # Add the new URL pattern for adding all org repos to hackathon
                path(
                    "<slug:slug>/add-org-repos/",
                    add_org_repos_to_hackathon,
                    name="add_org_repos_to_hackathon",
                ),
            ]
        ),
    ),   
]