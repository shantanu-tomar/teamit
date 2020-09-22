from django.urls import path
from . import views


urlpatterns = [
    path('', views.MessagesView.as_view()),
    path('<str:room_type>/<str:room_id>/', views.MessagesView.as_view()),
]