from django.urls import path

from . import views

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
    path("new/", views.NewDeckFormView.as_view(), name="new-deck"),
    path("<int:pk>/update/", views.update_deck, name="update-deck-id"),
    path(
        "<int:pk>/privatelink/", views.create_private_link, name="create-private-link"
    ),
    path(
        "<int:pk>/update/metadata/",
        views.UpdateDeckMetadataFormView.as_view(),
        name="update-deck-metadata",
    ),
    path(
        "<int:pk>/comment/",
        views.CreateCommentFormView.as_view(),
        name="create-deck-comment",
    ),
    path("<int:pk>/delete/", views.delete_deck, name="delete-deck-id"),
    path("<int:pk>/love/", views.love_deck, name="love-deck-id"),
    path("<int:pk>/comment/<int:comment_pk>/vote/", views.vote_comment, name="vote-comment"),
]
