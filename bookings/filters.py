from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework import filters


class YearFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        start = request.query_params.get("year", None)
        now = timezone.localtime(timezone.now()).date()
        if start:
            try:
                start = datetime.strptime(start, "%Y").date()
            except (TypeError, ValueError):
                start = now.replace(month=1, day=1)
            end = start + relativedelta(years=1) - relativedelta(days=1)

            queryset = queryset.filter(
                Q(check_in__range=[start, end]) |
                Q(check_out__range=[start, end]) |
                (Q(check_in__lte=start) & Q(check_out__gte=end))
            )
        else:
            queryset = queryset.filter(check_in__gt=now)
        return queryset


class MonthFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        start = request.query_params.get("month", None)
        now = timezone.localtime(timezone.now()).date()
        if start:
            try:
                start = datetime.strptime(start, "%Y-%m").date()
            except (TypeError, ValueError):
                start = now.replace(day=1)
            end = start + relativedelta(months=1) - relativedelta(days=1)

            queryset = queryset.filter(
                Q(check_in__range=[start, end]) |
                Q(check_out__range=[start, end]) |
                (Q(check_in__lte=start) & Q(check_out__gte=end))
            )
        else:
            queryset = queryset.filter(check_in__gt=now)
        return queryset


class DayFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        start = request.query_params.get("day", None)
        now = timezone.localtime(timezone.now()).date()
        if start:
            try:
                start = datetime.strptime(start, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                start = now.today()
            end = start

            queryset = queryset.filter(
                Q(check_in__range=[start, end]) |
                Q(check_out__range=[start, end]) |
                (Q(check_in__lte=start) & Q(check_out__gte=end))
            )
        else:
            queryset = queryset.filter(check_in__gt=now)
        return queryset
