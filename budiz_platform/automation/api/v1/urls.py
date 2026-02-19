from django.urls import path
from .views import (
    AutomationRuleListCreateAPIView,
    AutomationRuleDetailAPIView,
    ToggleAutomationRuleAPIView,
    AutomationLogListAPIView,
    AutomationRuleLogListAPIView,
    AutomationLogDetailAPIView,
    RetryAutomationLogAPIView,
)

urlpatterns = [
    path("rules/", AutomationRuleListCreateAPIView.as_view()),
    path("rules/<int:rule_id>/", AutomationRuleDetailAPIView.as_view()),
    path("rules/<int:rule_id>/toggle/", ToggleAutomationRuleAPIView.as_view()),
    path("logs/", AutomationLogListAPIView.as_view()),
    path("logs/<int:rule_id>/", AutomationRuleLogListAPIView.as_view()),
    path("logs/detail/<int:log_id>/", AutomationLogDetailAPIView.as_view()),
    path("logs/<int:rule_id>/retry/", RetryAutomationLogAPIView.as_view()),
]

app_name = "automation"
