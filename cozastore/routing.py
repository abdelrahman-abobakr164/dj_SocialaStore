"""
WebSocket URL routing for Django Channels
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Example WebSocket routes for a social media project
    # Chat room WebSocket
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Notifications WebSocket
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    
    # Live feed updates WebSocket
    re_path(r'ws/feed/$', consumers.FeedConsumer.as_asgi()),
    
    # User online status WebSocket
    re_path(r'ws/status/$', consumers.StatusConsumer.as_asgi()),
]