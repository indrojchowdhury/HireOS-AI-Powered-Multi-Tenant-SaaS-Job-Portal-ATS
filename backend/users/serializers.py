from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Customizes JWT claims to include user-specific data in the token payload and response."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims into the JWT payload (for decoded state)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = user.role
        
        if hasattr(user, 'company') and user.company:
            token['company_slug'] = user.company.slug
        else:
            token['company_slug'] = None

        return token

    # this will add the same user data to the raw API response when the token is obtained, making it easier for the React frontend to access user info immediately after login without needing to decode the token on the client side.
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add explicit user_data object in the raw API response for React frontend
        data['user_data'] = {
            'username': self.user.username if hasattr(self.user, 'username') else self.user.email,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
        }
        return data

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer to handle user registration/sign-up validation and creation."""
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        """Check if the email is already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create a new user with an encrypted password using our UserManager."""
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', 'CANDIDATE') # Default to Candidate if not specified
        )
        return user   


class EmployerRegisterSerializer(serializers.Serializer):
    """
    Handles Employer registration by creating BOTH a new Company (Tenant)
    and a User linked to that company in a single transaction.
    """
    # User Fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    
    # Company Fields
    company_name = serializers.CharField(max_length=255)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        from django.db import transaction
        
        # Extract company and user data
        company_name = validated_data.pop('company_name')
        
        # Use database transaction so if one fails, both rollback
        with transaction.atomic():
            # 1. Create the Company first
            company = Company.objects.create(name=company_name)
            
            # 2. Create the User and link to the newly created company
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                role='EMPLOYER',  # Force role to Employer
                company=company   # Linking the tenant
            )
            
        return user