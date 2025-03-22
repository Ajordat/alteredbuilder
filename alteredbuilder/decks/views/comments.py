from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from api.utils import ajax_request, ApiJsonResponse
from decks.models import Comment, CommentVote, Deck
from decks.forms import CommentForm


@login_required
def create_comment(request: HttpRequest, pk: int) -> HttpResponse:
    """
    View to create a Comment for a Deck.

    Args:
        request: The HTTP request object.
        pk: The primary key of the Deck for which a comment is being created.

    Returns:
        HttpResponse: The response object.
    """

    deck = get_object_or_404(Deck, pk=pk, is_public=True)

    if request.method == "POST":
        # Instantiate the form with the POST data
        form = CommentForm(request.POST)
        if form.is_valid():
            # Create a new comment linked to the deck and user
            Comment.objects.create(
                user=request.user, deck=deck, body=form.cleaned_data["body"]
            )

            # Increment the comment count on the Deck model
            deck.comment_count = F("comment_count") + 1
            deck.save(update_fields=["comment_count"])

    return redirect(deck.get_absolute_url())


@login_required
@ajax_request()
def vote_comment(request: HttpRequest, pk: int, comment_pk: int) -> HttpResponse:
    """Function to upvote a Comment with AJAX.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck
        comment_pk (int): Id of the target comment

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        comment = Comment.objects.get(pk=comment_pk, deck__pk=pk)
        comment_vote = CommentVote.objects.get(user=request.user, comment=comment)
        comment_vote.delete()
        comment.vote_count = F("vote_count") - 1
        comment.save()
        status = {"deleted": True}
    except CommentVote.DoesNotExist:
        CommentVote.objects.create(user=request.user, comment=comment)
        comment.vote_count = F("vote_count") + 1
        comment.save()
        status = {"created": True}
    except Comment.DoesNotExist:
        return ApiJsonResponse(_("Comment not found"), HTTPStatus.NOT_FOUND)

    return ApiJsonResponse(status, HTTPStatus.OK)


@login_required
@ajax_request()
def delete_comment(request: HttpRequest, pk: int, comment_pk: int) -> HttpResponse:
    """Function to delete a Comment with AJAX.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck
        comment_pk (int): Id of the target comment

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        deck = Deck.objects.get(pk=pk)
        comment = Comment.objects.get(pk=comment_pk, deck=deck, user=request.user)
        comment.delete()
        deck.comment_count = F("comment_count") - 1
        deck.save(update_fields=["comment_count"])

        status = {"deleted": True}
    except Comment.DoesNotExist:
        return ApiJsonResponse(_("Comment not found"), HTTPStatus.NOT_FOUND)
    except Deck.DoesNotExist:
        return ApiJsonResponse(_("Deck not found"), HTTPStatus.NOT_FOUND)

    return ApiJsonResponse(status, HTTPStatus.OK)
