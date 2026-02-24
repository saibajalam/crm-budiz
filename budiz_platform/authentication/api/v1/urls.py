from django.urls import path
from .views import (
    LoginAPIView,
    SuperAdminDashboardAPIView,
    AdminDashboardAPIView,
    ManagerDashboardAPIView,
    SalesDashboardAPIView,
    UserCreateAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
    VerifyEmailAPIView,
    ResendVerificationAPIView,
    RegisterAPI,
)

urlpatterns = [
    path("register/", RegisterAPI.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="api-login"),
    path(
        "superadmin/", SuperAdminDashboardAPIView.as_view(), name="superadmin_dashboard"
    ),
    path("admin/", AdminDashboardAPIView.as_view(), name="admin_dashboard"),
    path("manager/", ManagerDashboardAPIView.as_view(), name="manager_dashboard"),
    path("sales/", SalesDashboardAPIView.as_view(), name="sales_dashboard"),
    path("create-user/", UserCreateAPIView.as_view(), name="create_user"),
    path("forgot-password/", ForgotPasswordAPIView.as_view()),
    path("reset-password/", ResetPasswordAPIView.as_view()),
    path("verify-email/", VerifyEmailAPIView.as_view()),
    path("resend-verification/", ResendVerificationAPIView.as_view()),
]
