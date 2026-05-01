from django.urls import path

from meeting import views

urlpatterns = [
    path("", views.handle_meeting_creation),
]
