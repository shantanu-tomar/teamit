from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator as generator
from .models import (Project, Member, Ticket, Milestone, Invite, MilestoneComment, TicketComment)
from .models import (PROJECT_STATUSES, TICKET_TYPES, TICKET_STATUS,
                     TICKET_SEVERITY, MEMBER_ROLES)
from .communications import send_mail
from .serializers import (ProjectSerializer, TicketSerializer, TicketBaseSerializer,
                          MilestoneSerializer, MemberSerializer, MilestoneCommentSerializer,
                          MilestoneBaseSerializer, TicketCommentSerializer)
from users.serializers import ProfileUserSerializer
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import status
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
import operator
from functools import reduce
from users.views import get_user_portals
from users.serializers import PortalSerializer
from users.models import Portal
import datetime
from datetime import date
import json
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from users.de_en_crypt_password import encrypt, decrypt
from django.contrib.auth import get_user_model
from django.http import QueryDict

User = get_user_model()


BASE_URL = settings.BASE_URL


# Setting CSRF cookie when django serves index.html to Angular
# this decorator can also instead be used with every view/function that handles POST requests 
@ensure_csrf_cookie
def index(request, path=''):
    """
    Renders the Angular2 SPA
    """
    return render(request, "index.html")


def date_validator(*args):
    dates = list(args)
    
    for date in dates:
        if date == '':
            index = dates.index(date)
            dates[index] = None
    return dates


def get_user_projects(user):
    # Member instance of user
    member_qs = Member.objects.filter(user=user)
    if member_qs.exists():
        member_condition = reduce(operator.or_, [
                         Q(member__id=member.id) for member in member_qs])
        queryset = Project.objects.filter(
            Q(owner=user) | member_condition).distinct()
    else:
        queryset = Project.objects.filter(owner=user)

    return queryset


def get_portal_projects(portal):
    projects = Project.objects.filter(portal=portal)
    return projects


def get_user_assigned_tickets(user):
    member_qs = Member.objects.filter(user=user)
    if member_qs.exists():
        member_condition = reduce(operator.or_, [
                             Q(assigned_to=member) for member in member_qs])
            
        tickets = Ticket.objects.filter(member_condition).distinct()

    else:
        tickets = None
    return tickets


def is_portal_user(portal, user):
    user_portals = get_user_portals(user)
    if portal in user_portals:
        return True
    else:
        return False


def user_project_admin(project, user):
    if project.owner == user:
        return True
    elif project.portal.owner == user:
        return True

    for member in project.member_set:
        if member.user == user and member.is_project_admin():
            return True
    return False


class HomeView(APIView):
    def get(self, request):
        user = request.user
        portals = get_user_portals(user)
        portal_serializer = PortalSerializer(portals, many=True)

        projects = get_user_projects(user)
        project_serializer = ProjectSerializer(projects, many=True)

        tickets = get_user_assigned_tickets(user)

        if tickets is not None:
            due_tickets = tickets.exclude(Q(status='Closed') | Q(status='Resolved'))
        else:
            due_tickets = None

        due_tickets_serializer = TicketSerializer(due_tickets, many=True)

        today = datetime.date.today()

        if projects.exists():
            project_milestone_condition = reduce(operator.or_, [
                Q(project=project) for project in projects])

            due_milestones = Milestone.objects.filter(
                project_milestone_condition, start_date__lte=today, completed=False)

        else:
            due_milestones = None
            
        due_milestone_serializer = MilestoneSerializer(due_milestones, many=True)

        
        data = {
            "portals": portal_serializer.data,
            "projects": project_serializer.data,
            "due_tickets": due_tickets_serializer.data,
            "due_milestones": due_milestone_serializer.data,

        }

        return Response(data, status=status.HTTP_200_OK)


class PortalView(APIView):
    def get(self, *args, **kwargs):
        pass


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ProjectSerializer


    def get_queryset(self):
        queryset = Project.objects.all()
        return queryset


class PortalProjects(APIView):
    def get(self, *args, **kwargs):
        user = self.request.user
        member_role = None

        try:
            portal_name = kwargs['portal']
            portal_obj = get_object_or_404(Portal, name=portal_name)

            if is_portal_user(portal_obj, user):
                try:
                    project_id = kwargs['proj_id']
                    project = get_object_or_404(Project, id=project_id)
                    project_serializer = ProjectSerializer(project)
                    member_obj = get_object_or_404(Member, user=user, project=project)
                    member_role = member_obj.role
                except KeyError:
                    # Member instances of user
                    member_qs = Member.objects.filter(user=user)
                    if member_qs.exists():
                        member_condition = reduce(operator.or_, [
                                         Q(member__id=member.id, portal=portal_obj) for member in member_qs])
                        
                        projects = Project.objects.filter(
                            Q(owner=user, portal=portal_obj) | member_condition |
                            Q(portal__owner=user)).distinct()
                    else:
                        projects = Project.objects.filter(Q(owner=user, portal=portal_obj) |
                                                          Q(portal__owner=user)).distinct()

                    
                    project_serializer = ProjectSerializer(projects, many=True)

                if portal_obj.owner == user:
                    portal_owner = True
                else:
                    portal_owner = False

                data = {
                    "projects": project_serializer.data,
                    "portal_owner": portal_owner,
                }

                if member_role is not None:
                    data.update({"member_role": member_role})

                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response("Invalid request.",
                            status=status.HTTP_400_BAD_REQUEST)


    def perform_update(self, serializer):
        serializer.save()


    def put(self, request, *args, **kwargs):
        user = request.user

        partial = kwargs.pop('partial', False)
        portal_name = kwargs['portal']

        portal = get_object_or_404(Portal, name=portal_name)
        project = get_object_or_404(Project, id=kwargs['proj_id'])

        # check if project belongs to the portal AND the user has permission to update it
        if project.portal == portal and is_portal_user(portal, user):
            serializer = ProjectSerializer(project, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(project, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                project._prefetched_objects_cache = {}

            return Response(serializer.data)

        else:
            return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.put(request, *args, **kwargs)            


class InviteMemberView(APIView):
    secret = (settings.SECRET_KEY).encode()

    def post(self, request, *args, **kwargs):
        user = request.user
        portal_name = kwargs['portal']
        
        project_id = kwargs['proj_id']
        project = get_object_or_404(Project, id=project_id)

        if user_project_admin(project, user) and project.portal.name == portal_name:
            to_mail = request.data['email']
            role = request.data['role']

            # Check if Member already exists
            member_qs = Member.objects.filter(project=project, email=to_mail)
            if member_qs.exists():
                return Response("This member already exists.", status=status.HTTP_400_BAD_REQUEST)

            # create Invite model instance
            invite_expiry = datetime.datetime.now() + datetime.timedelta(hours=48)
            Invite.objects.create(
                portal=project.portal, project=project,
                email=to_mail, role=role, expiry=invite_expiry)

            # Send an email invitation
            data = f"{to_mail}/{role}"
            token = encrypt(data.encode(), (self.secret)).decode()

            confirm_url = f"{BASE_URL}/portals/{portal_name}/projects/{project_id}/confirm-invite/{token}/"
            
            subject = "Invitation From TomBug"
            body = f"""Hello!
{user.name} just invited you to be a member of the project \
titled "{project.title}" as {role}.

Click link below to confirm. Your member account will not be \
activated until you confirm your email address.

{confirm_url}"""

            send_mail([to_mail, ], subject, body)

            return Response("An invitation email has been sent.", status=status.HTTP_200_OK)

        else:
            return Response("You don't have permission to add a member to this project.", 
                status=status.HTTP_403_FORBIDDEN)


    def get(self, request, *args, **kwargs):
        authentication_classes = ()
        permission_classes = ()
        
        try:
            token = kwargs['token']
            portal = kwargs['portal']
            proj_id = kwargs['proj_id']

        except KeyError:
            return Response("Invalid token.", status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_data = decrypt(token.encode(), (self.secret)).decode()
            member_email, role = decoded_data.split('/')

            invite = Invite.objects.get(email=member_email, role=role,
                                        portal__name=portal, project__id=proj_id)
            
            user_qs = User.objects.filter(email=member_email)
            if user_qs.exists():
                user_exists = True
                user = user_qs[0]
            else:
                user_exists = False

            data = {
                "approved": True,
                "message": None,
                "user_exists": user_exists,
                "email": member_email,
                "role": role
            }

            if user_exists:
                data.update({ "user": ProfileUserSerializer(user).data })

            return Response(data, status=status.HTTP_200_OK)

        except Invite.DoesNotExist:
            return Response("No such invitation exists.",
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response("Exception occurred. Please try again.",
                            status=status.HTTP_400_BAD_REQUEST)


class ProjectMembers(APIView):
    def post(self, request, *args, **kwargs):
        authentication_classes = ()
        permission_classes = ()
        
        data = request.data
        portal_name = data.get('portal')
        project_id = data.get('project')
        user_exists = data.get('user_exists')
        name = data.get('name')
        email = data.get('email')
        role = data.get('role')
        contact = data.get('contact_no')

        try:
            invite = Invite.objects.get(email=email, role=role,
                                        portal__name=portal_name, project__id=project_id)
        except Invite.DoesNotExist:
            return Response("This member invite has either expired, doesn't exist,\
                 or has already has been used.", status=status.HTTP_403_FORBIDDEN)
            

        portal = get_object_or_404(Portal, name=portal_name)
        project = get_object_or_404(Project, id=project_id)

        # First signup the user if user doesn't exist
        if user_exists is False:
            user = User(
                        name=name,
                        email=email,
                        password=data.get('password')
                        )
            user.save()

        elif user_exists is True:
            user = get_object_or_404(User, email=data.get('email'))

        
        # check if project belongs to the portal
        if project.portal == portal:
            member, created = Member.objects.get_or_create(
                                portal=portal, 
                                project=project, user=user,
                                name=name, email=email,
                                role=role, contact_number=contact,
                              )
            member.save()

            invite.verified = True
            invite.save()

            serializer = MemberSerializer(member)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response("You don't have permission to perform this action.",
                            status=status.HTTP_403_FORBIDDEN)


    def perform_update(self, serializer):
        serializer.save()


    def put(self, request, *args, **kwargs):
        user = request.user

        partial = kwargs.pop('partial', False)
        portal_name = kwargs['portal']

        portal = get_object_or_404(Portal, name=portal_name)
        project = get_object_or_404(Project, id=kwargs['proj_id'])
        member = get_object_or_404(Member, id=kwargs['mem_id'])


        # check if project belongs to the portal AND the user has permission to update it
        if member.portal == portal \
         and member.project == project \
         and is_portal_user(portal, user):
            serializer = MemberSerializer(member, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(member, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                member._prefetched_objects_cache = {}

            return Response(serializer.data)

        else:
            return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.put(request, *args, **kwargs)


class ProjectMilestones(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            portal_obj = get_object_or_404(Portal, name=portal_name)

            if is_portal_user(portal_obj, user):
                try:
                    milestone_id = kwargs['milestone_id']

                    milestone = get_object_or_404(
                        Milestone, id=milestone_id, project__id=project_id)

                    milestone_serializer = MilestoneSerializer(milestone)

                except KeyError:
                    project_milestones = Milestone.objects.filter(project__id=project_id)
                    milestone_serializer = MilestoneSerializer(
                        project_milestones, many=True)

                member_obj = get_object_or_404(Member, user=user, project__id=project_id)
                member_role = member_obj.role

                if portal_obj.owner == user:
                    portal_owner = True
                else:
                    portal_owner = False

                data = {
                    "milestones": milestone_serializer.data,
                    "portal_owner": portal_owner,
                    "member_role": member_role,
                }

                return Response(data, status=status.HTTP_200_OK)
            
            else:
                return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response("Invalid request.",
                            status=status.HTTP_400_BAD_REQUEST)
   

    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            project = get_object_or_404(Project, id=project_id, portal__name=portal_name)
            
            if user_project_admin(project, user):
                create_data = request.data
                
                completed = create_data.get("completed", None)
                completed_on = create_data.get("completed_on")
                due_date = create_data.get("due_date")

                if completed == '' or completed is None:
                    completed = False
                    create_data["completed"] = completed

                due_date, completed_on = date_validator(due_date, completed_on)

                create_data.update({ 
                    "project": project_id,
                    "due_date": due_date,
                    "completed_on": completed_on
                })

                serializer = MilestoneBaseSerializer(data=create_data)
                serializer.is_valid(raise_exception=True)
                milestone = serializer.save()

                return_serializer = MilestoneSerializer(milestone)
                return Response(return_serializer.data, status=status.HTTP_201_CREATED)

            else:
                return Response("You don't have permission to perform this action.", 
                                status=status.HTTP_403_FORBIDDEN)

        except KeyError:
            return Response("Invalid request.", status=status.HTTP_400_BAD_REQUEST)


    def perform_update(self, serializer):
        serializer.save()


    def put(self, request, *args, **kwargs):
        user = request.user

        partial = kwargs.pop('partial', False)
        portal_name = kwargs['portal']

        # check if project belongs to the portal AND the user has permission to update it
        try:
            project = get_object_or_404(Project, id=kwargs['proj_id'], portal__name=portal_name)
            milestone = get_object_or_404(Milestone, id=kwargs['milestone_id'], project=project)
        
        except (Project.DoesNotExist, Milestone.DoesNotExist):
            return Response("This link does not exist.",
                            status=status.HTTP_400_BAD_REQUEST)
        
        if user_project_admin(project, user):
            update_data = request.data
            
            serializer = MilestoneBaseSerializer(milestone, data=update_data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(milestone, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                milestone._prefetched_objects_cache = {}

            return_serializer = MilestoneSerializer(milestone)
            return Response(return_serializer.data)

        else:
            return Response("You're not authorized to access this page.",
                            status=status.HTTP_403_FORBIDDEN)


    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.put(request, *args, **kwargs)


    def delete(self, request, *args, **kwargs):
        user = request.user
        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            milestone_id = kwargs['milestone_id']
            project = get_object_or_404(Project, id=project_id, portal__name=portal_name)
            
            if user_project_admin(project, user):
                get_object_or_404(Milestone, id=milestone_id, project=project).delete()

                milestones = Milestone.objects.filter(project=project)
                return_serializer = MilestoneSerializer(milestones, many=True)
                
                return Response(return_serializer.data, status=status.HTTP_200_OK)

            else:
                return Response("You don't have permission to perform this action.", 
                                status=status.HTTP_403_FORBIDDEN)

        except KeyError:
            return Response("Invalid request.", status=status.HTTP_400_BAD_REQUEST)


class MilestoneCommentView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            portal_obj = get_object_or_404(Portal, name=portal_name)

            try:
                milestone_id = kwargs['milestone_id']
                milestone = get_object_or_404(Milestone, id=milestone_id, project__id=project_id)
                member = get_object_or_404(Member, project__id=project_id, user=user)
                comment_text = request.data.get('comment')
                comment_image = request.data.get('image', None)

                MilestoneComment.objects.create(
                    milestone=milestone,
                    commenter=member,
                    comment=comment_text,
                    image=comment_image,
                )

                comments = MilestoneComment.objects.filter(milestone=milestone)
                comment_serializer = MilestoneCommentSerializer(comments, many=True)

                return Response(comment_serializer.data, status=status.HTTP_201_CREATED)

            except (Milestone.DoesNotExist, Member.DoesNotExist):
                return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                return Response("An exception occurred, try again.", status=status.HTTP_500_INTERNAL_SERVER_ERROR
)

        except KeyError:
            return Response("Invalid request.",
                            status=status.HTTP_400_BAD_REQUEST)


class ProjectTickets(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        
        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            portal_obj = get_object_or_404(Portal, name=portal_name)

            if is_portal_user(portal_obj, user):
                try:
                    ticket_id = kwargs['ticket_id']
                    ticket = get_object_or_404(
                        Ticket, id=ticket_id, project__id=project_id)

                    ticket_serializer = TicketSerializer(ticket)

                except KeyError:
                    project_tickets = Ticket.objects.filter(project__id=project_id)
                    ticket_serializer = TicketSerializer(project_tickets, many=True)

                member_obj = get_object_or_404(Member, user=user, project__id=project_id)
                member_role = member_obj.role

                if portal_obj.owner == user:
                    portal_owner = True
                else:
                    portal_owner = False

                data = {
                    "tickets": ticket_serializer.data,
                    "portal_owner": portal_owner,
                    "member_role": member_role,
                }

                return Response(data, status=status.HTTP_200_OK)
            
            else:
                return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)
        
        except KeyError:
            return Response("Invalid request.",
                            status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            project = get_object_or_404(Project, id=project_id, portal__name=portal_name)
            
            if user_project_admin(project, user):
                create_data = request.data
                
                due_date = create_data.get("due_date")
                due_date, *args = date_validator(due_date)

                create_data.update({ 
                    "project": project_id,
                    "due_date": due_date,
                })

                serializer = TicketBaseSerializer(data=create_data)
                serializer.is_valid(raise_exception=True)
                ticket = serializer.save()

                return_serializer = TicketSerializer(ticket)
                return Response(return_serializer.data, status=status.HTTP_201_CREATED)

            else:
                return Response("You don't have permission to perform this action.", 
                                status=status.HTTP_403_FORBIDDEN)

        except KeyError:
            return Response("Invalid request.", status=status.HTTP_400_BAD_REQUEST)


    def perform_update(self, serializer):
        serializer.save()


    def put(self, request, *args, **kwargs):
        user = request.user

        partial = kwargs.pop('partial', False)
        portal_name = kwargs['portal']

        # check if project belongs to the portal AND the user has permission to update it
        try:
            project = get_object_or_404(Project, id=kwargs['proj_id'], portal__name=portal_name)
            ticket = get_object_or_404(Ticket, id=kwargs['ticket_id'], project=project)
        
        except (Project.DoesNotExist, Ticket.DoesNotExist):
            return Response("This link does not exist.",
                            status=status.HTTP_400_BAD_REQUEST)
        
        if user_project_admin(project, user):
            update_data = request.data
            
            serializer = TicketBaseSerializer(ticket, data=update_data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(ticket, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                ticket._prefetched_objects_cache = {}

            return_serializer = TicketSerializer(ticket)
            return Response(return_serializer.data)

        else:
            return Response("You're not authorized to access this page.",
                            status=status.HTTP_403_FORBIDDEN)


    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.put(request, *args, **kwargs)


    def delete(self, request, *args, **kwargs):
        user = request.user
        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']
            ticket_id = kwargs['ticket_id']
            project = get_object_or_404(Project, id=project_id, portal__name=portal_name)
            
            if user_project_admin(project, user):
                get_object_or_404(Ticket, id=ticket_id, project=project).delete()

                tickets = Ticket.objects.filter(project=project)
                return_serializer = TicketSerializer(tickets, many=True)
                
                return Response(return_serializer.data, status=status.HTTP_200_OK)

            else:
                return Response("You don't have permission to perform this action.", 
                                status=status.HTTP_403_FORBIDDEN)

        except KeyError:
            return Response("Invalid request.", status=status.HTTP_400_BAD_REQUEST)


class TicketCommentView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            portal_name = kwargs['portal']
            project_id = kwargs['proj_id']

            try:
                ticket_id = kwargs['ticket_id']
                ticket = get_object_or_404(Ticket, id=ticket_id, project__id=project_id)
                member = get_object_or_404(Member, project__id=project_id, 
                    user=user, portal__name=portal_name)
                comment_text = request.data.get('comment')
                comment_image = request.data.get('image', None)

                TicketComment.objects.create(
                    ticket=ticket,
                    commenter=member,
                    comment=comment_text,
                    image=comment_image,
                )

                comments = TicketComment.objects.filter(ticket=ticket)
                comment_serializer = TicketCommentSerializer(comments, many=True)

                return Response(comment_serializer.data, status=status.HTTP_201_CREATED)

            except (Ticket.DoesNotExist, Member.DoesNotExist):
                return Response("This page either doesn't exist, or you're not authorized to access it.",
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                return Response("An exception occurred, try again.", 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except KeyError:
            return Response("Invalid request.",
                            status=status.HTTP_400_BAD_REQUEST)


@api_view()
def get_project_related_choices(request):
    choice_categories = [PROJECT_STATUSES, TICKET_TYPES,
               TICKET_STATUS, TICKET_SEVERITY, MEMBER_ROLES]
    category_names = ["PROJECT_STATUSES", "TICKET_TYPES",
                      "TICKET_STATUS", "TICKET_SEVERITY", "MEMBER_ROLES"]

    choices = {}
    i = 0
    for category in choice_categories:
        cat_choices = [category_names[i], list((list(choice) for choice in category))]
        choices[cat_choices[0]] = cat_choices[1]
        i += 1

    return Response(choices, status=status.HTTP_200_OK)
