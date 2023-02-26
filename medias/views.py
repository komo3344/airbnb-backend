from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView, status

from medias.models import Photo


class PhotoDetail(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Photo, pk=pk)

    def delete(self, request, pk):
        photo = self.get_object(pk)
        if (photo.room and photo.room.owner != request.user) or (
            photo.experience and photo.experience.host != request.user
        ):
            raise PermissionDenied
        photo.delete()
        return Response(status=status.HTTP_200_OK)
