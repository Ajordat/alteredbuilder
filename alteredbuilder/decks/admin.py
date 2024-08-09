from collections import OrderedDict
from typing import Any
from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest

from .models import (
    Card,
    CardInDeck,
    Comment,
    CommentVote,
    Deck,
    LovePoint,
    PrivateLink,
    Set,
    Subtype,
)


class ReadOnlyAdminMixin(object):
    """Disables all editing capabilities."""

    def __init__(self, *args, **kwargs):
        super(ReadOnlyAdminMixin, self).__init__(*args, **kwargs)
        # self.readonly_fields = [f.name for f in self.model._meta.get_fields()]

    def get_actions(self, request: HttpRequest) -> OrderedDict[Any, Any]:
        actions = super(ReadOnlyAdminMixin, self).get_actions(request)
        # del_action = "delete_selected"
        # if del_action in actions:
        #     del actions[del_action]
        return actions

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> bool:
        return False

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        pass

    def delete_model(self, request: HttpRequest, obj: Any) -> None:
        pass

    def save_related(self, request: Any, form: Any, formsets: Any, change: Any) -> None:
        pass


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "name", "is_public", "modified_at", "created_at"]
    search_fields = ["id", "name", "owner__username"]
    list_filter = ["is_public"]
    list_display_links = ["id", "name"]
    show_facets = admin.ShowFacets.ALWAYS
    readonly_fields = [
        "owner",
        "hero",
        "is_standard_legal",
        "standard_legality_errors",
        "is_draft_legal",
        "draft_legality_errors",
        "is_exalts_legal",
        "love_count",
        "hit_count",
        "comment_count",
        "created_at",
        "modified_at",
    ]
    fieldsets = [
        (
            "Metadata",
            {
                "fields": [
                    "owner",
                    "name",
                    "description",
                    "hero",
                    ("created_at", "modified_at"),
                ]
            },
        ),
        (
            "Engagement",
            {"fields": ["is_public", "love_count", "comment_count", "hit_count"]},
        ),
        (
            "Legality",
            {
                "fields": [
                    ("is_standard_legal", "standard_legality_errors"),
                    ("is_draft_legal", "draft_legality_errors"),
                    "is_exalts_legal",
                ]
            },
        ),
    ]
    actions = ["make_public", "make_private"]

    @admin.action(description="Mark selected Decks as public")
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        if updated == 1:
            self.message_user(request, f"{updated} deck was marked as public.")
        else:
            self.message_user(request, f"{updated} decks were marked as public.")

    @admin.action(description="Mark selected Decks as private")
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        if updated == 1:
            self.message_user(request, f"{updated} deck was marked as private.")
        else:
            self.message_user(request, f"{updated} decks were marked as private.")


@admin.register(Card)
class CardAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["reference", "name", "rarity", "faction", "set"]
    search_fields = ["reference", "name"]
    list_display_links = ["reference", "name"]
    list_filter = ["type", "faction", "rarity", "set"]
    show_facets = admin.ShowFacets.ALWAYS

    def get_fieldsets(
        self, request: HttpRequest, obj: Card
    ) -> list[tuple[str | None, dict[str, Any]]]:

        base_fieldset = [
            "set",
            "reference",
            "name",
            "faction",
            "type",
            "subtypes",
            "rarity",
            "image_url",
            "stats",
        ]
        i18n_fields = ["name", "image_url", "main_effect"]

        if obj.type == Card.Type.HERO:
            base_fieldset += ["main_effect"]
        else:
            base_fieldset += [
                "main_effect",
                "echo_effect",
            ]
            i18n_fields += ["echo_effect"]

        fieldsets = [
            (
                "Base stats",
                {"fields": base_fieldset},
            ),
        ]

        for code, name in settings.LANGUAGES:
            lang_fieldset = (
                name,
                {
                    "fields": [f"{field}_{code}" for field in i18n_fields],
                    "classes": ["collapse"],
                },
            )
            fieldsets.append(lang_fieldset)
        return fieldsets


@admin.register(CardInDeck)
class CardInDeckAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["deck", "card"]


@admin.register(LovePoint)
class LovePointAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["user", "deck", "created_at"]
    fields = list_display
    search_fields = ["user__username", "deck__name"]


@admin.register(PrivateLink)
class PrivateLinkAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["code", "deck", "last_accessed_at", "created_at"]
    fields = list_display
    search_fields = ["deck__name"]


@admin.register(Set)
class SetAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["name", "short_name", "code", "reference_code"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["deck", "user", "created_at"]
    readonly_fields = ["user", "deck", "vote_count"]


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ["user", "comment"]
    readonly_fields = ["user", "comment"]


@admin.register(Subtype)
class SubtypeAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["reference"]

    def get_fieldsets(
        self, request: HttpRequest, obj: Card
    ) -> list[tuple[str | None, dict[str, Any]]]:

        base_fieldset = ["reference", "name"]

        fieldsets = [(None, {"fields": base_fieldset})]

        for code, name in settings.LANGUAGES:
            lang_fieldset = (name, {"fields": [f"name_{code}"]})
            fieldsets.append(lang_fieldset)
        return fieldsets
