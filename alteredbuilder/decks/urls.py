from django.urls import path

from decks.views import card_list as card_list_views
from decks.views import collection as collection_views
from decks.views import comments as comment_views
from decks.views import deck_detail as deck_detail_views
from decks.views import deck_lists as deck_lists_views
from decks.views import deck_metadata as deck_metadata_views
from decks.views import embeds as embeds_views
from decks.views import imports as import_views
from decks.views import general as general_views


urlpatterns = [
    path("", deck_lists_views.DeckListView.as_view(), name="deck-list"),
    path("own/", deck_lists_views.OwnDeckListView.as_view(), name="own-deck"),
    path("<int:pk>/", deck_detail_views.DeckDetailView.as_view(), name="deck-detail"),
    path(
        "<int:pk>/<uuid:code>",
        deck_detail_views.PrivateLinkDeckDetailView.as_view(),
        name="private-url-deck-detail",
    ),
    path("cards/", card_list_views.CardListView.as_view(), name="cards"),
    path(
        "collection/",
        collection_views.display_collection,
        name="collection",
    ),
    path(
        "collection/update/", collection_views.save_collection, name="save-collection"
    ),
    path(
        "legality/",
        general_views.deck_legality_view,
        name="legality_changelog",
    ),
    path("new/", import_views.NewDeckFormView.as_view(), name="new-deck"),
    path("<int:pk>/update/", deck_metadata_views.update_deck, name="update-deck-id"),
    path(
        "<int:pk>/privatelink/",
        deck_detail_views.create_private_link,
        name="create-private-link",
    ),
    path(
        "<int:pk>/update/metadata/",
        deck_metadata_views.update_deck_metadata,
        name="update-deck-metadata",
    ),
    path(
        "<int:pk>/update/tags/",
        deck_metadata_views.update_tags,
        name="update-deck-tags",
    ),
    path("<int:pk>/comment/", comment_views.create_comment, name="create-deck-comment"),
    path("<int:pk>/delete/", deck_detail_views.delete_deck, name="delete-deck-id"),
    path("<int:pk>/love/", deck_metadata_views.love_deck, name="love-deck-id"),
    path(
        "<int:pk>/comment/<int:comment_pk>/vote/",
        comment_views.vote_comment,
        name="vote-comment",
    ),
    path(
        "<int:pk>/comment/<int:comment_pk>/delete/",
        comment_views.delete_comment,
        name="delete-comment",
    ),
    path("import-card/", import_views.import_card, name="import-card"),
    path(
        "import-multiple-cards/",
        import_views.import_multiple_cards,
        name="import-multiple-cards",
    ),
    path(
        "<int:deck_id>/embed/",
        embeds_views.deck_embed_view,
        name="embed-deck",
    ),
]
