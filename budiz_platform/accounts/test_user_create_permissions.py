from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from accounts.models import Role, UserRole
from workspaces.models import Workspace, WorkspaceMember

User = get_user_model()


class UserCreatePermissionTestCase(APITestCase):
    """Test cases for /api/create-user/ endpoint permissions"""

    def setUp(self):
        # Create roles
        self.superadmin_role, _ = Role.objects.get_or_create(
            name="superadmin", defaults={"description": "Super Admin"}
        )
        self.admin_role, _ = Role.objects.get_or_create(
            name="admin", defaults={"description": "Admin"}
        )
        self.sales_role, _ = Role.objects.get_or_create(
            name="sales_representative", defaults={"description": "Sales Rep"}
        )

        # Create a workspace
        self.workspace = Workspace.objects.create(
            name="Test Workspace", slug="test-workspace"
        )

        # Create users
        self.superadmin_user = User.objects.create_user(
            email="superadmin@example.com",
            password="testpass123",
            full_name="Super Admin",
            phone_number="+1234567890",
        )
        self.superadmin_user.is_superuser = True
        self.superadmin_user.save()
        UserRole.objects.create(user=self.superadmin_user, role=self.superadmin_role)

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            full_name="Admin User",
            phone_number="+1234567891",
        )
        UserRole.objects.create(user=self.admin_user, role=self.admin_role)
        WorkspaceMember.objects.create(
            workspace=self.workspace, user=self.admin_user, role="admin"
        )

        self.sales_user = User.objects.create_user(
            email="sales@example.com",
            password="testpass123",
            full_name="Sales User",
            phone_number="+1234567892",
        )
        UserRole.objects.create(user=self.sales_user, role=self.sales_role)
        WorkspaceMember.objects.create(
            workspace=self.workspace, user=self.sales_user, role="sales"
        )

    def test_superadmin_can_create_user(self):
        """Test that superadmin can create users"""
        self.client.force_authenticate(user=self.superadmin_user)

        url = reverse("create_user")
        data = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "newpass123",
            "phone_number": "+1234567893",
            "role_id": self.sales_role.id,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get("success"))
        self.assertIn("User created successfully", response.data.get("message", ""))

    def test_admin_can_create_user(self):
        """Test that admin can create users"""
        self.client.force_authenticate(user=self.admin_user)

        # Set workspace in request to simulate middleware
        url = reverse("create_user")
        data = {
            "email": "newadminuser@example.com",
            "full_name": "New Admin User",
            "password": "newpass123",
            "phone_number": "+1234567894",
            "role_id": self.sales_role.id,
        }

        response = self.client.post(url, data, format="json")

        # Admin should now have permission after fix
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get("success"))

    def test_sales_user_cannot_create_user(self):
        """Test that sales representative cannot create users"""
        self.client.force_authenticate(user=self.sales_user)

        url = reverse("create_user")
        data = {
            "email": "newsalesuser@example.com",
            "full_name": "New Sales User",
            "password": "newpass123",
            "phone_number": "+1234567895",
            "role_id": self.sales_role.id,
        }

        response = self.client.post(url, data, format="json")

        # Sales rep should not have permission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_user(self):
        """Test that unauthenticated users cannot create users"""
        url = reverse("create_user")
        data = {
            "email": "unautheduser@example.com",
            "full_name": "Unauthed User",
            "password": "newpass123",
            "phone_number": "+1234567896",
            "role_id": self.sales_role.id,
        }

        response = self.client.post(url, data, format="json")

        # Unauthenticated should get 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
