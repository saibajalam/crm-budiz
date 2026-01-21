from rest_framework.views import APIView
from .serializers import (
    CreateLeadSerializer,
    LeadActivityCreateSerializer,
    LeadActivityUpdateSerializer, 
    LeadListSerializer, 
    LeadDetailSerializer,
    LeadActivityListSerializer
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import LeadActivity, Lead, LeadActivityAttachment
from subscriptions.permissions import HasActiveSubscription
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from core.pagination import LeadPagination
from rest_framework.generics import ListAPIView, RetrieveAPIView

# Create your views here.

class CreateLeadAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request):
        serializer = CreateLeadSerializer(
            data=request.data,
            context={"request": request}
            )
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
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def post(self, request):
        serializer = LeadActivityCreateSerializer(
            data=request.data,
            context={"request": request}
            )
        serializer.is_valid(raise_exception=True)

        lead = serializer.validated_data["lead"]

        activity = LeadActivity.objects.create(
        lead= lead,
        activity_type=serializer.validated_data["activity_type"],
        priority=serializer.validated_data["priority"],
        subject=serializer.validated_data["subject"],
        description=serializer.validated_data.get("description", ""),
        due_date=serializer.validated_data.get("due_date"),
        attachment=serializer.validated_data.get("attachment"),
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



class LeadListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]
    queryset = Lead.objects.all()
    serializer_class = LeadListSerializer
    pagination_class = LeadPagination

    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]

    search_fields = [
        "first_name",
        "last_name",
        "email",
        "phone",
        "company",
    ]

    filterset_fields = ["status", "source"]
    ordering_fields = ["created_at", "score"]
    ordering = ["-created_at"]


class UpdateLeadActivityAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, activity_id):
        try:
            activity = LeadActivity.objects.get(
                id=activity_id,
                performed_by=request.user
            )
        except LeadActivity.DoesNotExist:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LeadActivityUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update fields dynamically
        for field, value in serializer.validated_data.items():
            if field != "attachments":
                setattr(activity, field, value)

        activity.save()

        # Save new attachments (append only)
        attachments = request.FILES.getlist("attachments")
        for file in attachments:
            LeadActivityAttachment.objects.create(
                activity=activity,
                file=file
            )

        return Response(
            {
                "success": True,
                "message": "Activity updated successfully",
                "data": {
                    "activity_id": activity.id,
                    "attachments_added": len(attachments)
                },
                "error": None
            },
            status=status.HTTP_200_OK
        )
    


class DeleteLeadActivityAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveSubscription]

    def delete(self, request, activity_id):
        try:
            activity = LeadActivity.objects.get(
                id=activity_id,
                performed_by=request.user
            )
        except LeadActivity.DoesNotExist:
            return Response(
                {"error": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        activity.delete()

        return Response(
            {
                "success": True,
                "message": "Activity deleted successfully",
                "data": None,
                "error": None
            },
            status=status.HTTP_200_OK
        )



class LeadDetailAPIView(RetrieveAPIView) :
    permission_classes = [IsAuthenticated, HasActiveSubscription]
    queryset = Lead.objects.all()
    serializer_class = LeadDetailSerializer

    def get_queryset(self):
        return Lead.objects.select_related("created_by")
    
    lookup_field = "id"
    lookup_url_kwarg = "lead_id"


class LeadActivityListView(ListAPIView) :
    permission_classes = [IsAuthenticated, HasActiveSubscription]
    serializer_class = LeadActivityListSerializer
    pagination_class = LeadPagination

    def get_queryset(self):
        lead_id = self.kwargs.get("lead_id")
        return (
            LeadActivity.objects
            .filter(lead_id=lead_id)
            .select_related("performed_by")
            .order_by("-created_at")
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
    
        