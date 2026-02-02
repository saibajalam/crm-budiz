from django.urls import path
from .views import (
    LeadListCreateAPIView,
    LeadRetrieveUpdateDeleteAPIView,
    LeadActivityListCreateAPIView,
    LeadActivityRetrieveUpdateDeleteAPIView,
    LeadRestoreAPIView,
    LeadActivityRestoreAPIView,
    LeadActivityFeedAPIView,
    LeadConversionAPIView,
)

urlpatterns = [
    # Leads
    path(
        "leads/", LeadListCreateAPIView.as_view(), name="lead_list_create"
    ),  # GET=list, POST=create
    path(
        "leads/<int:lead_id>/",
        LeadRetrieveUpdateDeleteAPIView.as_view(),
        name="lead_detail_update_delete",
    ),  # GET/PUT/PATCH/DELETE
    # Lead Activities (nested under lead)
    path(
        "leads/<int:lead_id>/activities/",
        LeadActivityListCreateAPIView.as_view(),
        name="lead_activity_list_create",
    ),  # GET=list, POST=create
    path(
        "leads/<int:lead_id>/activities/<int:activity_id>/",
        LeadActivityRetrieveUpdateDeleteAPIView.as_view(),
        name="lead_activity_detail_update_delete",
    ),  # GET/PUT/PATCH/DELETE
    path(
        "leads/<int:lead_id>/restore/",
        LeadRestoreAPIView.as_view(),
        name="restore_lead",
    ),
    path(
        "leads/activities/<int:activity_id>/restore/",
        LeadActivityRestoreAPIView.as_view(),
        name="restore_activity",
    ),
    path(
        "leads/<int:lead_id>/activity-feed/",
        LeadActivityFeedAPIView.as_view(),
        name="lead_activity_feed",
    ),
    path(
        "leads/<int:lead_id>/convert/",
        LeadConversionAPIView.as_view(),
        name="lead_convert",
    ),
]
