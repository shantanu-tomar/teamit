from rest_framework import serializers
from .models import Message, ProjectChatGroup, UserChatGroup
from projects.serializers import MemberSerializer
from users.serializers import ProfileUserSerializer


class FileSerializer(serializers.Serializer):
    name = serializers.FileField(use_url=False)
    url = serializers.FileField(use_url=True)


class MessageMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    sender = ProfileUserSerializer()
    recepient = ProfileUserSerializer()
    filename = serializers.CharField(source='get_file_name')


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