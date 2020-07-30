from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer

# from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

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
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        self.accept()

    def disconnect(self):
        async_to_sync(self.channel_layer.group_discard)(
            "subscribed_active_incidents", 
            self.channel_name
        )

    def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "action" key we can switch on
        print("RECEIVE_JSON", content)
        action = content.get("action", None)
        try:
            if action == "list":
                # Make them join the room
                self.list()
            elif action == "subscribe":
                # Leave the room
                self.subscribe()
        except ClientError as e:
            # Catch any errors and send it back
            self.send_json({"error": e.code})

    def disconnect(self, code):
        pass

    def list(self, limit=25):
        incidents = self.get_active_incidents()
        print("INCIDENTS", incidents)
        serialized = IncidentSerializer(incidents, many=True)

        self.send_json({"incidents": serialized.data})

    def notify(self, event):
        print("NOTIFY", event)
        self.send_json(event["content"])


    def subscribe(self, limit=25):
        async_to_sync(self.channel_layer.group_add)(
            "subscribed_active_incidents", 
            self.channel_name
        )

        incidents = self.get_active_incidents()
        serialized = IncidentSerializer(incidents, many=True)

        self.send_json({"msg": "subscribed", "channel_name": self.channel_name, "start_incidents": serialized.data})

    def get_active_incidents(self, last=25):
        return Incident.objects.active()[:last]


# class ActiveIncidentConsumer(AsyncJsonWebsocketConsumer):
#     """
#     This chat consumer handles websocket connections for chat clients.
#     It uses AsyncJsonWebsocketConsumer, which means all the handling functions
#     must be async functions, and any sync work (like ORM access) has to be
#     behind database_sync_to_async or sync_to_async. For more, read
#     http://channels.readthedocs.io/en/latest/topics/consumers.html
#     """
# 
#     async def connect(self):
#         """
#         Called when the websocket is handshaking as part of initial connection.
#         """
#         await self.accept()
# 
#     async def receive_json(self, content):
#         """
#         Called when we get a text frame. Channels will JSON-decode the payload
#         for us and pass it as the first argument.
#         """
#         # Messages will have a "action" key we can switch on
#         print("RECEIVE_JSON", content)
#         action = content.get("action", None)
#         try:
#             if action == "list":
#                 # Make them join the room
#                 await self.list()
#             elif action == "subscribe":
#                 # Leave the room
#                 await self.subscribe()
#         except ClientError as e:
#             # Catch any errors and send it back
#             await self.send_json({"error": e.code})
# 
#     async def disconnect(self, code):
#         pass
# 
#     async def list(self, limit=25):
#         incidents = await self.get_active_incidents()
#         print("INCIDENTS", incidents)
#         serialized = IncidentSerializer(incidents, many=True)
# 
#         await self.send_json({"incidents": serialized.data})
# 
#     @database_sync_to_async
#     def get_active_incidents(self, last=25):
#         return Incident.objects.active()[:last]
# 

