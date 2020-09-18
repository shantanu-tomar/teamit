from django.contrib import admin
from .models import (ProjectChatGroup, UserChatGroup, Message,)


admin.site.register(ProjectChatGroup)
admin.site.register(UserChatGroup)
admin.site.register(Message)
