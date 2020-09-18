from rest_framework import serializers
from .models import (Project, Member, Ticket, TicketHistory, Milestone, 
                     MilestoneComment, TicketComment)
from users.serializers import ProfileUserSerializer, PortalSerializer, MinimalPortalSerializer


class MinimalProjectSerializer(serializers.ModelSerializer):
    portal = MinimalPortalSerializer()

    class Meta:
        model = Project
        fields = ('id', 'title', 'portal')


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'


class MilestoneCommentSerializer(serializers.ModelSerializer):
    commenter = MemberSerializer()

    class Meta:
        model = MilestoneComment
        fields = '__all__'


class MilestoneBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    project = MinimalProjectSerializer()
    responsible = MemberSerializer()
    milestonecomment_set = MilestoneCommentSerializer(many=True)

    class Meta:
        model = Milestone
        fields = '__all__'


class TicketCommentSerializer(serializers.ModelSerializer):
    commenter = MemberSerializer()

    class Meta:
        model = TicketComment
        fields = '__all__'


class TicketBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'


class TicketHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketHistory
        exclude = ('id', 'ticket')


class TicketSerializer(serializers.ModelSerializer):
    assigned_to = MemberSerializer()
    submitter = MemberSerializer()
    tickethistory_set = serializers.SerializerMethodField()
    ticketcomment_set = TicketCommentSerializer(many=True)

    class Meta:
        model = Ticket
        exclude = ('project', )


    def get_tickethistory_set(self, instance):
        history = instance.tickethistory_set.all().order_by('-date_changed')
        return TicketHistorySerializer(history, many=True).data


class ProjectSerializer(serializers.ModelSerializer):
    member_set = MemberSerializer(many=True)
    ticket_set = TicketSerializer(many=True)
    milestone_set = MilestoneSerializer(many=True)
    owner = ProfileUserSerializer()
    portal = PortalSerializer()

    class Meta:
        model = Project
        fields = '__all__'


class MemberDetailSerializer(serializers.ModelSerializer):
    # ticket_set = TicketSerializer(many=True)

    class Meta:
        model = Member
        fields = '__all__'