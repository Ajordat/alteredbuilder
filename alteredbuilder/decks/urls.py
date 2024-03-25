from django.urls import path

from . import views

# Endpoints for this app

urlpatterns = [
    path("", views.DeckListView.as_view(), name="deck-list"),
    path("<int:pk>/", views.DeckDetailView.as_view(), name="deck-detail"),
    path("cards/", views.cards, name="cards"),
    path("new/", views.NewDeckFormView.as_view(), name="new-deck"),
]
