from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer

# from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from argus.incident.models import Incident
from argus.incident.serializers import IncidentSerializer


class ClientError(Exception):
    """
    Custom exception class that is caught by the websocket receive()
    handler and translated into a send back to the client.
    """
    def __init__(self, code):
        super().__init__(code)
        self.code = code

class ActiveIncidentConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        print("CONNECTING USER", self.user, "cookies", self.scope["cookies"])
        if self.user and self.user.is_authenticated:
            return self.accept()
        # TODO REJECT
        print("REJECTED")
        # self.reject()

    def disconnect(self, code):
        print("DISCONNECT", code)
        async_to_sync(self.channel_layer.group_discard)(
            "subscribed_active_incidents", 
            self.channel_name
        )


    def receive_json(self, content):
        action = content.get("action", None)
        try:
            if action == "list":
                self.list()
            elif action == "subscribe":
                self.subscribe()
        except ClientError as e:
            # Catch any errors and send it back
            self.send_json({"error": e.code})


    def list(self, limit=25):
        incidents = self.get_active_incidents()
        serialized = IncidentSerializer(incidents, many=True)
        self.send_json({"incidents": serialized.data})


    def notify(self, event):
        self.send_json(event["content"])


    def subscribe(self, limit=25):
        async_to_sync(self.channel_layer.group_add)(
            "subscribed_active_incidents", 
            self.channel_name
        )

        incidents = self.get_active_incidents()
        serialized = IncidentSerializer(incidents, many=True)

        self.send_json({"type": "subscribed", "channel_name": self.channel_name, "start_incidents": serialized.data})


    def get_active_incidents(self, last=25):
        return Incident.objects.active()[:last]


@receiver(post_save, sender=Incident)
def notify_on_change_or_create(sender, instance: Incident, created: bool, raw: bool, *args, **kwargs):
    is_new = created or raw

    serializer = IncidentSerializer(instance)
    channel_layer = get_channel_layer()
    content = {
        "type": "created" if is_new else "modified",
        "payload": serializer.data,
    }
    async_to_sync(channel_layer.group_send)("subscribed_active_incidents", {
        "type": "notify",
        "content": content,
    })
