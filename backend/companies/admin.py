from django.contrib import admin
from .models import Company

class CompanyAdmin(admin.ModelAdmin):
    """Configuration for Company model in Django admin panel."""
    list_display = ('name', 'slug', 'website', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # Auto-fills slug as you type name in admin

admin.site.register(Company, CompanyAdmin)