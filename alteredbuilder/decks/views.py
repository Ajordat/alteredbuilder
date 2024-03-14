from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .models import Card, CardInDeck, Character, Deck, Hero, Landmark, Spell
from .forms import DecklistForm
from .exceptions import MalformedDeckException


# Create your views here.
class DeckListView(ListView):
    model = Deck
    paginate_by = 10


class DeckDetailView(DetailView):
    model = Deck

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["character_list"] = [card for card in self.object.cards.all() if card.type == Card.Type.CHARACTER]
        context["spell_list"] = [card for card in self.object.cards.all() if card.type == Card.Type.SPELL]
        context["landmark_list"] = [card for card in self.object.cards.all() if card.type == Card.Type.LANDMARK]
        return context


@transaction.atomic
def create_new_deck(deck_form):
    decklist = deck_form["decklist"]
    deck = Deck.objects.create(name=deck_form["name"])
    has_hero = False
    for line in decklist.splitlines():
        try:
            count, reference = line.split()
        except ValueError:
            # The form validator only checks if there's at least one
            # line with the correct format
            raise MalformedDeckException(f"Failed to unpack '{line}'")

        try:
            card = Card.objects.get(reference=reference)
        except Card.DoesNotExist:
            raise MalformedDeckException(f"Card '{reference}' does not exist")

        if card.type == Card.Type.HERO:
            if not has_hero:
                deck.hero = Hero.objects.get(reference=reference)
                deck.save()
            else:
                # Report error
                pass
        else:
            CardInDeck.objects.create(deck=deck, card=card, quantity=count)

    if not has_hero:
        # Report error
        pass

    return deck

class NewDeckFormView(FormView):
    template_name = "decks/new_deck.html"
    form_class = DecklistForm

    def form_valid(self, form):
        # Create deck
        try:
            self.deck = create_new_deck(form.cleaned_data)
        except MalformedDeckException as e:
            form.add_error("decklist", e.detail)
            return render(self.request, self.template_name, {"form": form})

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("deck-detail", kwargs={"pk":self.deck.id})


def cards(request):
    cards = Card.objects.order_by("faction")[:20]

    context = {"card_list": cards}
    return render(request, "decks/cards.html", context)
