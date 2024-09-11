from collections import OrderedDict
from typing import Any
from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest
from django.template.response import TemplateResponse

from decks.forms import ChangeDeckOwnerForm
from decks.models import (
    Card,
    CardInDeck,
    Comment,
    CommentVote,
    Deck,
    FavoriteCard,
    LovePoint,
    PrivateLink,
    Set,
    Subtype,
    Tag,
)


class ReadOnlyAdminMixin(object):
    """Disables all editing capabilities."""

    def __init__(self, *args, **kwargs):
        super(ReadOnlyAdminMixin, self).__init__(*args, **kwargs)

    def get_actions(self, request: HttpRequest) -> OrderedDict[Any, Any]:
        actions = super(ReadOnlyAdminMixin, self).get_actions(request)
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
        if isinstance(obj, Card):
            return obj.rarity == Card.Rarity.UNIQUE
        return False

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
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
        "tags",
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
                    "tags",
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
    actions = ["make_public", "make_private", "change_deck_owner"]

    @admin.action(description="Mark selected Decks as public")
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} deck(s) marked as public.")

    @admin.action(description="Mark selected Decks as private")
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f"{updated} deck(s) marked as private.")

    @admin.action(description="Change owner of selected decks")
    def change_deck_owner(self, request, queryset):
        form = None

        if "apply" in request.POST:
            form = ChangeDeckOwnerForm(request.POST)
            if form.is_valid():
                new_owner = form.cleaned_data["new_owner"]
                count = queryset.update(owner=new_owner)

                self.message_user(
                    request, f"{count} deck(s) successfully reassigned to {new_owner}"
                )
                return

        if not form:
            form = ChangeDeckOwnerForm()

        return TemplateResponse(
            request,
            "admin/change_owner_confirmation.html",
            {
                "decks": queryset,
                "form": form,
                "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            },
        )


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

        match obj.type:
            case Card.Type.HERO:
                card_stats_fields = ["reserve_count", "permanent_count"]
            case Card.Type.CHARACTER:
                card_stats_fields = ["mana_cost", "power"]
            case Card.Type.SPELL | Card.Type.PERMANENT:
                card_stats_fields = ["mana_cost"]
            case _:
                card_stats_fields = None

        if card_stats_fields:
            fieldsets.append(("Stats", {"fields": card_stats_fields}))

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

    @admin.display
    def reserve_count(self, obj: Card):
        return obj.stats["reserve_count"]

    @admin.display
    def permanent_count(self, obj: Card):
        return obj.stats["permanent_count"]

    @admin.display
    def mana_cost(self, obj: Card):
        return obj.stats["main_cost"], obj.stats["recall_cost"]

    @admin.display
    def power(self, obj: Card):
        return (
            obj.stats["forest_power"],
            obj.stats["mountain_power"],
            obj.stats["ocean_power"],
        )


@admin.register(CardInDeck)
class CardInDeckAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["deck", "card"]
    search_fields = ["card__reference"]


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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "description"]
    search_fields = ["name"]


@admin.register(FavoriteCard)
class FavoriteCardAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["__str__"]
    search_fields = ["user", "card"]
