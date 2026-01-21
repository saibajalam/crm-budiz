from rest_framework.permissions import BasePermission
from django.utils import timezone
from .models import CompanySubscription

class HasActiveSubscription(BasePermission):
    message = "Your trial or subscription has expired. Please subscribe."

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        company = getattr(user, "company", None)

        # Company user
        if company:
            if company.is_trial_active():
                return True

            subscription = company.subscriptions.filter(is_active=True).first()
            if subscription and subscription.is_valid():
                return True

            return False

        # Individual user
        if user.is_trial_active():
            return True

        subscription = user.subscriptions.filter(is_active=True).first()
        if subscription and subscription.is_valid():
            return True

        return False
