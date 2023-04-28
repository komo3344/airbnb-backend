import jwt
import requests
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
            return Response({"ok": "Welcome!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "wrong password"}, status=status.HTTP_400_BAD_REQUEST)


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


class GithubLogIn(APIView):
    def post(self, request):
        try:
            code = request.data.get("code")
            url = f"https://github.com/login/oauth/access_token?code={code}&client_id=3429bbb417261e7ad92f&client_secret={settings.GH_SECRET}"
            gh_response = requests.post(url, headers={"Accept": "application/json"})
            access_token = gh_response.json().get('access_token')
            user_data = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            user_data = user_data.json()
            # github email이 private인 것을 받아오기 위함
            user_emails = requests.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            user_emails = user_emails.json()
            try:
                user = User.objects.get(email=user_emails[0]["email"])
                login(request, user)
                return Response(status=status.HTTP_200_OK)
            except User.DoesNotExist:
                user = User.objects.create(
                    username=user_data.get('login'),
                    email=user_emails[0]['email'],
                    name=user_data.get('name'),
                    avatar=user_data.get('avatar_url'),
                )
                user.set_unusable_password()
                user.save()
                login(request, user)
                return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class KakaoLogIn(APIView):
    def post(self, request):
        code = request.data.get("code")
        access_token = requests.post(
            "https://kauth.kakao.com/oauth/token",
            headers={"Content-type": "application/x-www-form-urlencoded;charset=utf-8"},
            data={
                "grant_type": "authorization_code",
                "client_id": "483f1759e6da568fa36ef312e6ea4396",
                "redirect_uri": "http://127.0.0.1:3000/social/kakao",
                "code": code
            }
        )
        access_token = access_token.json().get('access_token')
        user_data = requests.post(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer ${access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8"
            }
        )
        user_data = user_data.json()
        kakao_account = user_data.get('kakao_account')
        profile = kakao_account.get('profile')
        try:
            user = User.objects.get(email=kakao_account.get('email'))
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            user = User.objects.create(
                email=kakao_account.get('email'),
                username=profile.get('nickname'),
                name=profile.get('nickname'),
                avatar=profile.get('profile_image_url')
            )
            user.set_unusable_password()
            user.save()
            login(request, user)
        return Response(status=status.HTTP_200_OK)
