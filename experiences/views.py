from django.utils import timezone
from rest_framework import status
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking
from bookings.serializers import PublicBookingSerializer, CreateExperienceBookingSerializer
from medias.models import Video
from medias.serializers import PhotoSerializer, VideoSerializer
from reviews.serializers import ReviewSerializer
from .models import Perk, Experience
from .serializers import PerkSerializer, ExperienceSerializer, ExperienceDetailSerializer


class Perks(APIView):
    def get(self, request):
        all_perks = Perk.objects.all()
        serializer = PerkSerializer(all_perks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PerkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PerkDetail(APIView):
    def get_object(self, pk):
        return get_object_or_404(Perk, pk=pk)

    def get(self, request, pk):
        perk = self.get_object(pk)
        serializer = PerkSerializer(perk)
        return Response(serializer.data)

    def put(self, request, pk):
        perk = self.get_object(pk)
        serializer = PerkSerializer(perk, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.errors)

    def delete(self, request, pk):
        perk = self.get_object(pk)
        perk.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Experiences(generics.ListCreateAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ExperiencesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ExperiencePerks(generics.ListAPIView):
    queryset = Perk.objects.all()
    serializer_class = PerkSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(experiences__pk=self.kwargs["pk"])
        return queryset


class ExperienceReviews(APIView):
    pagination_class = PageNumberPagination

    def get_object(self, pk):
        return get_object_or_404(Experience, pk=pk)

    def get(self, request, pk):
        experience = self.get_object(pk)
        reviews = experience.reviews.all()
        paginator = self.pagination_class()
        queryset_page = paginator.paginate_queryset(reviews, request)
        serializer = ReviewSerializer(queryset_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExperiencePhotos(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Experience, pk=pk)

    def post(self, request, pk):
        experience = self.get_object(pk)
        if request.user != experience.host:
            raise PermissionDenied
        serializer = PhotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(experience=experience)
        return Response(serializer.data)


class ExperienceVideo(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Experience, pk=pk)

    def post(self, request, pk):
        experience = self.get_object(pk)
        if request.user != experience.host:
            raise PermissionDenied
        if Video.objects.filter(experience=experience).exists():
            raise ParseError("비디오가 이미 있습니다.")
        serializer = VideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(experience=experience)
        return Response(serializer.data)


class ExperienceBookings(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Booking.objects.all()
    serializer_class = PublicBookingSerializer
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateExperienceBookingSerializer
        return self.serializer_class

    def get_object(self, **kwargs):
        return get_object_or_404(Experience, pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        experience = self.get_object()
        paginator = self.pagination_class()

        now = timezone.localtime(timezone.now()).date()
        bookings = Booking.objects.filter(
            experience=experience,
            kind=Booking.BookingKindChoices.EXPERIENCE,
            experience_time__gte=now,
        )
        filter_queryset = self.filter_queryset(bookings)
        queryset_page = paginator.paginate_queryset(filter_queryset, request)
        serializer = self.get_serializer(queryset_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        experience = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"experience": experience})
        serializer.is_valid(raise_exception=True)
        booking = serializer.save(
            experience=experience,
            user=request.user,
            kind=Booking.BookingKindChoices.EXPERIENCE,
        )
        serializer = PublicBookingSerializer(booking)
        return Response(serializer.data)
