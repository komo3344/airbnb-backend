import jwt
from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from rest_framework import status, generics
from rest_framework.exceptions import ParseError
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import Review
from reviews.paginations import ReviewPagination
from reviews.serializers import ReviewSerializer
from rooms.models import Room
from rooms.paginations import HostRoomPagination
from rooms.serializers import HostRoomSerializer
from . import serializers
from .models import User


class Me(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = serializers.PrivateUserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = serializers.PrivateUserSerializer(
            user,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            user = serializer.save()
            serializer = serializers.PrivateUserSerializer(user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class Users(APIView):
    def post(self, request):
        serializer = serializers.PrivateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PublicUser(APIView):
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        serializer = serializers.PublicUserSerializer(user)
        return Response(serializer.data)


class ChangePassword(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not old_password or not new_password:
            raise ParseError
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_200_OK)
        else:
            raise ParseError


class LogIn(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            raise ParseError
        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user:
            login(request, user)
            return Response({"ok": "Welcome!"})
        else:
            return Response({"error": "wrong password"})


class LogOut(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": "bye!"})


class UserReviews(generics.ListAPIView):
    serializer_class = ReviewSerializer
    pagination_class = ReviewPagination

    def get_queryset(self):
        username = self.kwargs.get("username")
        if User.objects.filter(username=username).exists():
            queryset = Review.objects.filter(user__username=username).all().order_by("-created_at")
            return queryset
        else:
            raise ParseError(f"No user with that nickname({username}) exists.")


class HostRooms(generics.ListAPIView):
    serializer_class = HostRoomSerializer
    pagination_class = HostRoomPagination

    def get_queryset(self):
        username = self.kwargs.get("username")
        if User.objects.filter(username=username).exists():
            queryset = Room.objects.filter(owner__username=username).order_by("-created_at")
            return queryset
        else:
            raise ParseError(f"No user with that nickname({username}) exists.")


class JWTLogIn(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            raise ParseError
        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user:
            # 유저가 복호화 할 수 있기 때문에 중요정보는 넣지 않음
            token = jwt.encode(
                {"pk": user.pk},
                settings.SECRET_KEY,
                algorithm="HS256",
            )
            return Response({"token": token})
        else:
            return Response({"error": "wrong password"})
