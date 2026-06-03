from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from users.views import CustomTokenObtainPairView, RegisterView, EmployerRegisterView  

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication API Endpoints
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/register-employer/', EmployerRegisterView.as_view(), name='auth_register_employer'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Include App Endpoints
    path('', include('companies.urls')),
    path('', include('jobs.urls')),
    path('', include('payments.urls')),
]

# Serve media files during development (Crucial for PDF resume uploads)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
