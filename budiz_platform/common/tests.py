from django.test import TestCase, RequestFactory

from authentication.models import User, Role, UserRole
from common.permissions import IsSuperAdmin


class IsSuperAdminPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsSuperAdmin()

    def _build_request(self, user):
        request = self.factory.get("/api/create-user/")
        request.user = user
        return request

    def test_allows_django_superuser(self):
        user = User.objects.create_user(
            email="superuser@example.com",
            password="password123",
            full_name="Super User",
            phone_number="1111111111",
        )
        user.is_superuser = True
        user.save(update_fields=["is_superuser"])

        request = self._build_request(user)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_allows_global_superadmin_role(self):
        role = Role.objects.create(name="superadmin")
        user = User.objects.create_user(
            email="roleadmin@example.com",
            password="password123",
            full_name="Role Admin",
            phone_number="2222222222",
        )
        UserRole.objects.create(user=user, role=role)

        request = self._build_request(user)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_denies_non_superadmin(self):
        user = User.objects.create_user(
            email="regular@example.com",
            password="password123",
            full_name="Regular User",
            phone_number="3333333333",
        )

        request = self._build_request(user)

        self.assertFalse(self.permission.has_permission(request, None))
