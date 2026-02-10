from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate

from .serializers import (
    LoginSerializers,
    UserCreateSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer,
    RegisterSerializer,
)
from ...decorators import role_required
from ...models import User, PasswordResetToken, EmailVerificationToken
from ...utils import send_verification_email
from django.utils import timezone
from datetime import timedelta
from accounts.jobs.emails_verification import resend_email_verification
from common.permissions import IsSuperAdmin, IsAdmin
from subscriptions.permissions import HasActiveSubscription


class RegisterAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        response_data = {
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "full_name": result["user"].full_name,
            }
        }

        if result["type"] == "company":
            response_data["company"] = {
                "id": result["company"].id,
                "name": result["company"].company_name,
            }

        return Response(
            {
                "success": True,
                "message": "Registration successful",
                "data": response_data,
                "error": None,
            },
            status=status.HTTP_201_CREATED,
        )


# Login API jwt based


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login Successfull",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": list(user.get_roles()),
                    "is_active": user.is_active,
                },
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class UserCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(created_by=request.user)

        return Response(
            {
                "message": "User created successfully",
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone_number": user.phone_number,
                    "roles": list(user.get_roles()),
                },
                "success": True,
                "error": None,
                "status_code": status.HTTP_201_CREATED,
            },
            status=status.HTTP_201_CREATED,
        )


class ForgotPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data["email"])
        reset_token = PasswordResetToken.objects.create(user=user)

        # Later: send via email
        return Response(
            {
                "message": "Password reset token generated",
                "reset_token": str(reset_token.token),
                "success": True,
                "error": None,
                "status_code": 200,
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token_obj = PasswordResetToken.objects.get(
                token=serializer.validated_data["token"], is_used=False
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {
                    "error": "Invalid or used token",
                    "success": False,
                    "status_code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_expired():
            return Response(
                {"error": "Token expired", "success": False, "status_code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        token_obj.is_used = True
        token_obj.save()

        return Response(
            {
                "message": "Password reset successful",
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token_obj = EmailVerificationToken.objects.get(
                token=serializer.validated_data["token"], is_used=False
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {
                    "error": "Invalid or used token",
                    "success": False,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_expired():
            return Response(
                {"error": "Token expired", "success": False, "status_code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user
        user.is_email_verified = True
        user.save()

        token_obj.is_used = True
        token_obj.save()

        return Response(
            {
                "message": "Email verified successfully",
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class ResendVerificationAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        token = resend_email_verification(user)

        return Response(
            {
                "message": "Verification email resent",
                "verification_token": str(token),
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


# role based API


class SuperAdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @role_required("superadmin")
    def get(self, request):
        return Response(
            {
                "message": "Welcome to SuperAdmin Dashboard",
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            }
        )


class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @role_required("admin")
    def get(self, request):
        return Response(
            {
                "message": "Welcome to Admin Dashboard",
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            }
        )


class ManagerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @role_required("manager")
    def get(self, request):
        return Response(
            {
                "message": "Welcome to Manager Dashboard",
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            }
        )


class SalesDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @role_required("sales_representative")
    def get(self, request):
        return Response(
            {
                "message": "Welcome to Sales Dashboard",
                "success": True,
                "error": None,
                "status_code": status.HTTP_200_OK,
            }
        )
