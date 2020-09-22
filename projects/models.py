from django.db import models
from users.models import Portal
from messaging.models import ProjectChatGroup 
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

PROJECT_STATUSES = (
    ('Active', 'Active'),
    ('In Progress', 'In Progress'),
    ('On Track', 'On Track'),
    ('Delayed', 'Delayed'),
    ('In Testing', 'In Testing'),
    ('On Hold', 'On Hold'),
    ('Approved', 'Approved'),
    ('Cancelled', 'Cancelled'),
    ('Planning', 'Planning'),
    ('Completed', 'Completed'),
    ('Invoiced', 'Invoiced'),
)

TICKET_TYPES = (
    ('Crash/Hang', 'Crash/Hang'),
    ('UI/Usability', 'UI/Usability'),
    ('Bug/Error', 'Bug/Error'),
    ('Security', 'Security'),
    ('Feature Request', 'Feature Request'),
    ('Other Comments', 'Other Comments'),
    ('Training/Document Requests', 'Training/Document Requests'),
)

TICKET_STATUS = (
    ('Open', 'Open'),
    ('Closed', 'Closed'),
    ('In Progress', 'In Progress'),
    ('Resolved', 'Resolved'),
    ('Additional Info Required', 'Additional Info Required'),
)

TICKET_SEVERITY = (
    ('None', 'None'),
    ('Show Stopper', 'Show Stopper'),
    ('Critical', 'Critical'),
    ('Major', 'Major'),
    ('Minor', 'Minor'),
)

MEMBER_ROLES = (
    ('Administrator', 'Administrator'),
    ('Project Manager', 'Project Manager'),
    ('Developer', 'Developer'),
    ('Submitter', 'Submitter'),
)


class Project(models.Model):
    portal = models.ForeignKey(Portal, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    description = models.TextField()
    reference_link = models.URLField(help_text='include http protocol; eg: "https://example.com"',
                                     null=True, blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owner')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(choices=PROJECT_STATUSES, max_length=25, default='Active')
    completed = models.BooleanField(default=False)


    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # checking if Member object instance for Owner exists
        # if not, creating one...
        owner = self.owner
        obj, created = Member.objects.get_or_create(
            project=self, email=owner.email)
        obj.role = 'Administrator'
        obj.save()

    def get_members(self):
        return self.member_set.all()


class Member(models.Model):
    portal = models.ForeignKey(Portal, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField()
    role = models.CharField(choices=MEMBER_ROLES, max_length=16, default='Submitter')
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    def clean(self):
        if self.email != self.user.email:
            raise ValidationError({'email':(f"Member email field must be same as its User's email field, i.e. {self.user.email}")})

        if self.name != self.user.name:
            raise ValidationError({'name':(f"Member name field must be same as its User's name field, i.e. {self.user.name}")})

    def save(self, *args, **kwargs):
        if self.name is None:
            self.name = self.user.name
        
        self.clean()
        super().save(*args, **kwargs)

    def is_project_admin(self):
        if self.role == 'Administrator' or self.role == 'Project Manager':
            return True
        else:
            return False


class TicketHistory(models.Model):
    ticket = models.ForeignKey('projects.Ticket', on_delete=models.CASCADE)
    change = models.CharField(max_length=20, help_text='What changed ?')
    old_value = models.CharField(max_length=20, null=True, blank=True)
    new_value = models.CharField(max_length=20, null=True, blank=True)
    date_changed = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name_plural='Ticket History'


class Ticket(models.Model):
    # Saving previous values for history
    __old_values = None

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=25)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_to')
    submitter = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True)
    ticket_type = models.CharField(choices=TICKET_TYPES, max_length=27)
    severity = models.CharField(choices=TICKET_SEVERITY, max_length=15, default='None')
    status = models.CharField(choices=TICKET_STATUS, max_length=24)
    due_date = models.DateField(help_text='Deadline', null=True, blank=True)
    modified = models.DateField(auto_now=True)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


    def __init__(self, *args, **kwargs):
        fields_to_save = [ 'assigned_to', 'ticket_type', 'status', 'due_date', 'severity' ]

        super().__init__(*args, **kwargs)

        values = []
        for field in fields_to_save:
            values.append(getattr(self, field))

        self.__old_values = dict(zip(fields_to_save, values))


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        fields_to_check = [ 'assigned_to', 'ticket_type', 'status', 'due_date', 'severity' ]

        for field in fields_to_check:
            current_value = getattr(self, field)
            print(field, current_value)
            old_value = self.__old_values[field]

            if current_value != old_value:

                TicketHistory.objects.create(
                    ticket=self,
                    change=field.replace('_', ' ').capitalize(),
                    old_value=self.__old_values[field],
                    new_value=getattr(self, field)
                )


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    commenter = models.ForeignKey(Member, on_delete=models.CASCADE)
    comment = models.CharField(max_length=200, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    milestone = models.CharField(max_length=25)
    description = models.TextField(null=True, blank=True)
    responsible = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    due_date = models.DateField()
    completed = models.BooleanField(default=False)
    completed_on = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if self.due_date == '':
            self.due_date = None
        if self.completed_on == '':
            self.completed_on = None
        super().save(*args, **kwargs)


class MilestoneComment(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    commenter = models.ForeignKey(Member, on_delete=models.CASCADE)
    comment = models.CharField(max_length=200, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Invite(models.Model):
    portal = models.ForeignKey(Portal, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    email = models.EmailField()
    role = models.CharField(choices=MEMBER_ROLES, max_length=16, default='Submitter')
    verified = models.BooleanField(default=False)
    expiry = models.DateTimeField()
    
    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.verified:
            self.delete()


# Post-save actions
@receiver(post_save, sender=Project)
def create_project_chat_group(sender, instance, created, **kwargs):
    if created:
        ProjectChatGroup.objects.create(project=instance)
