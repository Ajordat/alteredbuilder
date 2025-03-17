from django.urls import path
from django.views.generic import TemplateView

from decks import views

# Endpoints for this app

urlpatterns = [
    path("", views.DeckListView.as_view(), name="deck-list"),
    path("own/", views.OwnDeckListView.as_view(), name="own-deck"),
    path("<int:pk>/", views.DeckDetailView.as_view(), name="deck-detail"),
    path(
        "<int:pk>/<uuid:code>",
        views.PrivateLinkDeckDetailView.as_view(),
        name="private-url-deck-detail",
    ),
    path("cards/", views.CardListView.as_view(), name="cards"),
    path(
        "collection/",
        TemplateView.as_view(template_name="decks/collection.html"),
        name="collection",
    ),
    path(
        "legality/",
        views.deck_legality_view,
        name="legality_changelog",
    ),
    path("new/", views.NewDeckFormView.as_view(), name="new-deck"),
    path("<int:pk>/update/", views.update_deck, name="update-deck-id"),
    path(
        "<int:pk>/privatelink/", views.create_private_link, name="create-private-link"
    ),
    path(
        "<int:pk>/update/metadata/",
        views.update_deck_metadata,
        name="update-deck-metadata",
    ),
    path("<int:pk>/update/tags/", views.update_tags, name="update-deck-tags"),
    path("<int:pk>/comment/", views.create_comment, name="create-deck-comment"),
    path("<int:pk>/delete/", views.delete_deck, name="delete-deck-id"),
    path("<int:pk>/love/", views.love_deck, name="love-deck-id"),
    path(
        "<int:pk>/comment/<int:comment_pk>/vote/",
        views.vote_comment,
        name="vote-comment",
    ),
    path(
        "<int:pk>/comment/<int:comment_pk>/delete/",
        views.delete_comment,
        name="delete-comment",
    ),
    path("import-card/", views.import_card, name="import-card"),
]
