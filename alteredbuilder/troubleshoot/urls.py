from django.urls import path

from . import views

# Endpoints for this app

app_name = "troubleshoot"
urlpatterns = [
    path("session", views.SubmitSessionFormView.as_view(), name="session"),
]
