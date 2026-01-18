from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role, UserRole, PasswordResetToken, EmailVerificationToken


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)
    phone_number = serializers.CharField(max_length=15)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Auto-assign sales_representative role
        role = Role.objects.get(name="sales_representative")
        UserRole.objects.create(user=user, role=role)

        return user



class LoginSerializers(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            email = data["email"],
            password = data["password"]
        )

        if not user :
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.is_email_verified:
            raise serializers.ValidationError(
                "Email is not verified. Please check your email."
            )

        data["user"] = user
        return data
    


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length = 15)
    role_id = serializers.IntegerField()
    

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role_id")
        return value

    def create(self, validated_data):
        role_id = validated_data.pop("role_id")
        password = validated_data.pop("password")

        user = User.objects.create_user(
        email=validated_data["email"],
        password=password,
        full_name=validated_data["full_name"],
        phone_number=validated_data["phone_number"]
        )
        
        role = Role.objects.get(id=role_id)
        UserRole.objects.create(user=user, role=role)

        return user
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist")
        return value
    


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8)



class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()



class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        if user.is_email_verified:
            raise serializers.ValidationError("Email already verified")

        self.user = user 
        return value
    

