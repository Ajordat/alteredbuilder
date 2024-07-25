from django.urls import path

from . import views

# Endpoints for this app

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]
