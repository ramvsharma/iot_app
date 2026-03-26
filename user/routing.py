from django.urls import path

from user.consumers import IotIngestConsumer, SubscribeConsumer

websocket_urlpatterns = [
    path('ws/ingest/', IotIngestConsumer.as_asgi()),
    path('ws/subscribe/', SubscribeConsumer.as_asgi()),
]
