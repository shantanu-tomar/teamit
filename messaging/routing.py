from django.urls import re_path, path
from . import consumers


websocket_urlpatterns = [
    path('ws/messages/', consumers.ProjectMessagesConsumer),
    path('ws/messages/video/', consumers.VideoChatConsumer),
]