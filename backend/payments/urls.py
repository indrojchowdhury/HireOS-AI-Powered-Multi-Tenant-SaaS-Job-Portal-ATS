from django.urls import path

from .views import (
    PaymentCancelView,
    PaymentFailView,
    PaymentInitiateView,
    PaymentIpnView,
    PaymentSuccessView,
    SubscriptionStatusView,
)

urlpatterns = [
    path('api/subscription/status/', SubscriptionStatusView.as_view(), name='subscription_status'),
    path('api/payments/initiate/', PaymentInitiateView.as_view(), name='payment_initiate'),
    path('api/payments/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('api/payments/fail/', PaymentFailView.as_view(), name='payment_fail'),
    path('api/payments/cancel/', PaymentCancelView.as_view(), name='payment_cancel'),
    path('api/payments/ipn/', PaymentIpnView.as_view(), name='payment_ipn'),
]
