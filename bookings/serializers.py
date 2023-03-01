from django.utils import timezone
from rest_framework import serializers
from .models import Booking


class CreateRoomBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            "check_in",
            "check_out",
            "guests",
        )

    def validate_check_in(self, value):
        now = timezone.localtime(timezone.now()).date()
        if now > value:
            raise serializers.ValidationError("Can't book in the past!")
        return value

    def validate_check_out(self, value):
        now = timezone.localtime(timezone.now()).date()
        if now > value:
            raise serializers.ValidationError("Can't book in the past!")
        return value

    def validate(self, data):
        if data["check_out"] < data["check_in"]:
            raise serializers.ValidationError(
                "Check in should be smaller than check out."
            )

        if Booking.objects.filter(
            room=self.context["room"],
            check_in__lte=data["check_out"],
            check_out__gte=data["check_in"],
        ).exists():
            raise serializers.ValidationError(
                "Those (or some) of those dates are already taken."
            )
        return data


class PublicBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            "pk",
            "check_in",
            "check_out",
            "experience_time",
            "guests",
        )


class CreateExperienceBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            "experience_time",
            "guests"
        )

    # TODO 다양한 경우의 validate 추가
    def validate_experience_time(self, value):
        start = self.context["experience"].start
        end = self.context["experience"].end
        if start > value:
            raise serializers.ValidationError("Can't book in the past!")
        if end < value:
            raise serializers.ValidationError("Can't book in the future!")
        return value
