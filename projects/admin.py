from django.contrib import admin
from .models import (Project, Ticket, TicketHistory, 
                     Member, Portal, Milestone, Invite, MilestoneComment, TicketComment)


class PortalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'status', 'completed')


class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'title',
                    'assigned_to', 'ticket_type', 'severity', 'status')

    def get_form(self, request, obj=None, **kwargs):
        form = super(TicketAdmin, self).get_form(request, obj, **kwargs)
        
        if obj is not None:
            form.base_fields['assigned_to'].queryset = obj.project.member_set.all()
            form.base_fields['submitter'].queryset = obj.project.member_set.all()
        return form


class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'change', 'old_value', 'new_value', 'date_changed']


class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'commenter')


class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'role')


class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'project')


class MilestoneCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'milestone', 'commenter')


class InviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'project', 'role')

    
admin.site.register(Portal, PortalAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(TicketHistory, TicketHistoryAdmin)
admin.site.register(TicketComment, TicketCommentAdmin)
admin.site.register(Milestone, MilestoneAdmin)
admin.site.register(MilestoneComment, MilestoneCommentAdmin)
admin.site.register(Invite, InviteAdmin)
