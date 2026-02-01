from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse


class SubscriptionRequiredMiddleware:

    EXEMPT_PATHS = [
        "/api/register/",
        "/api/login/",
        "/api/company_status/",
        "/api/activate_subscription/",
    ]

    """
    Blocks API access if company trial & subscription are inactive
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in self.EXEMPT_PATHS:
            return self.get_response(request)

        user = request.user

        # Allow unauthenticated requests
        if not user.is_authenticated:
            return self.get_response(request)

       # Company user
        if hasattr(user, "company") and user.company:
            subscription = getattr(user.company, "subscription", None)

            if not subscription or not subscription.is_valid():
                return JsonResponse(
                    {"detail": "Company subscription expired"},
                    status=403
                )

        # Individual user
        else:
            subscription = getattr(user, "subscription", None)

            if not subscription or not subscription.is_valid():
                return JsonResponse(
                    {"detail": "User subscription expired"},
                    status=403
                )

        return self.get_response(request)

