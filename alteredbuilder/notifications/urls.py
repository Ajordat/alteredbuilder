from django.urls import path

from notifications import views


urlpatterns = [
    path("<int:pk>/", views.notification_detail, name="notification-detail"),
    path("fetch/", views.fetch_notifications, name="notification-fetch"),
]
