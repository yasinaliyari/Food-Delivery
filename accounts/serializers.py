from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ("id", "role")


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This username is already registered.",
            )
        ],
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email has already been registered.",
            )
        ]
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})
    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES, default=User.ROLE_CUSTOMER
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Repeat password does not match."}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["role"] = user.role
        return token
