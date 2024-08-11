from typing import Any
from django.views.generic.detail import DetailView

from decks.models import Deck
from profiles.models import UserProfile


# Create your views here.
class ProfileDetailView(DetailView):
    model = UserProfile
    template_name = "profiles/profile_detail.html"
    context_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["deck_list"] = Deck.objects.filter(owner=self.object.user, is_public=True)

        return context