from rest_framework import serializers
from users.serializers import TinyUserSerializer
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):

    user = TinyUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = (
            "user",
            "payload",
            "rating",
        )

    def validate(self, attrs):
        rating = attrs.get("rating")
        if rating < 1:
            raise serializers.ValidationError("1점 이상만 줄 수 있습니다.")

    def create(self, validated_data):
        return Review.objects.create(**validated_data)
