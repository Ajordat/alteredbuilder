from typing import Any

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from decks.models import Deck
from profiles.forms import UserProfileForm
from profiles.models import UserProfile
from profiles.utils import get_discord_handle


class ProfileListView(ListView):
    queryset = UserProfile.objects.order_by("-created_at")


class ProfileDetailView(DetailView):
    model = UserProfile
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["deck_list"] = Deck.objects.filter(owner=self.object.user, is_public=True)
        context["discord_handle"] = get_discord_handle(self.object.user) if self.object.discord_public else None

        return context


@login_required
def edit_profile(request):
    profile: UserProfile = request.user.profile  # Assuming OneToOne relationship is set up
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(profile.get_absolute_url())  # Redirect to profile detail view after saving
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'profiles/edit_profile.html', {'form': form})