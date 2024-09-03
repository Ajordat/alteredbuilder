from collections import defaultdict
from datetime import timedelta
from typing import Any
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Exists, F, OuterRef, Q, Sum
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import localtime
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from hitcount.models import Hit

from decks.models import Card, Deck, LovePoint
from profiles.forms import UserProfileForm
from profiles.models import Follow, UserProfile


class ProfileListView(ListView):
    """View to display a list of profiles. It retrieves the latest users, the users
    with the most views and the most followed users.
    """

    template_name = "profiles/userprofile_list.html"
    context_object_name = "latest_users"
    USER_COUNT_DISPLAY = 10

    def get_queryset(self) -> QuerySet[Any]:
        """Return a queryset with the Users who last joined the platform.

        Returns:
            QuerySet[User]: The latest users to join the platform.
        """

        # Retrieve the latest users
        qs = (
            get_user_model()
            .objects.select_related("profile")
            .order_by("-date_joined")[: self.USER_COUNT_DISPLAY]
        )

        # If the requester is authenticated, annotate the user list indicating if the
        # requester follows any of them
        if self.request.user.is_authenticated:
            qs = qs.annotate(
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("pk"), follower=self.request.user
                    )
                )
            )
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the most viewed and most followed users to the context and if they're
        followed by the requester. It also adds general metrics of the platform.

        Returns:
            dict[str, Any]: The view's context.
        """
        context = super().get_context_data(**kwargs)

        # Extract the most viewed users
        most_viewed_users = (
            get_user_model()
            .objects.alias(total_hits=Sum("deck__hit_count_generic__hits"))
            .annotate(deck_count=Count("deck", filter=Q(deck__is_public=True)))
            .select_related("profile")
            .order_by(F("total_hits").desc(nulls_last=True))[: self.USER_COUNT_DISPLAY]
        )

        # Extract the most followed users
        most_followed_users = (
            get_user_model()
            .objects.annotate(follower_count=Count("followers"))
            .filter(follower_count__gt=0)
            .select_related("profile")
            .order_by("-follower_count")[: self.USER_COUNT_DISPLAY]
        )

        # Annotate the querysets indicating whether the requester follows the users
        if self.request.user.is_authenticated:
            most_viewed_users = most_viewed_users.annotate(
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("pk"), follower=self.request.user
                    )
                )
            )
            most_followed_users = most_followed_users.annotate(
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("pk"), follower=self.request.user
                    )
                )
            )
        context["most_viewed_users"] = most_viewed_users
        context["most_followed_users"] = most_followed_users

        # Extract the metrics of the last 7 days
        timelapse = localtime() - timedelta(days=7)

        # Extract the user count
        context["total_user_count"] = get_user_model().objects.count()
        context["last_week_user_count"] = (
            get_user_model().objects.filter(date_joined__gte=timelapse).count()
        )

        # Extract the public deck count
        context["total_deck_count"] = Deck.objects.filter(is_public=True).count()
        context["last_week_deck_count"] = Deck.objects.filter(
            is_public=True, created_at__gte=timelapse
        ).count()

        # Extract the count of unique cards imported
        context["total_unique_card_count"] = Card.objects.filter(
            rarity=Card.Rarity.UNIQUE
        ).count()
        context["last_week_unique_card_count"] = Card.objects.filter(
            rarity=Card.Rarity.UNIQUE, created_at__gte=timelapse
        ).count()

        # Extract the amount of hits
        context["last_week_hits"] = Hit.objects.filter(created__gte=timelapse).count()

        return context


class FollowersListView(ListView):
    """View to display the amount of followed users and followers that a user has."""

    template_name = "profiles/followers_list.html"
    context_object_name = "followers"
    # paginate_by = 20

    def get_queryset(self) -> QuerySet[Follow]:
        """Return a queryset with the Users following the displayed profile.

        Returns:
            QuerySet[Follow]: Users following the current profile.
        """

        self.builder = get_user_model().objects.get(profile__code=self.kwargs["code"])
        qs = Follow.objects.filter(followed=self.builder).select_related(
            "follower__profile"
        )

        # Annotate the records indicating whether the users are followed by the
        # requester
        if self.request.user.is_authenticated:
            qs = qs.annotate(
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("follower"), follower=self.request.user
                    )
                )
            )

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the displayed profile and the followed users to the context.

        Returns:
            dict[str, Any]: The view's context.
        """

        context = super().get_context_data(**kwargs)

        # Add the displayed user
        context["builder"] = self.builder

        # Extract the followed users and if they're being followed by the requester
        followed_users = Follow.objects.filter(follower=self.builder).select_related(
            "followed__profile", "follower__profile"
        )
        if self.request.user.is_authenticated:
            followed_users = followed_users.annotate(
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("followed"), follower=self.request.user
                    )
                )
            )
        context["followed_users"] = followed_users

        return context


class ProfileDetailView(DetailView):
    """View that displays the profile of a user."""

    context_object_name = "builder"
    slug_field = "profile__code"
    slug_url_kwarg = "code"
    template_name = "profiles/userprofile_detail.html"

    def get_queryset(self) -> QuerySet[Any]:
        """Return a queryset with the requested profile, including the amount of
        followers, followed users and if it's followed by the requester.

        Returns:
            QuerySet[User]: The requested user and its profile.
        """

        # Get the user and its Follow numbers
        qs = (
            get_user_model()
            .objects.select_related("profile")
            .annotate(
                follower_count=Count("followers", distinct=True),
                following_count=Count("following", distinct=True),
            )
        )

        # Annotate if it's followed by the requester
        if self.request.user.is_authenticated:
            qs = qs.annotate(
                is_followed=Exists(
                    Follow.objects.filter(
                        follower=self.request.user, followed=OuterRef("pk")
                    )
                )
            )

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the user's Decks and their faction distribution to the context.

        Returns:
            dict[str, Any]: The view's context.
        """
        context = super().get_context_data(**kwargs)

        # Extract the user's decks
        deck_list = Deck.objects.filter(
            owner=self.object, is_public=True
        ).select_related("hero")

        # Annotate the Decks if they're loved by the requester
        if self.request.user.is_authenticated:
            deck_list = deck_list.annotate(
                is_loved=Exists(
                    LovePoint.objects.filter(
                        deck=OuterRef("pk"), user=self.request.user
                    )
                )
            )

        context["deck_list"] = deck_list

        # Generate the faction distribution
        faction_distribution = defaultdict(int)
        for deck in deck_list:
            if deck.hero:
                faction_distribution[deck.hero.get_faction_display()] += 1

        context["faction_distribution"] = faction_distribution

        return context


class EditProfileFormView(LoginRequiredMixin, FormView):
    """View to modify a user's profile."""

    template_name = "profiles/edit_profile.html"
    form_class = UserProfileForm

    def get_initial(self) -> dict[str, Any]:
        """Add the existing values of the profile to the initial values of the form.

        Returns:
            dict[str, Any]: The form's initial values.
        """
        initial = super().get_initial()
        for attr in self.form_class.base_fields:
            initial[attr] = getattr(self.request.user.profile, attr)
        return initial

    def form_valid(self, form: UserProfileForm) -> HttpResponse:
        """If the form is valid, set the values on the profile and save.

        Args:
            form (UserProfileForm): The filed form.

        Returns:
            HttpResponse: The view's response
        """

        profile = self.request.user.profile
        for attr in form.fields:
            setattr(profile, attr, form.cleaned_data[attr])
        profile.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """If the form submission is successful, redirect to the profile view.

        Returns:
            str: The URL of the profile view.
        """
        return self.request.user.profile.get_absolute_url()


@login_required
def follow_user(request: HttpRequest, code: uuid.uuid4) -> HttpResponse:
    """View to follow a user.

    Args:
        request (HttpRequest): The request object.
        code (uuid.uuid4): The profile's code that has to be followed by the requester.

    Returns:
        HttpResponse: The view's response.
    """

    # Get the profile to be followed
    builder_profile = get_object_or_404(UserProfile, code=code)

    # If it's not the same user, create a Follow record
    if request.user != builder_profile.user:
        Follow.objects.get_or_create(
            follower=request.user, followed=builder_profile.user
        )

    # Redirect to the followed profile
    return redirect(builder_profile.get_absolute_url())


@login_required
def unfollow_user(request: HttpRequest, code: uuid.uuid4) -> HttpResponse:
    """View to unfollow a user.

    Args:
        request (HttpRequest): The request object.
        code (uuid.uuid4): The profile's code that has to be unfollowed by the
                           requester.

    Returns:
        HttpResponse: The view's response.
    """

    # Get the profile to be unfollowed
    builder_profile = get_object_or_404(UserProfile, code=code)

    # Delete the Follow records that made that relationship. There should only be one
    Follow.objects.filter(follower=request.user, followed=builder_profile.user).delete()

    # Redirect to the unfollowed profile
    return redirect(builder_profile.get_absolute_url())
