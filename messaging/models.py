from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
import magic

User = get_user_model()


ROOM_TYPES = [
    ('PG', 'Project Group'),
    ('UG', 'User Group'),
    ('PC', 'Private Chat'),
]

MSG_STATUSES = [
    ('S', 'Sent'),
    ('D', 'Delivered'),
    ('R', 'Read'),
    ('F', 'Failed')
]

FILE_TYPES = [
    ('application', 'Document'),
    ('audio', 'Audio'),
    ('video', 'Video'),
    ('image', 'Image'),
]


class ProjectChatGroup(models.Model):
    # Is auto-created when a project is created
    room_type = models.CharField(choices=ROOM_TYPES, max_length=2)

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    name = models.CharField(help_text="Fills automatically. Same as project title", 
                            max_length=20)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        self.name = self.project.title
        self.__room_type = 'PG'
        super().save(*args, **kwargs)


class UserChatGroup(models.Model):
    # Created by a user
    room_type = models.CharField(choices=ROOM_TYPES, max_length=2)
    
    name = models.CharField(max_length=20)
    chat_members = models.ManyToManyField('projects.Member',
                                          related_name='user_chat_group_members')
    admins = models.ManyToManyField('projects.Member', related_name='user_chat_group_admins')

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        self.__room_type = 'UG'
        super().save(*args, **kwargs)


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='sender')
    recepient = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='recepient')
    target_type = models.CharField(choices=ROOM_TYPES, max_length=2)

    project_chat_group = models.ForeignKey(ProjectChatGroup, on_delete=models.CASCADE, 
                                           null=True, blank=True)
    user_chat_group = models.ForeignKey(UserChatGroup, on_delete=models.CASCADE, 
                                        null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    file_type = models.CharField(choices=FILE_TYPES, max_length=11, null=True, blank=True, editable=False)
    file = models.FileField(upload_to=settings.IMAGE_UPLOAD_FOLDER, null=True, blank=True)
    status = models.CharField(choices=MSG_STATUSES, max_length=1, default='S')
    id_on_client = models.CharField(max_length=36, help_text='Temporary ID on client', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ('created',)

    def get_file_name(self):
        if self.file:
            path = self.file.name
            name = path.replace(settings.IMAGE_UPLOAD_FOLDER +'/', '')
            return name
        return None

    def save(self, *args, **kwargs):
        if self.file:
            mime = magic.from_buffer(self.file.read(), mime=True)
            self.file_type = mime.split('/')[0]
            print(self.file_type)
        else:
            self.file_type = None

        super().save(*args, **kwargs)
        

# Post-save actions
@receiver(post_save, sender=Message)
def send_message_to_websocket(sender, instance, created, **kwargs):
    if created:
        pass
    pass
