from django.urls import path
from .views import CompanyStatusAPIView, ActivateSubscriptionAPIView

urlpatterns = [
    path("company_status/", CompanyStatusAPIView.as_view(), name="company_status"),
    path("activate_subscription/", ActivateSubscriptionAPIView.as_view(), name="activate_subscription"),
]