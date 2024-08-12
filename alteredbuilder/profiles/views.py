from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.shortcuts import redirect, render
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from hitcount.views import HitCountDetailView

from decks.models import Deck
from profiles.forms import UserProfileForm
from profiles.models import UserProfile
from profiles.utils import get_discord_handle


class ProfileListView(ListView):
    queryset = UserProfile.objects.select_related("user").order_by("-created_at")[:5]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context


class ProfileDetailView(HitCountDetailView):

    queryset = get_user_model().objects.select_related("profile")
    context_object_name = "builder"
    slug_field = "profile__code"
    slug_url_kwarg = "code"
    template_name = "profiles/userprofile_detail.html"
    count_hit = True

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["deck_list"] = Deck.objects.filter(owner=self.object, is_public=True)

        if self.object.profile.discord_public:
            context["discord_handle"] = get_discord_handle(self.object)

        return context


class EditProfileFormView(LoginRequiredMixin, FormView):
    template_name = "profiles/edit_profile.html"
    form_class = UserProfileForm

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        for attr in self.form_class.base_fields:
            initial[attr] = getattr(self.request.user.profile, attr)
        return initial

    def form_valid(self, form: UserProfileForm):
        profile = self.request.user.profile
        for attr in form.fields:
            setattr(profile, attr, form.cleaned_data[attr])
        profile.save()
        return super().form_valid(form)
    
    def get_success_url(self) -> str:
        return self.request.user.profile.get_absolute_url()