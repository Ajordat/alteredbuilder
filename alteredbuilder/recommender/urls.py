from django.urls import path

from recommender import views


urlpatterns = [
    path("next-card/", views.get_next_card, name="recommend-card"),
]
