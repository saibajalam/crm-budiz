from django.urls import path

from .views import LegacyContactDetailAPIView, LegacyContactListAPIView

urlpatterns = [
    # Deprecated aliases. Canonical endpoints are routed from core router at /api/contacts/.
    path("legacy/contacts/", LegacyContactListAPIView.as_view(), name="contact-list-create"),
    path(
        "legacy/contacts/<int:pk>/",
        LegacyContactDetailAPIView.as_view(),
        name="contact-detail",
    ),
]

app_name = "contact"