from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ...services import activate_subscription
from ...models import SubscriptionPlan, Company
from rest_framework import status
from subscriptions.services import (
    activate_subscription,
    activate_user_subscription,
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

# Create your views here.


class CompanyStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Company status retrieved"),
            403: OpenApiResponse(description="User does not belong to a company"),
        },
        description="Get company trial and subscription status",
        tags=["Subscriptions"],
    )
    def get(self, request):
        if not hasattr(request.user, "owned_company"):
            return Response({"error": "User does not belong to a company"}, status=403)

        company = request.user.owned_company

        return Response(
            {
                "trial_active": company.is_trial_active(),
                "trial_ends_at": company.trial_ends_at,
                "has_subscription": company.has_active_subscription(),
            }
        )


class ActivateSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="plan_id",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Subscription plan ID",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Subscription activated"),
            400: OpenApiResponse(description="Invalid plan_id"),
            404: OpenApiResponse(description="Plan not found"),
        },
        description="Activate a subscription plan for user or company",
        tags=["Subscriptions"],
    )
    def post(self, request):
        plan_id = request.data.get("plan_id")

        if not plan_id:
            return Response(
                {"error": "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = SubscriptionPlan.objects.get(plan_id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Invalid plan_id"}, status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # Company subscription
        if hasattr(user, "company") and user.company:
            company = user.company

            subscription = activate_subscription(company, plan)

            return Response(
                {
                    "success": True,
                    "subscription_type": "company",
                    "message": "Company subscription activated successfully",
                    "subscription_id": subscription.id,
                    "plan": plan.name,
                    "valid_till": subscription.ends_at,
                    "status_code": 200,
                    "error": None,
                },
                status=status.HTTP_200_OK,
            )

        # Individual user subscription
        subscription = activate_user_subscription(user, plan)

        return Response(
            {
                "success": True,
                "subscription_type": "individual",
                "message": "User subscription activated successfully",
                "subscription_id": subscription.id,
                "plan": plan.name,
                "valid_till": subscription.ends_at,
                "status_code": 200,
                "error": None,
            },
            status=status.HTTP_200_OK,
        )
