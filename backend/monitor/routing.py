from django.urls import path
from .consumers import HostConsumer

websocket_urlpatterns = [
    path("ws/hosts/<str:hostname>/", HostConsumer.as_asgi()),
]