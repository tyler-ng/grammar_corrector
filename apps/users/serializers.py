from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'phone_number')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                  'bio', 'profile_image', 'phone_number', 'is_admin', 
                  'is_manager', 'date_joined', 'last_login')
        read_only_fields = ('is_admin', 'is_staff', 'is_superuser', 'date_joined', 'last_login')

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                  'bio', 'profile_image', 'phone_number', 'is_admin', 
                  'is_manager', 'is_active', 'date_joined', 'last_login')
        read_only_fields = ('is_admin', 'is_staff', 'is_superuser', 'date_joined', 'last_login')