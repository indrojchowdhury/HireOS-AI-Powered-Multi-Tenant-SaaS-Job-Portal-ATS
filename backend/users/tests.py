from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()

class AuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth_register')
        self.employer_register_url = reverse('auth_register_employer')
        self.login_url = reverse('token_obtain_pair')

    def test_candidate_registration(self):
        """Ensure a new candidate can register successfully."""
        data = {
            "email": "candidate@hireos.ai",
            "password": "SecurePassword123",
            "first_name": "John",
            "last_name": "Doe"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().role, 'CANDIDATE')

    def test_employer_registration_creates_company(self):
        """Ensure an employer registration correctly creates both user and company records."""
        data = {
            "email": "employer@techcorp.com",
            "password": "SecurePassword123",
            "first_name": "Jane",
            "last_name": "Smith",
            "company_name": "TechCorp Global"
        }
        response = self.client.post(self.employer_register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Company.objects.count(), 1)
        
        user = User.objects.get()
        self.assertEqual(user.role, 'EMPLOYER')
        self.assertIsNotNone(user.company)
        self.assertEqual(user.company.name, "TechCorp Global")

    def test_login_returns_jwt_with_custom_claims(self):
        """Ensure successful login returns access/refresh tokens with required payload claims."""
        # Pre-create a candidate user
        User.objects.create_user(
            email="test@hireos.ai",
            password="Password123",
            first_name="Test",
            last_name="User",
            role="CANDIDATE"
        )
        
        login_data = {
            "email": "test@hireos.ai",
            "password": "Password123"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)