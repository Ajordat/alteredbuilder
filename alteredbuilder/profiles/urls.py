from django.urls import path

from profiles import views


urlpatterns = [
    path("<uuid:pk>/", views.ProfileDetailView.as_view(), name='profile-detail'),
]
