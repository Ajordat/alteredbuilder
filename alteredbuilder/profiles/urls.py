from django.urls import path

from profiles import views


urlpatterns = [
    path("", views.ProfileListView.as_view(), name="profile-list"),
    path("<uuid:code>/", views.ProfileDetailView.as_view(), name="profile-detail"),
    path("edit/", views.EditProfileFormView.as_view(), name="profile-edit"),
    path("<uuid:code>/follow/", views.follow_user, name="profile-follow"),
    path("<uuid:code>/unfollow/", views.unfollow_user, name="profile-unfollow"),
]
