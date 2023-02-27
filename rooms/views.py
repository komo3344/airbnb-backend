from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.filters import YearFilter, MonthFilter, DayFilter
from bookings.models import Booking
from bookings.serializers import PublicBookingSerializer, CreateRoomBookingSerializer
from medias.serializers import PhotoSerializer
from reviews.serializers import ReviewSerializer
from rooms import serializers
from rooms.models import Amenity, Room


class Amenities(APIView):
    def get(self, request):
        all_amenities = Amenity.objects.all()
        serializer = serializers.AmenitySerializer(all_amenities, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = serializers.AmenitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AmenityDetail(APIView):
    def get_object(self, pk):
        return get_object_or_404(Amenity, pk=pk)

    def get(self, request, pk):
        amenity = self.get_object(pk)
        serializer = serializers.AmenitySerializer(amenity)
        return Response(serializer.data)

    def put(self, request, pk):
        amenity = self.get_object(pk)
        serializer = serializers.AmenitySerializer(
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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]
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

    # TODO 예약을 한 적이 있어야 리뷰를 남길 수 있도록
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
        serializer = serializers.AmenitySerializer(queryset_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RoomPhotos(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Room, pk=pk)

    def post(self, request, pk):
        room = self.get_object(pk)
        if request.user != room.owner:
            raise PermissionDenied
        serializer = PhotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(room=room)
        return Response(serializer.data)


class RoomBookings(GenericAPIView):

    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Booking.objects.all()
    serializer_class = PublicBookingSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DayFilter, MonthFilter, YearFilter]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRoomBookingSerializer
        return self.serializer_class

    def get_object(self, **kwargs):
        return get_object_or_404(Room, pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        room = self.get_object()
        paginator = self.pagination_class()

        bookings = Booking.objects.filter(
            room=room,
            kind=Booking.BookingKindChoices.ROOM,
        )
        filter_queryset = self.filter_queryset(bookings)
        queryset_page = paginator.paginate_queryset(filter_queryset, request)
        serializer = self.get_serializer(queryset_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        room = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"room": room})
        serializer.is_valid(raise_exception=True)
        booking = serializer.save(
            room=room,
            user=request.user,
            kind=Booking.BookingKindChoices.ROOM,
        )
        serializer = PublicBookingSerializer(booking)
        return Response(serializer.data)

    def delete(self, request):
        # TODO 예약 취소
        pass
