from django.contrib import admin
from django.urls import path, include, re_path
from users import views as user_views
from rest_auth import views as rest_auth_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from projects import views as project_views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('api/projects', project_views.ProjectViewSet, basename='projects')


urlpatterns = [
    path('', project_views.index, name="index"),
    
    # AUTH PATHS
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("api/register/", user_views.UserCreate.as_view(), name="register"),
    path("api/login/", user_views.LoginView.as_view(), name="login"),
    path('api/password-reset/',
         rest_auth_views.PasswordResetView.as_view(), name="password_reset"),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'),
         name="password_reset_confirm"),

    path('password-reset-complete/',
         user_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'),
         name="password_reset_complete"),

    path('api/profile/', user_views.ProfileView.as_view()),

    path('api/get-portals/', user_views.GetPortalsView.as_view()),
    path("api/messages/", include('messaging.urls')),

    # App Paths
    path('api/', include('projects.urls')),
    path('admin/', admin.site.urls),
]

urlpatterns += router.urls

# only adding MEDIA ROOT when in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += re_path(r'^(?P<path>.*)/$', project_views.index),

admin.site.site_header = "TomBug Admin"
admin.site.site_title = "TomBug Admin Portal"
admin.site.index_title = "Welcome to TomBug Administration Portal"