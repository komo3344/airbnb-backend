from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from categories.models import Category
from categories.serializers import CategorySerializer
from medias.serializers import PhotoSerializer
from users.serializers import TinyUserSerializer
from wishlists.models import Wishlist
from .models import Amenity, Room


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


class RoomDetailSerializer(serializers.ModelSerializer):
    owner = TinyUserSerializer(read_only=True)
    amenities = AmenitySerializer(
        read_only=True,
        many=True,
    )

    # category 필드를 PrimaryKeyRelatedField로 정의하여 CategorySerializer를 사용합니다.
    category = PrimaryKeyRelatedField(queryset=Category.objects.all())
    rating = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = "__all__"

    def get_rating(self, room):
        return room.rating()

    def get_is_owner(self, room):
        request = self.context["request"]
        return room.owner == request.user

    def get_is_liked(self, room):
        request = self.context["request"]
        return Wishlist.objects.filter(user=request.user, rooms__pk=room.pk).exists()

    def validate(self, data):
        category = data.get("category")
        if category and category.kind != Category.CategoryKindChoices.ROOMS:
            raise serializers.ValidationError("The category kind should be 'rooms'")
        return data

    def create(self, validated_data):
        amenities = self.context['request'].data.get("amenities", None)
        room = Room.objects.create(**validated_data)

        if amenities:
            amenity_objs = Amenity.objects.filter(id__in=amenities)
            room.amenities.set(amenity_objs)

        # try:
        #     with transaction.atomic():
        #         room = Room.objects.create(**validated_data)
        #         for amenity_pk in amenities:
        #             amenity = Amenity.objects.get(pk=amenity_pk)
        #             room.amenities.add(amenity)
        #
        # except Exception as e:
        #     raise ParseError("Amenity not found")

        return room

    def update(self, instance, validated_data):
        category = validated_data.pop("category", None)
        if category:
            instance.category = category

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        amenities = self.context['request'].data.get("amenities", None)

        if amenities:
            amenity_objs = Amenity.objects.filter(id__in=amenities)
            instance.amenities.set(amenity_objs)

        return instance

    def to_representation(self, instance):
        # RoomCreateSerializer의 to_representation 메서드를 오버라이드하여 category 필드를 CategorySerializer로 변경합니다.
        data = super().to_representation(instance)
        data['category'] = CategorySerializer(instance.category).data
        return data


class RoomListSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = (
            "pk",
            "name",
            "country",
            "city",
            "price",
            "rating",
            "is_owner",
            "photos",
        )

    def get_rating(self, room):
        return room.rating()

    def get_is_owner(self, room):
        request = self.context["request"]
        return room.owner == request.user
