from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import GlobalActivityListAPIView, GlobalSearchAPIView
from deals.api.v1.views import DealViewSet
from contact.api.v1.views import ContactViewSet

router = DefaultRouter(trailing_slash=True)
router.register("deals", DealViewSet, basename="deals")
router.register("contacts", ContactViewSet, basename="contacts")

urlpatterns = [
    path("activities/", GlobalActivityListAPIView.as_view(), name="global-activities"),
    path("search/", GlobalSearchAPIView.as_view(), name="global-search"),
]

urlpatterns += router.urls
