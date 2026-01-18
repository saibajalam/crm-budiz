from rest_framework.views import APIView
from .serializers import AddLeadSerializer, LeadActivityCreateSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import LeadActivity, Lead

# Create your views here.

class AddLeadAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AddLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Lead created successfully",
                "data": {
                    "id": lead.id,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "status": lead.status,
                    "source": lead.source,
                }
            },
            status=status.HTTP_201_CREATED
        )


class CreateLeadActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LeadActivityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead = Lead.objects.get(id=serializer.validated_data["lead_id"])

        activity = LeadActivity.objects.create(
            lead=lead,
            activity_type=serializer.validated_data["activity_type"],
            priority=serializer.validated_data["priority"],
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data.get("description", ""),
            due_date=serializer.validated_data.get("due_date"),
            performed_by=request.user,
        )

        # Update lead score
        from leads.utils import update_lead_score
        update_lead_score(lead, activity.activity_type)

        return Response(
            {
                "success": True,
                "message": "Activity created successfully",
                "data": {
                    "activity_id": activity.id,
                    "lead_score": lead.score
                },
                "error": None
            },
            status=status.HTTP_201_CREATED
        )