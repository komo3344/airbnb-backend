from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import User


class TinyUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            "name",
            "avatar",
            "username",
        )


class PrivateUserSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "avatar",
            "name",
            "is_host",
            "gender",
            "language",
            "currency",
            "password"
        ]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class PublicUserSerializer(serializers.ModelSerializer):
    total_reviews = serializers.SerializerMethodField()
    total_rooms = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "avatar",
            "name",
            "is_host",
            "gender",
            "language",
            "currency",
            "total_reviews",
            "total_rooms",
        ]

    def get_total_reviews(self, user):
        return user.total_reviews()

    def get_total_rooms(self, user):
        return user.total_rooms()

