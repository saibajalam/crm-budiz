from django.urls import path
from .views import AddLeadAPIView, CreateLeadActivityAPIView

urlpatterns = [
    path("leads/", AddLeadAPIView.as_view(), name="add-lead"),
    path("lead-activity/", CreateLeadActivityAPIView.as_view(), name="create-leadActivity"),
]
