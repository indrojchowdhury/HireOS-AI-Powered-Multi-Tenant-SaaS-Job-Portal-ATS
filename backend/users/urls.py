from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, EmployerRegisterView, CustomTokenObtainPairView

urlpatterns = [
    # Login & Token Endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Registration Endpoints
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('register/employer/', EmployerRegisterView.as_view(), name='auth_register_employer'),
]