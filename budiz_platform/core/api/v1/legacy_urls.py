from django.urls import path

from contact.api.v1.views import LegacyContactDetailAPIView, LegacyContactListAPIView
from deals.api.v1.views import LegacyDealDetailAPIView, LegacyDealListAPIView

urlpatterns = [
    # Deprecated legacy endpoints. Prefer canonical lowercase routes under /api/.
    path("deals/", LegacyDealListAPIView.as_view(), name="legacy-deals-list"),
    path("deals/<int:pk>/", LegacyDealDetailAPIView.as_view(), name="legacy-deals-detail"),
    path("contacts/", LegacyContactListAPIView.as_view(), name="legacy-contacts-list"),
    path(
        "contacts/<int:pk>/",
        LegacyContactDetailAPIView.as_view(),
        name="legacy-contacts-detail",
    ),
]
