from django.db import models
from django.utils.text import slugify

class Company(models.Model):
    """
    Represents a Company (Tenant) in the Multi-tenant SaaS system.
    Each company will have its own isolated data (jobs, candidates, etc.).
    """
    name = models.CharField(max_length=255)
    
    # Subdomain or URL-friendly identifier (e.g., 'google' for google.hireos.ai)
    slug = models.SlugField(unique=True, max_length=255)
    
    # Optional company details
    website = models.URLField(max_length=200, blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status to quickly activate/deactivate a tenant (e.g., subscription expiry)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Auto-generate a unique slug from the company name if not provided."""
        if not self.slug:
            base_slug = slugify(self.name) or 'company'
            slug = base_slug
            counter = 1

            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name