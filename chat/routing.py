# chat/routing.py
from django.urls import re_path

from chat.chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path("ws/chat/", ChatConsumer.as_asgi()),
]
