import asyncio
import json
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.shortcuts import get_object_or_404
from .views import get_user_chatgroups
from .models import ProjectChatGroup, Message, UserChatGroup
from .serializers import ( MessageSerializer, MessageMinimalSerializer)
from projects.models import TicketComment, MilestoneComment, Member
from projects.serializers import (MilestoneCommentSerializer, TicketCommentSerializer,
                                  TicketCommentBaseSerializer, MilestoneCommentBaseSerializer)
import base64
from django.core.files import File
import os
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator

User = get_user_model()


@database_sync_to_async
def get_user_member(project, user):
    # Takes in a project and a user object & returns a 
    # member object corresponding to that user in that project
    member = get_object_or_404(Member, user=user, project=project)
    return member


def convert_imgb64_to_file(file_b64_str, filename):
    imgdata = base64.b64decode(file_b64_str)
        
    file = open(filename, 'wb')
    file.write(imgdata)
    file.close()
    file = open(filename, 'rb')
    
    # Delete local file
    if os.path.exists(filename):
        os.remove(filename)
    
    djangofile = File(file)
    return djangofile


@database_sync_to_async
def get_user(scope):
    query_string = scope['query_string']
    
    if b'auth' in query_string:
        try:
            token_name, token_key = query_string.decode().split('=')
    
            if token_name == 'auth':
                token = Token.objects.get(key=token_key)
                user = token.user
                
        except Token.DoesNotExist:
            user = AnonymousUser()

    else:
        user = AnonymousUser()

    return user


@database_sync_to_async
def get_chat_group(room_type, group_id):
    if room_type == 'PG':
        group = get_object_or_404(ProjectChatGroup, id=group_id)
    elif room_type == 'UG':
        group = get_object_or_404(UserChatGroup, id=group_id)
    elif room_type == 'PC':
        pass

    return group


@database_sync_to_async
def verify_group_user(room_type, chat_group, user):
    if room_type == 'PG':
        for member in chat_group.project.get_members():
            if member.user == user:
                return True

    elif room_type == 'UG':
        return True

    elif room_type == 'PC':
        return True

    return False


class ProjectMessagesConsumer(AsyncWebsocketConsumer):
    room_name_prefix = 'inbox_'
    room_group_name_prefix = 'group_'

    async def connect(self):
        # user = self.scope['user']
        user = await get_user(self.scope)

        if user == AnonymousUser():
            raise DenyConnection("Invalid User")
        
        self.room_name = f"{self.room_name_prefix}{user.id}"
        self.room_group_name = f"{self.room_group_name_prefix}{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("connected")

    
    # Receive message from Client
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        event_type = text_data_json['event']
        payload = text_data_json['payload']

        # Send message to room group
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': event_type,
        #         'payload': payload,
        #     }
        # )

        event = {
            'type': event_type,
            'payload': payload,
        }
        
        try:
            await eval(f"self.{event_type}(event)")
            
        except:
            raise DenyConnection("Invalid Request")


    async def sent_message(self, event):
        user = await get_user(self.scope)
        sender_group_name = f"{self.room_group_name_prefix}{self.room_name_prefix}{user.id}"

        payload = event['payload']
        target_room_group_names = await self.get_group_names(payload, user)

        msg_text = payload.get('text')
        room_type = payload['target_type']
        chat_group_id = payload['target']
        msg_id_on_client = payload.get('temp_id', None)

        try:
            file_type = payload['file_type']
            file_name = payload['filename']

            *args, file_b64_str = payload['file'].split(',')
            django_file = convert_imgb64_to_file(file_b64_str, file_name)
        
        except KeyError:
            file_type = None
            file_name = None
            django_file = None
        
        if room_type == 'PG':
            message_dict = {
                "sender": user.id,
                "target_type": room_type,
                "project_chat_group": chat_group_id ,
                "text": msg_text,
                "file": django_file,
                "file_name": file_name,
                "id_on_client": msg_id_on_client,
            }

        elif room_type == 'UG':
            message_dict = {
                "sender": user.id,
                "target_type": room_type,
                "user_chat_group": chat_group_id ,
                "text": msg_text,
                "file": django_file,
                "file_name": file_name,
                "id_on_client": msg_id_on_client,
            }
        
        # Save message in database
        message = await self.save_message(message_dict)
        
        # Send message to every user except the sender
        for group in target_room_group_names:
            if group != sender_group_name:
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': "chat_message",
                        'message': message,
                    }
                )


    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        print("RECEIVED MSG")
        # Send message to Client
        await self.send(text_data=json.dumps({
            'type': "message",
            'message': message
        }))


    async def delivery_receipt(self, event):
        event_payload = event["payload"]
        message_id = event_payload['message_id']
        delivered_to = event_payload["delivered_to"]

        try:
            message_serialized= await self.update_message_status(message_id, "D")
            sender_group_name = f"{self.room_group_name_prefix}{self.room_name_prefix}{message_serialized['sender']['id']}"
            print("PROCESSING DELIVERY RECEIPT", sender_group_name)

            payload = {
                "type": "delivery_receipt",
                "payload": {
                    "message": message_serialized,
                    "delivered_to": delivered_to,
                },
            }

            await self.channel_layer.group_send(
                sender_group_name,
                {
                    'type': "event_emitter",
                    'payload': payload
                },
            )
        except Exception as e:
            print("DELIVERY RECEIPT ERROR", e)
            pass


    async def jitsi_offer(self, event):
        user = await get_user(self.scope)
        caller_group_name = f"{self.room_group_name_prefix}{self.room_name_prefix}{user.id}"
        event_payload = event["payload"]
        event_payload.update({ 
            "caller": user.id,
            "caller_name": user.name, 
        })
        
        target_room_group_names = await self.get_group_names(event_payload, user)
        
        payload = {
            "type": "jitsi_offer",
            'payload': event_payload
        }

        for group in target_room_group_names:
            if group != caller_group_name:
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': "event_emitter",
                        'payload': payload,
                    }
                )


    async def videochat_offer(self, event):
        user = await get_user(self.scope)
        caller_group_name = f"{self.room_group_name_prefix}{self.room_name_prefix}{user.id}"
        event_payload = event["payload"]
        event_payload.update({ "caller": user.id })
        print("OFFER", user.id)

        target_room_group_names = await self.get_group_names(event_payload, user)
        
        payload = {
            "type": "videochat_offer",
            'payload': event_payload
        }

        for group in target_room_group_names:
            if group != caller_group_name:
                print("SENDING OFFER TO ", group)
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': "event_emitter",
                        'payload': payload,
                    }
                )


    async def videochat_answer(self, event):
        user = await get_user(self.scope)
        answerer_group_name = f"{self.room_group_name_prefix}{self.room_name_prefix}{user.id}"
        print("ANSWER", user.id)

        event_payload = event["payload"]
        event_payload.update({ 
            "answerer": user.id 
        })
        
        target_room_group_names = await self.get_group_names(event_payload, user)
        
        payload = {
            "type": "videochat_answer",
            'payload': event_payload
        }

        for group in target_room_group_names:
            if group != answerer_group_name:
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': "event_emitter",
                        'payload': payload,
                    }
                )
    

    async def ice_candidate(self, event):
        user = await get_user(self.scope)
        sender_group_name = f"{self.room_group_name_prefix}{self.room_name_prefix}{user.id}"
        event_payload = event["payload"]
        print("ICE-CANDIDATE", user.id)

        event_payload.update({ 
            "sender": user.id
        })
        
        target_room_group_names = await self.get_group_names(event_payload, user)
        
        payload = {
            "type": "ice_candidate",
            'payload': event_payload
        }

        for group in target_room_group_names:
            if group != sender_group_name:
                await self.channel_layer.group_send(
                    group,
                    {
                        'type': "event_emitter",
                        'payload': payload,
                    }
                )


    async def event_emitter(self, event):
        payload = event["payload"]
        
        # Send message to Each Client
        await self.send(text_data=json.dumps(payload))
        
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print("disconnected", close_code)


    @database_sync_to_async
    def save_message(self, message_dict):
        file = None
        file_name = None

        if message_dict['file'] != None:
            file = message_dict['file']
            file_name = message_dict['file_name']

            del message_dict['file']
            del message_dict['file_name']

        serializer = MessageMinimalSerializer(data=message_dict)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        if file != None:
            message.file.save(file_name, file)

        detail_serializer = MessageSerializer(message)

        return detail_serializer.data


    @database_sync_to_async
    def update_message_status(self, message_id, status):
        message = get_object_or_404(Message, id=message_id)
        message.status = status
        message.save()

        message_serializer = MessageSerializer(message)
        return message_serializer.data


    @database_sync_to_async
    def get_group_names(self, payload, user):
        channel_group_names = []

        if payload['target_type'] == 'PG':
            group = get_object_or_404(ProjectChatGroup, id=payload['target'])

            # checking if the user is authorized to send message to this group
            user_project_groups, *args = get_user_chatgroups(user)
            if group in user_project_groups:
                members = group.project.member_set.all()
                
                for member in members:
                    user_id = member.user.id  
                    target_room_name = f"{self.room_name_prefix}{user_id}"
                    target_room_group_name = f"{self.room_group_name_prefix}{target_room_name}"
                    channel_group_names.append(target_room_group_name)

        elif payload['target_type'] == 'UG':
            group = get_object_or_404(UserChatGroup, id=payload['target'])

            # checking if the user is authorized to send message to this group
            *args, user_userchat_groups = get_user_chatgroups(user)
            if group in user_userchat_groups:
                members = group.chat_members.all()
                
                for member in members:
                    user_id = member.user.id  
                    target_room_name = f"{self.room_name_prefix}{user_id}"
                    target_room_group_name = f"{self.room_group_name_prefix}{target_room_name}"
                    channel_group_names.append(target_room_group_name)

        return channel_group_names


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        comment_of = self.scope["url_route"]["kwargs"]["comment_of"]
        of_id = self.scope["url_route"]["kwargs"]["of_id"]
        
        self.room_name = f"{comment_of}_{of_id}"
        self.room_group_name = f"group_{self.room_name}"
        user = await get_user(self.scope)

        if user == AnonymousUser():
            raise DenyConnection("Invalid User")


        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print("connected")

    
    # Receive comment from Client
    async def receive(self, text_data):
        comment_of = self.scope["url_route"]["kwargs"]["comment_of"]
        of_id = self.scope["url_route"]["kwargs"]["of_id"]
        
        commenter_user = await get_user(self.scope)
        payload = json.loads(text_data)
        comment_text = payload['comment']
        project = payload['project_id']

        # get member object of commenter_user
        commenter = await get_user_member(project, commenter_user)

        if comment_of == 't':
            comment_dict = {
                "ticket": of_id,
                "commenter": commenter.id,
                "comment": comment_text,
            }

        elif comment_of == 'm':
            comment_dict = {
                "milestone": of_id,
                "commenter": commenter.id,
                "comment": comment_text,
            }
        
        # Save comment in database
        comment = await self.save_comment(comment_dict, comment_of)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': "comment_received",
                'comment': comment,
            }
        )


    # Receive comment from room group
    async def comment_received(self, event):
        comment = event['comment']
        
        # Send comment to Client
        await self.send(text_data=json.dumps({
            'type': "comment",
            'comment': comment
        }))


    @database_sync_to_async
    def save_comment(self, comment_dict, comment_of):
        if comment_of == 't':
            serializer = TicketCommentBaseSerializer(data=comment_dict)
            serializer.is_valid(raise_exception=True)
            comment = serializer.save()

            detail_serializer = TicketCommentSerializer(comment)
       
        elif comment_of == 'm':
            serializer = MilestoneCommentBaseSerializer(data=comment_dict)
            serializer.is_valid(raise_exception=True)
            comment = serializer.save()
            
            detail_serializer = MilestoneCommentSerializer(comment)
        
        return detail_serializer.data


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print("disconnected", close_code)
