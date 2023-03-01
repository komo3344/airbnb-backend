from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from categories.models import Category
from categories.serializers import CategorySerializer
from medias.serializers import PhotoSerializer, VideoSerializer
from reviews.serializers import ReviewSerializer
from wishlists.models import Wishlist
from .models import Perk, Experience


class PerkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perk
        fields = "__all__"


class ExperienceWishListSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(
        read_only=True,
        many=True,
    )
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = [
            "pk",
            "name",
            "price",
            "photos",
            "is_liked",
        ]

    def get_is_liked(self, experience):
        owner = self.context["request"].user
        return Wishlist.objects.filter(owner=owner, experiences__pk=experience.pk).exists()


class ExperienceSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)
    video = VideoSerializer(required=False, source="videos")

    class Meta:
        model = Experience
        fields = [
            "pk",
            "name",
            "country",
            "city",
            "price",
            "rating",
            "is_owner",
            "is_liked",
            "photos",
            "video",
            "start",
            "end",
        ]

    def get_rating(self, experience):
        return experience.rating()

    def get_is_owner(self, experience):
        request = self.context["request"]
        return experience.host == request.user

    def get_is_liked(self, experience):
        request = self.context["request"]
        return Wishlist.objects.filter(user=request.user, experiences__pk=experience.pk).exists()

    def create(self, validated_data):
        experience = Experience.objects.create(host=self.context["request"].user, **validated_data)
        return experience


class ExperienceDetailSerializer(serializers.ModelSerializer):
    category = PrimaryKeyRelatedField(queryset=Category.objects.all())
    perks = serializers.PrimaryKeyRelatedField(queryset=Perk.objects.all(), many=True)
    rating = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, read_only=True)
    video = VideoSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Experience
        fields = [
            "pk",
            "country",
            "city",
            "name",
            "host",
            "price",
            "address",
            "start",
            "end",
            "description",
            "perks",
            "category",
            "rating",
            "is_owner",
            "is_liked",
            "photos",
            "video",
            "reviews",
        ]

    def get_rating(self, experience):
        return experience.rating()

    def get_is_owner(self, experience):
        request = self.context["request"]
        return experience.host == request.user

    def get_is_liked(self, experience):
        request = self.context["request"]
        return Wishlist.objects.filter(user=request.user, experiences__pk=experience.pk).exists()

    def validate(self, data):
        category = data.get("category")
        if category and category.kind != Category.CategoryKindChoices.EXPERIENCES:
            raise serializers.ValidationError("The category kind should be 'experiences'")
        return data

    def create(self, validated_data):
        perks = self.context['request'].data.get("perks", None)
        experience = Experience.objects.create(**validated_data)

        if perks:
            perk_objs = Perk.objects.filter(id__in=perks)
            experience.perks.set(perk_objs)

        return experience

    def update(self, instance, validated_data):
        category = validated_data.pop("category", None)
        if category:
            instance.category = category

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        perks = self.context['request'].data.get("perks", None)

        if perks:
            perk_objs = Experience.objects.filter(id__in=perks)
            instance.perks.set(perk_objs)

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = CategorySerializer(instance.category).data
        data['perks'] = PerkSerializer(instance.perks, many=True).data
        return data
