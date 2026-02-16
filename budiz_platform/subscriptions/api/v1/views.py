from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from subscriptions.services import (
    activate_user_subscription,
    activate_workspace_subscription,
)
from subscriptions.services.subscription_service import (
    get_workspace_for_user,
)
from ...models import SubscriptionPlan
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .serializers import ActivateSubscriptionSerializer

# Create your views here.


class CompanyStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Company status retrieved"),
            403: OpenApiResponse(description="User does not belong to a company"),
        },
        description="Get workspace or user subscription status",
        tags=["Subscriptions"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        user = request.user
        workspace = get_workspace_for_user(user)

        if workspace:
            subscription = getattr(workspace, "subscription", None)
            return Response(
                {
                    "subscription_scope": "workspace",
                    "workspace_id": workspace.id,
                    "workspace_name": workspace.name,
                    "status": subscription.status if subscription else None,
                    "expires_at": subscription.expires_at if subscription else None,
                    "has_subscription": (
                        subscription.is_valid() if subscription else False
                    ),
                }
            )

        subscription = getattr(user, "subscription", None)
        return Response(
            {
                "subscription_scope": "user",
                "trial_active": user.is_trial_active(),
                "trial_ends_at": user.trial_ends_at,
                "status": subscription.status if subscription else None,
                "expires_at": subscription.expires_at if subscription else None,
                "has_subscription": subscription.is_valid() if subscription else False,
            }
        )


class UserStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="User subscription status retrieved"),
        },
        description="Get individual user subscription status",
        tags=["Subscriptions"],
        auth=[{"jwtAuth": []}],
    )
    def get(self, request):
        user = request.user
        subscription = getattr(user, "subscription", None)

        return Response(
            {
                "trial_active": user.is_trial_active(),
                "trial_ends_at": user.trial_ends_at,
                "status": subscription.status if subscription else None,
                "expires_at": subscription.expires_at if subscription else None,
                "is_activated": subscription.is_valid() if subscription else False,
            }
        )


class ActivateSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ActivateSubscriptionSerializer,
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
        auth=[{"jwtAuth": []}],
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
        workspace = get_workspace_for_user(user)

        if workspace:
            if workspace.owner_id != user.id:
                return Response(
                    {"error": "Only workspace owner can activate subscription"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            subscription = activate_workspace_subscription(workspace, plan)

            return Response(
                {
                    "success": True,
                    "subscription_type": "workspace",
                    "message": "Workspace subscription activated successfully",
                    "subscription_id": subscription.id,
                    "plan": plan.name,
                    "valid_till": subscription.expires_at,
                    "status_code": 200,
                    "error": None,
                },
                status=status.HTTP_200_OK,
            )

        subscription = activate_user_subscription(user, plan)

        return Response(
            {
                "success": True,
                "subscription_type": "individual",
                "message": "User subscription activated successfully",
                "subscription_id": subscription.id,
                "plan": plan.name,
                "valid_till": subscription.expires_at,
                "status_code": 200,
                "error": None,
            },
            status=status.HTTP_200_OK,
        )
