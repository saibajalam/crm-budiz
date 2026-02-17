from rest_framework.permissions import BasePermission
from .services.subscription_service import has_active_subscription_for_request


class HasActiveSubscription(BasePermission):
    message = "Your trial or subscription has expired. Please subscribe."

    def has_permission(self, request, view):
        return has_active_subscription_for_request(request)
