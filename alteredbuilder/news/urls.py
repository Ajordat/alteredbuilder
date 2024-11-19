from django.urls import path
from .views import updates_view

urlpatterns = [
    path("", updates_view, name="news"),
]
