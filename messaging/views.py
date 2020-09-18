from django.shortcuts import render
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import ProjectChatGroup, UserChatGroup, Message
from .serializers import MessageSerializer, ProjectChatGroupSerializer, UserChatGroupSerializer
from projects.models import Member
from django.db.models import Q
import operator
from functools import reduce


def get_user_chatgroups(user):
    # Member instance of user
    member_qs = Member.objects.filter(user=user)

    if member_qs.exists():
        # Conditions for project chat groups
        member_condition_1 = reduce(operator.or_, [
                         Q(project__member__id=member.id) for member in member_qs])
        project_chatgroups = ProjectChatGroup.objects.filter(
            Q(project__owner=user) | member_condition_1).distinct()

        # Conditions for user chat groups
        member_condition_2 = reduce(operator.or_, [
                         Q(chat_members__id=member.id) for member in member_qs])
        user_chatgroups = UserChatGroup.objects.filter(member_condition_2).distinct()


    else:
        project_chatgroups = ProjectChatGroup.objects.filter(project__owner=user)
        user_chatgroups = None

    return project_chatgroups, user_chatgroups


class MessagesView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            room_type = kwargs['room_type']
            chat_group_id = kwargs['room_id']
            to_retrieve = 'messages'

        except:
            to_retrieve = 'chats'

        if to_retrieve == 'messages':
            if room_type == 'PG':
                chat_group = get_object_or_404(ProjectChatGroup, id=chat_group_id)

                if self.verify_project_group_user(chat_group, user):
                    messages = Message.objects.filter(project_chat_group=chat_group)
                    serializer = MessageSerializer(messages, many=True)

                    data = {
                        "messages": serializer.data,
                    }
                    return Response(data, status=status.HTTP_200_OK)

                else:
                    return Response("This page either does not exist or you are not authorized to access it.", 
                                    status=status.HTTP_400_BAD_REQUEST)

            elif room_type == 'UG':
                pass

            elif room_type == 'PC':
                pass

            else:
                return Response("Invalid request.", status=status.HTTP_400_BAD_REQUEST)

        elif to_retrieve == 'chats':
            project_chatgroups, user_chatgroups = get_user_chatgroups(user)
            projectgroup_serializer = ProjectChatGroupSerializer(project_chatgroups, many=True)
            usergroup_serializer = UserChatGroupSerializer(user_chatgroups, many=True)

            chat_groups = {
                "project_chatgroups": projectgroup_serializer.data,
                "user_chatgroups": usergroup_serializer.data
            }

            data = {
                "chat_groups": chat_groups
            }

            return Response(data, status=status.HTTP_200_OK)

        else:
            return Response("This page either does not exist or you are not authorized to access it.", 
                            status=status.HTTP_400_BAD_REQUEST)

    def verify_project_group_user(self, chat_group, user):
        for member in chat_group.project.get_members():
            if member.user == user:
                return True
        return False
