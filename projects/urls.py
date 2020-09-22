from django.urls import path
from . import views


urlpatterns = [
    path('home/', views.HomeView.as_view()),
    path('portals/', views.PortalView.as_view()),
    path('portals/<str:portal>/', views.PortalView.as_view()),
	path('portals/<str:portal>/projects/', views.PortalProjects.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/', views.PortalProjects.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/invite/', views.InviteMemberView.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/confirm-invite/<str:token>/',
         views.InviteMemberView.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/members/',
         views.ProjectMembers.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/members/<int:mem_id>/',
         views.ProjectMembers.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/milestones/',
         views.ProjectMilestones.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/milestones/<int:milestone_id>/',
         views.ProjectMilestones.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/milestones/<int:milestone_id>/comment/',
         views.MilestoneCommentView.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/tickets/',
         views.ProjectTickets.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/tickets/<int:ticket_id>/',
         views.ProjectTickets.as_view()),
    path('portals/<str:portal>/projects/<int:proj_id>/tickets/<int:ticket_id>/comment/',
         views.TicketCommentView.as_view()),
    
    path("get-project-choices/", views.get_project_related_choices),
]