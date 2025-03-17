from http import HTTPStatus
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.manager import Manager
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from hitcount.views import HitCountDetailView

from api.utils import ajax_request
from decks.deck_utils import get_deck_details
from decks.models import Comment, CommentVote, Deck, LovePoint, PrivateLink
from decks.forms import CommentForm, DeckMetadataForm, DeckTagsForm
from profiles.models import Follow


class DeckDetailView(HitCountDetailView):
    """DetailView to display the detail of a Deck model."""

    model = Deck
    count_hit = True

    def get_queryset(self) -> Manager[Deck]:
        """When retrieving the object, we need to make sure that the Deck is public or
        the User is its owner.

        Returns:
            Manager[Deck]: The view's queryset.
        """
        qs = super().get_queryset()
        filter = Q(is_public=True)
        if self.request.user.is_authenticated:
            filter |= Q(owner=self.request.user)
            qs = qs.annotate(
                is_loved=Exists(
                    LovePoint.objects.filter(
                        deck=OuterRef("pk"), user=self.request.user
                    )
                ),
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("owner"), follower=self.request.user
                    )
                ),
            )
        # I don't fancy making these queries here. Maybe I could store that information
        # on the UserProfile model
        qs = qs.annotate(
            follower_count=Count("owner__followers", distinct=True),
            following_count=Count("owner__following", distinct=True),
        )
        return (
            qs.filter(filter)
            .select_related("hero", "owner", "owner__profile")
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add metadata of the Deck to the context.

        Returns:
            dict[str, Any]: The view's context.
        """

        context = super().get_context_data(**kwargs)
        context |= get_deck_details(self.object)
        context["metadata_form"] = DeckMetadataForm(
            initial={
                "name": self.object.name,
                "description": self.object.description,
                "is_public": self.object.is_public,
            }
        )
        context["tags_form"] = DeckTagsForm(
            initial={"tags": list(self.object.tags.values_list("pk", flat=True))}
        )
        context["comment_form"] = CommentForm()
        comments_qs = Comment.objects.filter(deck=self.object).select_related(
            "user", "user__profile"
        )
        if self.request.user.is_authenticated:
            comments_qs = comments_qs.annotate(
                is_upvoted=Exists(
                    CommentVote.objects.filter(
                        comment=OuterRef("pk"), user=self.request.user
                    )
                )
            )
        context["comments"] = comments_qs
        return context


class PrivateLinkDeckDetailView(LoginRequiredMixin, DeckDetailView):
    """DetailView to display the detail of a Deck model by using a private link."""

    def get(self, request, *args, **kwargs):
        self.object: Deck = self.get_object()
        if self.object.owner == request.user or self.object.is_public:
            # If the owner is accessing with the private link or the Deck is public,
            # redirect to the official one
            return redirect(self.object.get_absolute_url())
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self) -> Manager[Deck]:
        """When retrieving the object, we need to make sure that the code matches with
        the requested Deck.

        Returns:
            Manager[Deck]: The view's queryset.
        """
        code = self.kwargs["code"]
        deck_id = self.kwargs["pk"]
        try:
            link = PrivateLink.objects.get(code=code, deck__id=deck_id)
            link.last_accessed_at = timezone.now()
            link.save(update_fields=["last_accessed_at"])
            return (
                Deck.objects.filter(id=deck_id)
                .select_related("hero", "owner", "owner__profile")
                .annotate(
                    follower_count=Count("owner__followers", distinct=True),
                    following_count=Count("owner__following", distinct=True),
                )
            )
        except PrivateLink.DoesNotExist:
            raise Http404("Private link does not exist")


@login_required
@ajax_request()
def create_private_link(request: HttpRequest, pk: int) -> HttpResponse:
    """Function to create a PrivateLink with AJAX.
    Ideally it should be moved to the API app.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        # Retrieve the referenced Deck
        deck = Deck.objects.get(pk=pk, owner=request.user)
        if deck.is_public:
            return JsonResponse(
                {
                    "error": {
                        "code": HTTPStatus.BAD_REQUEST,
                        "message": _("Invalid request"),
                    }
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        pl, created = PrivateLink.objects.get_or_create(deck=deck)
        status = {"created": created, "link": pl.get_absolute_url()}

    except Deck.DoesNotExist:
        return JsonResponse(
            {"error": {"code": HTTPStatus.NOT_FOUND, "message": _("Deck not found")}},
            status=HTTPStatus.NOT_FOUND,
        )
    return JsonResponse({"data": status}, status=HTTPStatus.OK)


@login_required
def delete_deck(request: HttpRequest, pk: int) -> HttpResponse:
    """View to delete a Deck.

    Args:
        request (HttpRequest): The request.
        pk (int): The ID of the Deck to be deleted.

    Returns:
        HttpResponse: The response.
    """

    # The user is part of the filter to ensure ownership.
    # The delete statement won't fail even if the filter doesn't match any record, which
    # means that if the Deck is not found (doesn't exist or isn't owned) the view will
    # fail silently and redirect the user to their Decks regardless of the result.
    Deck.objects.filter(pk=pk, owner=request.user).delete()
    return redirect("own-deck")
