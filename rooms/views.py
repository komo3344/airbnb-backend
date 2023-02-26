from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.serializers import ReviewSerializer
from rooms import serializers
from rooms.models import Amenity, Room
from rooms.serializers import AmenitySerializer


class Amenities(APIView):
    def get(self, request):
        all_amenities = Amenity.objects.all()
        serializer = AmenitySerializer(all_amenities, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AmenitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AmenityDetail(APIView):
    def get_object(self, pk):
        return get_object_or_404(Amenity, pk=pk)

    def get(self, request, pk):
        amenity = self.get_object(pk)
        serializer = AmenitySerializer(amenity)
        return Response(serializer.data)

    def put(self, request, pk):
        amenity = self.get_object(pk)
        serializer = AmenitySerializer(
            amenity,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        amenity = self.get_object(pk)
        amenity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Rooms(APIView):
    def get(self, request):
        all_rooms = Room.objects.all()
        serializer = serializers.RoomListSerializer(
            all_rooms,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = serializers.RoomDetailSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=self.request.user)
        return Response(serializer.data)


class RoomDetail(APIView):
    def get_object(self, pk):
        return get_object_or_404(Room, pk=pk)

    def get(self, request, pk):
        room = self.get_object(pk)
        serializer = serializers.RoomDetailSerializer(
            room,
            context={"request": request},
        )
        return Response(serializer.data)

    def put(self, request, pk):
        room = self.get_object(pk)
        if room.owner != request.user:
            raise PermissionDenied

        serializer = serializers.RoomDetailSerializer(
            room,
            data=request.data,
            context={"request": request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=self.request.user)
        return Response(serializer.data)

    def delete(self, request, pk):
        room = self.get_object(pk)
        if room.owner != request.user:
            raise PermissionDenied
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomReviews(APIView):
    pagination_class = PageNumberPagination

    def get_object(self, pk):
        return get_object_or_404(Room, pk=pk)

    def get(self, request, pk):
        # try:
        #     page = request.query_params.get("page", 1)
        #     page = int(page)
        # except ValueError:
        #     page = 1
        # page_size = settings.PAGE_SIZE
        # start = (page - 1) * page_size
        # end = start + page_size
        # room = self.get_object(pk)
        # serializer = ReviewSerializer(
        #     room.reviews.all()[start:end],
        #     many=True,
        # )
        room = self.get_object(pk)
        reviews = room.reviews.all()
        paginator = self.pagination_class()
        queryset_page = paginator.paginate_queryset(reviews, request)
        serializer = ReviewSerializer(queryset_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, room=self.get_object(pk))
        return Response(serializer.data)


class RoomAmenities(APIView):
    pagination_class = PageNumberPagination

    def get_object(self, pk):
        return get_object_or_404(Room, pk=pk)

    def get(self, request, pk):
        room = self.get_object(pk)
        amenities = room.amenities.all()
        paginator = self.pagination_class()
        queryset_page = paginator.paginate_queryset(amenities, request)
        serializer = AmenitySerializer(queryset_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RoomPhotos(APIView):
    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def post(self, request, pk):
        room = self.get_object(pk)
        if not request.user.is_authenticated:
            raise NotAuthenticated
        if request.user != room.owner:
            raise PermissionDenied
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(room=room)
            serializer = PhotoSerializer(photo)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
