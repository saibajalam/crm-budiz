from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from leads.models import Lead
from deals.models import Deal
from workspaces.models import Workspace, WorkspaceMember

User = get_user_model()


class LeadConversionTestCase(APITestCase):
    def setUp(self):
        # Create test user and workspace
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.workspace = Workspace.objects.create(
            name="Test Workspace", created_by=self.user
        )
        WorkspaceMember.objects.create(
            workspace=self.workspace, user=self.user, role="admin"
        )

        # Create a qualified lead
        self.lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            status="qualified",
            workspace=self.workspace,
            created_by=self.user,
            display_number=1,
        )

    def test_lead_conversion_success(self):
        """Test successful conversion of qualified lead to deal"""
        self.client.force_authenticate(user=self.user)

        url = reverse("lead_convert", kwargs={"lead_id": self.lead.id})
        data = {
            "title": "Test Deal",
            "value": 10000.00,
            "probability": 75,
        }

        response = self.client.post(url, data, format="json")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        # Check lead was marked as converted
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, "converted")
        self.assertTrue(self.lead.is_converted)

        # Check deal was created
        deal = Deal.objects.get(created_from_lead=self.lead)
        self.assertEqual(deal.title, "Test Deal")
        self.assertEqual(deal.value, 10000.00)
        self.assertEqual(deal.probability, 75)
        self.assertEqual(deal.workspace, self.workspace)

    def test_lead_conversion_unqualified_fails(self):
        """Test that unqualified leads cannot be converted"""
        # Change lead status to unqualified
        self.lead.status = "new"
        self.lead.save()

        self.client.force_authenticate(user=self.user)

        url = reverse("lead_convert", kwargs={"lead_id": self.lead.id})
        data = {"title": "Test Deal"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only qualified leads can be converted", str(response.data))

    def test_lead_conversion_already_converted_fails(self):
        """Test that already converted leads cannot be converted again"""
        # Mark lead as converted
        self.lead.status = "converted"
        self.lead.is_converted = True
        self.lead.save()

        self.client.force_authenticate(user=self.user)

        url = reverse("lead_convert", kwargs={"lead_id": self.lead.id})
        data = {"title": "Test Deal"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been converted", str(response.data))
