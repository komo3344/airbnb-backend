from rest_framework.pagination import PageNumberPagination


class HostRoomPagination(PageNumberPagination):
    page_size = 10
