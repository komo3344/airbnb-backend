from django.db import models
from common.models import DateTimeModel
from config import settings


class ChattingRoom(DateTimeModel):
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="chatting_rooms",
    )

    def __str__(self):
        return "Chatting Room"


class Message(DateTimeModel):
    text = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="messages",
    )
    room = models.ForeignKey(
        "direct_messages.ChattingRoom",
        on_delete=models.CASCADE,
        related_name="messages",
    )

    def __str__(self):
        return f"{self.user} says: {self.text}"
