from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import BaseUser

from .models import BackofficeAdmin


class RegisterAdminPermissionTests(APITestCase):
    def setUp(self):
        self.url = reverse("register_admin")
        self.payload = {
            "email": "new-admin@example.com",
            "password": "A-strong-test-password-123!",
            "username": "newadmin",
            "first_name": "New",
            "last_name": "Admin",
            "phone_number": "+237600000001",
        }

    def test_anonymous_user_cannot_register_admin(self):
        response = self.client.post(self.url, self.payload, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(BackofficeAdmin.objects.filter(email=self.payload["email"]).exists())

    def test_non_admin_user_cannot_register_admin(self):
        user = BaseUser.objects.create(
            email="client@example.com",
            user_type="client",
            is_active=True,
        )
        user.set_password("A-strong-test-password-123!")
        user.save(update_fields=["password"])
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self.payload, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(BackofficeAdmin.objects.filter(email=self.payload["email"]).exists())

    def test_backoffice_admin_can_register_another_admin(self):
        admin = BackofficeAdmin.objects.create(
            email="existing-admin@example.com",
            username="existingadmin",
            first_name="Existing",
            last_name="Admin",
            phone_number="+237600000000",
            user_type="admin",
            is_active=True,
        )
        admin.set_password("A-strong-test-password-123!")
        admin.save(update_fields=["password"])
        self.client.force_authenticate(user=admin)

        response = self.client.post(self.url, self.payload, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BackofficeAdmin.objects.filter(email=self.payload["email"]).exists())
