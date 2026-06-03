import uuid

import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, Subscription
from .serializers import SubscriptionSerializer


class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription, _ = Subscription.objects.get_or_create(user=request.user)
        return Response(SubscriptionSerializer(subscription).data)


class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'CANDIDATE':
            return Response(
                {"detail": "Only candidates can buy a premium subscription."},
                status=status.HTTP_403_FORBIDDEN
            )

        plan = request.data.get('plan', 'PREMIUM')
        amount = '500.00'
        transaction_id = f"HIREOS-{uuid.uuid4().hex[:12].upper()}"

        Payment.objects.create(
            user=request.user,
            transaction_id=transaction_id,
            plan=plan,
            amount=amount,
        )

        success_url = request.build_absolute_uri('/api/payments/success/')
        fail_url = request.build_absolute_uri('/api/payments/fail/')
        cancel_url = request.build_absolute_uri('/api/payments/cancel/')
        ipn_url = request.build_absolute_uri('/api/payments/ipn/')

        payload = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
            'total_amount': amount,
            'currency': 'BDT',
            'tran_id': transaction_id,
            'success_url': success_url,
            'fail_url': fail_url,
            'cancel_url': cancel_url,
            'ipn_url': ipn_url,
            'cus_name': request.user.get_full_name() or request.user.email,
            'cus_email': request.user.email,
            'cus_add1': 'Dhaka',
            'cus_city': 'Dhaka',
            'cus_country': 'Bangladesh',
            'cus_phone': '01700000000',
            'shipping_method': 'NO',
            'product_name': 'HireOS Premium Subscription',
            'product_category': 'Subscription',
            'product_profile': 'non-physical-goods',
        }

        try:
            ssl_response = requests.post(settings.SSLCOMMERZ_INIT_URL, data=payload, timeout=20)
            data = ssl_response.json()
        except Exception as exc:
            return Response(
                {"detail": f"Could not connect to SSLCommerz: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        payment_url = data.get('GatewayPageURL')
        if not payment_url:
            return Response(
                {"detail": "SSLCommerz did not return a payment URL.", "gateway_response": data},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"payment_url": payment_url, "transaction_id": transaction_id})


class PaymentSuccessView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        return self.complete_payment(request.data)

    def get(self, request):
        return self.complete_payment(request.GET)

    def complete_payment(self, data):
        transaction_id = data.get('tran_id')
        payment = Payment.objects.filter(transaction_id=transaction_id).first()

        if payment:
            payment.status = 'SUCCESS'
            payment.gateway_response = dict(data)
            payment.save()

            subscription, _ = Subscription.objects.get_or_create(user=payment.user)
            subscription.activate_premium()

        return redirect(f"{settings.FRONTEND_URL}/payment/success?tran_id={transaction_id or ''}")


class PaymentIpnView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        transaction_id = request.data.get('tran_id')
        payment_status = request.data.get('status')
        payment = Payment.objects.filter(transaction_id=transaction_id).first()

        if payment and payment_status in ['VALID', 'VALIDATED']:
            payment.status = 'SUCCESS'
            payment.gateway_response = dict(request.data)
            payment.save()

            subscription, _ = Subscription.objects.get_or_create(user=payment.user)
            subscription.activate_premium()

        return Response({"detail": "IPN received"})


class PaymentFailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        return self.fail_payment(request.data)

    def get(self, request):
        return self.fail_payment(request.GET)

    def fail_payment(self, data):
        transaction_id = data.get('tran_id')
        payment = Payment.objects.filter(transaction_id=transaction_id).first()

        if payment:
            payment.status = 'FAILED'
            payment.gateway_response = dict(data)
            payment.save()

        return redirect(f"{settings.FRONTEND_URL}/payment/fail?tran_id={transaction_id or ''}")


class PaymentCancelView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        return self.cancel_payment(request.data)

    def get(self, request):
        return self.cancel_payment(request.GET)

    def cancel_payment(self, data):
        transaction_id = data.get('tran_id')
        payment = Payment.objects.filter(transaction_id=transaction_id).first()

        if payment:
            payment.status = 'CANCELLED'
            payment.gateway_response = dict(data)
            payment.save()

        return redirect(f"{settings.FRONTEND_URL}/payment/cancel?tran_id={transaction_id or ''}")
