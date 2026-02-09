from django.urls import path
from .views import (
    AutomationRuleListCreateAPIView,
    AutomationRuleDetailAPIView,
    ToggleAutomationRuleAPIView,
)

urlpatterns = [
    path("rules/", AutomationRuleListCreateAPIView.as_view()),
    path("rules/<int:rule_id>/", AutomationRuleDetailAPIView.as_view()),
    path("rules/<int:rule_id>/toggle/", ToggleAutomationRuleAPIView.as_view()),
]

app_name = "automation"
