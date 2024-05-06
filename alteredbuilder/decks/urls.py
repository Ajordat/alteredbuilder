from django.urls import path

from . import views

# Endpoints for this app

urlpatterns = [
    path("", views.DeckListView.as_view(), name="deck-list"),
    path("own/", views.OwnDeckListView.as_view(), name="own-deck"),
    path("<int:pk>/", views.DeckDetailView.as_view(), name="deck-detail"),
    path("cards/", views.CardListView.as_view(), name="cards"),
    path("new/", views.NewDeckFormView.as_view(), name="new-deck"),
    path("<int:pk>/update/", views.update_deck, name="update-deck-id"),
    path(
        "<int:pk>/update/metadata/",
        views.UpdateDeckMetadataFormView.as_view(),
        name="update-deck-metadata",
    ),
    path("update/", views.UpdateDeckFormView.as_view(), name="update-deck"),
]
