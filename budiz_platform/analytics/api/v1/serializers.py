from rest_framework import serializers
from ...models import DealAnalytics, UserAnalytics

# The serializers for the analytics API endpoints is not used in the current implementation but is defined here for the future use.


class DealAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for workspace-level deal analytics"""

    class Meta:
        model = DealAnalytics
        fields = [
            "id",
            "workspace",
            "date",
            "total_deals",
            "total_value",
            "won_deals",
            "won_value",
            "lost_deals",
            "pipeline_value",
            "leads_converted",
            "conversion_rate",
            "total_leads_qualified",
        ]
        read_only_fields = ["id", "workspace", "date"]


class UserAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for user performance analytics"""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserAnalytics
        fields = [
            "id",
            "user",
            "user_name",
            "user_email",
            "workspace",
            "date",
            "deals_created",
            "deals_closed",
            "revenue_generated",
            "activities_completed",
            "leads_converted",
            "conversion_value",
        ]
        read_only_fields = ["id", "user_name", "user_email"]


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for analytics summary/dashboard data"""

    # Deal metrics
    total_deals = serializers.IntegerField()
    total_pipeline_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    won_deals = serializers.IntegerField()
    won_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    lost_deals = serializers.IntegerField()
    win_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Lead conversion metrics
    leads_converted = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_qualified_leads = serializers.IntegerField()

    # User metrics
    active_users = serializers.IntegerField()
    total_activities = serializers.IntegerField()
    avg_deals_per_user = serializers.DecimalField(max_digits=5, decimal_places=2)

    # Trends (compared to previous period)
    deals_growth = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )
    revenue_growth = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )
