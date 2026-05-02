from django.urls import path

from meetings import views

urlpatterns = [
    path("", views.handle_meeting_creation),
]
