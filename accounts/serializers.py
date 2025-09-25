from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ("id", "role")
