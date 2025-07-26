"""
WebSocket consumers for Django Channels
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer for chat room functionality"""
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json.get('username', 'Anonymous')

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer for real-time notifications"""
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.user_group_name = f'notifications_{self.user.id}'
            
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'data': event.get('data', {})
        }))


class FeedConsumer(AsyncWebsocketConsumer):
    """Consumer for live feed updates"""
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.feed_group_name = 'live_feed'
            
            await self.channel_layer.group_add(
                self.feed_group_name,
                self.channel_name
            )
            
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.feed_group_name,
            self.channel_name
        )

    async def feed_update(self, event):
        # Send feed update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'feed_update',
            'data': event['data']
        }))


class StatusConsumer(AsyncWebsocketConsumer):
    """Consumer for user online/offline status"""
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.status_group_name = 'user_status'
            
            await self.channel_layer.group_add(
                self.status_group_name,
                self.channel_name
            )
            
            # Mark user as online
            await self.update_user_status(True)
            await self.accept()

    async def disconnect(self, close_code):
        # Mark user as offline
        await self.update_user_status(False)
        
        await self.channel_layer.group_discard(
            self.status_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def update_user_status(self, is_online):
        # Update user's online status in database
        # You'll need to create a UserProfile model with an is_online field
        pass

    async def status_update(self, event):
        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'user_id': event['user_id'],
            'is_online': event['is_online']
        }))