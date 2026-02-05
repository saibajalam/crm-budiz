from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from ...models import Form, FormSubmission, FormResponse
from ...api.v1.serailizers import (
    PublicFormSubmitSerializer,
    CreateFormSerializer,
    AddFieldSerializer,
    UpdateFormAssignmentSerializer,
)
from rest_framework.response import Response
from leads.models import Lead
from deals.models import Deal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from workspaces.permissions import IsWorkspaceMember
from workspaces.utils import get_user_workspace
import uuid
from ...utils import get_round_robin_user
from django.contrib.auth import get_user_model
from subscriptions.permissions import HasActiveSubscription

# Create your views here.

User = get_user_model()


class PublicFormSubmitAPIView(APIView):
    permission_classes = []

    def post(self, request, slug):
        form = get_object_or_404(Form, slug=slug, is_active=True)
        workspace = form.workspace

        data = request.data.get("data", {})

        # Extract mapped values
        lead_data = {}

        for field in form.fields.all():
            if field.label in data:
                value = data[field.label]

                if field.map_to_lead_field != "none":
                    lead_data[field.map_to_lead_field] = value

        email = lead_data.get("email")
        phone = lead_data.get("phone")

        lead = None

        # DUPLICATE HANDLING
        if form.duplicate_handling == "update":
            lead = Lead.objects.filter(workspace=workspace, email=email).first()

        elif form.duplicate_handling == "configurable":
            lead = (
                Lead.objects.filter(workspace=workspace)
                .filter(Q(email=email) | Q(phone=phone))
                .first()
            )

        # CREATE OR UPDATE LEAD
        if not lead:
            lead = Lead.objects.create(
                workspace=workspace, created_by=None, **lead_data
            )
        else:
            for key, value in lead_data.items():
                setattr(lead, key, value)
            lead.save()

        # ASSIGNMENT LOGIC
        assignee = None

        if form.assignment_type == "fixed" and form.fixed_assignee:
            assignee = form.fixed_assignee

        elif form.assignment_type == "round_robin":
            assignee = get_round_robin_user(form)

        if assignee:
            lead.assigned_to = assignee
            lead.save(update_fields=["assigned_to"])

        # CREATE SUBMISSION
        submission = FormSubmission.objects.create(
            form=form,
            workspace=workspace,
            lead=lead,
        )

        # STORE RESPONSES
        for field in form.fields.all():
            if field.label in data:
                FormResponse.objects.create(
                    submission=submission,
                    field=field,
                    value=data[field.label],
                )

        return Response(
            {
                "success": True,
                "message": "Form submitted successfully",
            }
        )


class CreateFormAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    def post(self, request):
        workspace = get_user_workspace(request.user)

        serializer = CreateFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = serializer.save(
            workspace=workspace, created_by=request.user, slug=str(uuid.uuid4())[:10]
        )

        return Response(serializer.data, status=201)


class AddFieldAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    def post(self, request, form_id):
        workspace = get_user_workspace(request.user)

        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        serializer = AddFieldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(form=form)

        return Response(serializer.data, status=201)


class UpdateFormAssignmentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    def patch(self, request, form_id):
        workspace = get_user_workspace(request.user)
        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        serializer = UpdateFormAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        form.assignment_type = data["assignment_type"]

        if data["assignment_type"] == "fixed":
            user = User.objects.get(id=data["fixed_assignee_id"])
            form.fixed_assignee = user

        if data["assignment_type"] == "round_robin":
            users = User.objects.filter(id__in=data["round_robin_user_ids"])
            form.round_robin_users.set(users)

        form.save()

        return Response({"success": True})


class FormEmbedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, form_id):
        form = get_object_or_404(Form, id=form_id)

        embed_code = f"""
<script>
fetch("https://api.yourcrm.com/public/forms/{form.slug}/submit/", {{
 method: "POST",
 headers: {{ "Content-Type": "application/json" }},
 body: JSON.stringify({{
   data: {{
     "Full Name": "",
     "Email": "",
     "Phone": ""
   }}
 }})
}});
</script>
"""

        return Response({"embed_code": embed_code})


class FormConversionFunnelAPIView(APIView):
    permission_classes = [IsAuthenticated, IsWorkspaceMember, HasActiveSubscription]

    def get(self, request, form_id):
        workspace = get_user_workspace(request.user)
        form = get_object_or_404(Form, id=form_id, workspace=workspace)

        days = int(request.query_params.get("days", 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 🔹 submissions
        submissions_qs = FormSubmission.objects.filter(
            form=form,
            submitted_at__date__range=[start_date, end_date],
        )

        submissions_count = submissions_qs.count()

        # 🔹 leads
        lead_ids = submissions_qs.exclude(lead=None).values_list("lead_id", flat=True)

        leads_count = len(set(lead_ids))

        # 🔹 deals
        deals_qs = Deal.objects.filter(
            workspace=workspace,
            lead_id__in=lead_ids,
        )

        deals_count = deals_qs.count()

        # 🔹 won deals
        won_qs = deals_qs.filter(pipeline_stage="won")
        won_count = won_qs.count()

        revenue = won_qs.aggregate(total=Sum("value"))["total"] or 0

        # 🔹 conversion rates
        submission_to_lead = (
            (leads_count / submissions_count) * 100 if submissions_count else 0
        )

        lead_to_deal = (deals_count / leads_count) * 100 if leads_count else 0

        deal_to_won = (won_count / deals_count) * 100 if deals_count else 0

        return Response(
            {
                "form_id": form.id,
                "form_name": form.name,
                "period_days": days,
                "submissions": submissions_count,
                "leads": leads_count,
                "deals": deals_count,
                "won": won_count,
                "revenue": revenue,
                "rates": {
                    "submission_to_lead": round(submission_to_lead, 2),
                    "lead_to_deal": round(lead_to_deal, 2),
                    "deal_to_won": round(deal_to_won, 2),
                },
            }
        )
