from rest_framework import serializers


class ActivateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.CharField()
