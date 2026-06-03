from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock

from .models import Payment, Subscription

User = get_user_model()


class PaymentAPITests(APITestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            email="candidate@hireos.ai",
            password="SecurePassword123!",
            first_name="Alex",
            last_name="Lee",
            role="CANDIDATE"
        )

    @override_settings(
        SSLCOMMERZ_STORE_ID='test_store',
        SSLCOMMERZ_STORE_PASSWORD='test_password',
        SSLCOMMERZ_INIT_URL='https://sandbox.sslcommerz.com/gwprocess/v4/api.php',
        FRONTEND_URL='http://localhost:3000'
    )
    @patch('payments.views.requests.post')
    def test_candidate_can_initiate_payment(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'GatewayPageURL': 'https://sslcommerz.test/checkout'
        }
        mock_post.return_value = mock_response

        self.client.force_authenticate(user=self.candidate)
        url = reverse('payment_initiate')
        response = self.client.post(url, {'plan': 'PREMIUM'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)
        self.assertIn('transaction_id', response.data)
        self.assertEqual(response.data['payment_url'], 'https://sslcommerz.test/checkout')

        payment = Payment.objects.filter(transaction_id=response.data['transaction_id']).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.user, self.candidate)
        self.assertEqual(payment.status, 'PENDING')

    @override_settings(FRONTEND_URL='http://localhost:3000')
    def test_payment_success_activates_subscription(self):
        payment = Payment.objects.create(
            user=self.candidate,
            transaction_id='HIREOS-TEST1234',
            plan='PREMIUM',
            amount='500.00'
        )

        url = reverse('payment_success') + '?tran_id=HIREOS-TEST1234'
        response = self.client.get(url)

        payment.refresh_from_db()
        subscription = Subscription.objects.get(user=self.candidate)

        self.assertEqual(payment.status, 'SUCCESS')
        self.assertTrue(subscription.is_active)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/payment/success', response.url)

    @override_settings(FRONTEND_URL='http://localhost:3000')
    def test_payment_ipn_validates_and_activates_subscription(self):
        payment = Payment.objects.create(
            user=self.candidate,
            transaction_id='HIREOS-TESTIPN',
            plan='PREMIUM',
            amount='500.00'
        )

        url = reverse('payment_ipn')
        response = self.client.post(url, {'tran_id': 'HIREOS-TESTIPN', 'status': 'VALID'}, format='json')

        payment.refresh_from_db()
        subscription = Subscription.objects.get(user=self.candidate)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, 'SUCCESS')
        self.assertTrue(subscription.is_active)
        self.assertEqual(response.data['detail'], 'IPN received')
