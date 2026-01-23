from django.urls import path
from .views import (
    CreateDealAPIView,
    RetrieveUpdateDestroyAPIView,
    DealRestoreAPIView,
    PipelineWiseDealListAPIView,
    DealAssignmentUpdateAPIView,
)

urlpatterns = [
    path("deals/", CreateDealAPIView.as_view(), name="create_deal"),
    path(
        "deals/<int:deal_id>/",
        RetrieveUpdateDestroyAPIView.as_view(),
        name="retrieve_update_delete_deal",
    ),
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
]
