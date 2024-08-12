from django.urls import path

from profiles import views


urlpatterns = [
    path("", views.ProfileListView.as_view(), name="profile-list"),
    path("<uuid:code>/", views.ProfileDetailView.as_view(), name="profile-detail"),
    path("edit/", views.EditProfileFormView.as_view(), name="profile-edit"),
]
