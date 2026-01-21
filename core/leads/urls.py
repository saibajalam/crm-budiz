from django.urls import path
from .views import (
    CreateLeadAPIView, 
    CreateLeadActivityAPIView, 
    UpdateLeadActivityAPIView, 
    DeleteLeadActivityAPIView, 
    LeadListAPIView, 
    LeadDetailAPIView,
    LeadActivityListView
)

urlpatterns = [
    path("leads/", CreateLeadAPIView.as_view(), name="add_lead"),
    path("lead-activity/", CreateLeadActivityAPIView.as_view(), name="create_leadActivity"),
    path("update-leadActivity/", UpdateLeadActivityAPIView.as_view(), name="update_leadActivity"),
    path("delete-leadActivity/", DeleteLeadActivityAPIView.as_view(), name="delete_leadActivity"),
    path("lead_list/", LeadListAPIView.as_view(), name="lead_list"),
    path("leads/<lead_id>/", LeadDetailAPIView.as_view(), name="lead_detail_list"),
    path("lead-activity/<lead_id>", LeadActivityListView.as_view(), name="lead_activity_list")
]
