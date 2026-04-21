from django.urls import path
from .views import (
    DealRestoreAPIView,
    PipelineWiseDealListAPIView,
    DealAssignmentUpdateAPIView,
    DealActivityFeedAPIView,
    CreateDealActivityAPIView,
    DealActivityRetrieveUpdateDestroyAPIView,
    RestoreDealActivityAPIView,
    DealContactListCreateAPIView,
    DealContactDeleteAPIView,
)

urlpatterns = [
    # Canonical /api/deals/ CRUD is served via core router.
    path(
        "deals/<int:deal_id>/restore/",
        DealRestoreAPIView.as_view(),
        name="restore_deal",
    ),
    path(
        "deals/pipeline/", PipelineWiseDealListAPIView.as_view(), name="pipeline_deals"
    ),
    path(
        "deals/<int:deal_id>/assign/",
        DealAssignmentUpdateAPIView.as_view(),
        name="update_deal_assignment",
    ),
    path(
        "deals/<int:deal_id>/activity-feed/",
        DealActivityFeedAPIView.as_view(),
        name="deal_activity_feed",
    ),
    path(
        "deals/<int:deal_id>/activities/",
        CreateDealActivityAPIView.as_view(),
        name="create_deal_activity",
    ),
    path(
        "deals/<int:deal_id>/activities/<int:pk>/",
        DealActivityRetrieveUpdateDestroyAPIView.as_view(),
        name="retrieve_update_delete_deal_activity",
    ),
    path(
        "deals/<int:deal_id>/activities/<int:activity_id>/restore/",
        RestoreDealActivityAPIView.as_view(),
        name="restore_deal_activity",
    ),
    path(
        "deals/<int:deal_id>/contacts/",
        DealContactListCreateAPIView.as_view(),
        name="deal-contacts-list-create",
    ),
    path(
        "deals/<int:deal_id>/contacts/<int:contact_id>/",
        DealContactDeleteAPIView.as_view(),
        name="deal-contacts-delete",
    ),
]
