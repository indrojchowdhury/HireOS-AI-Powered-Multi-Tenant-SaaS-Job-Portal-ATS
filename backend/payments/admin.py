from django.contrib import admin

from .models import Payment, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'started_at', 'expires_at')
    list_filter = ('plan', 'is_active')
    search_fields = ('user__email',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('transaction_id', 'user__email')
