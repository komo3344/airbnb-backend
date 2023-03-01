from rest_framework.serializers import ModelSerializer

from experiences.serializers import ExperienceWishListSerializer
from rooms.serializers import RoomListSerializer
from .models import Wishlist


class WishlistSerializer(ModelSerializer):

    rooms = RoomListSerializer(
        many=True,
        read_only=True,
    )

    experiences = ExperienceWishListSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Wishlist
        fields = (
            "pk",
            "name",
            "rooms",
            "experiences",
        )
