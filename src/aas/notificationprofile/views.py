import json

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from aas.alert.serializers import AlertSerializer
from .models import Filter, NotificationProfile
from .permissions import IsOwner
from .serializers import (
    FilterSerializer,
    NotificationProfileSerializer,
    TimeSlotSerializer,
)
from .validators import FilterStringValidator


class NotificationProfileList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = NotificationProfileSerializer

    def get_queryset(self):
        return self.request.user.notification_profiles.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = NotificationProfileSerializer

    def get_queryset(self):
        return self.request.user.notification_profiles.all()


@api_view(["GET"])
def alerts_filtered_by_notification_profile_view(request, notification_profile_pk):
    try:
        # Go through user to ensure that the user owns the requested notification profile
        notification_profile = request.user.notification_profiles.get(
            pk=notification_profile_pk
        )
    except NotificationProfile.DoesNotExist:
        raise ValidationError(
            f"Notification profile with pk={notification_profile_pk} does not exist."
        )

    serializer = AlertSerializer(notification_profile.filtered_alerts, many=True)
    return Response(serializer.data)


class TimeSlotList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        return self.request.user.time_slots.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeSlotDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        return self.request.user.time_slots.all()


class FilterList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FilterSerializer

    def get_queryset(self):
        return self.request.user.filters.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FilterDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = FilterSerializer

    def get_queryset(self):
        return self.request.user.filters.all()


# TODO: make HTTP method GET and get query data from URL
@api_view(["POST"])
def filter_preview_view(request):
    filter_string_dict = request.data
    # Validate posted filter string
    filter_string_validator = FilterStringValidator()
    filter_string_validator(filter_string_dict)

    filter_string_json = json.dumps(filter_string_dict)
    mock_filter = Filter(filter_string=filter_string_json)
    serializer = AlertSerializer(mock_filter.filtered_alerts, many=True)
    return Response(serializer.data)
