from rest_framework import serializers
from .models import Message, ProjectChatGroup, UserChatGroup
from projects.serializers import MemberSerializer
from users.serializers import ProfileUserSerializer


class MessageMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    sender = ProfileUserSerializer()
    recepient = ProfileUserSerializer()

    class Meta:
        model = Message
        fields = '__all__'


class ProjectChatGroupSerializer(serializers.ModelSerializer):
    message_set = MessageSerializer(many=True)

    class Meta:
        model = ProjectChatGroup
        fields = '__all__'


class UserChatGroupSerializer(serializers.ModelSerializer):
    message_set = MessageSerializer(many=True)
    
    class Meta:
        model = UserChatGroup
        fields = '__all__'