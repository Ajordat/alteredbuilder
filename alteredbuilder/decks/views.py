from collections import defaultdict

from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .models import Card, CardInDeck, Deck, Hero
from .forms import DecklistForm
from .exceptions import MalformedDeckException


# Create your views here.
class DeckListView(ListView):
    model = Deck
    queryset = Deck.objects.filter(is_public=True).order_by("-created_at")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["own_decks"] = Deck.objects.filter(
                owner=self.request.user
            ).order_by("-created_at")
        return context


class DeckDetailView(DetailView):
    model = Deck
    
    def get_queryset(self):
        return Deck.objects.filter(Q(is_public=True) | Q(owner=self.request.user))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        decklist = self.object.cardindeck_set.all()

        hand_counter = defaultdict(int)
        recall_counter = defaultdict(int)

        d = {
            Card.Type.CHARACTER: [[], 0, "character"],
            Card.Type.SPELL: [[], 0, "spell"],
            Card.Type.LANDMARK: [[], 0, "landmark"],
        }
        for cid in decklist:
            d[cid.card.type][0].append((cid.quantity, cid.card))
            d[cid.card.type][1] += cid.quantity
            hand_counter[getattr(cid.card, d[cid.card.type][2]).main_cost] += 1
            recall_counter[getattr(cid.card, d[cid.card.type][2]).recall_cost] += 1

        context |= {
            "character_list": d[Card.Type.CHARACTER][0],
            "spell_list": d[Card.Type.SPELL][0],
            "landmark_list": d[Card.Type.LANDMARK][0],
            "stats": {
                "type_distribution": {
                    "characters": d[Card.Type.CHARACTER][1],
                    "spells": d[Card.Type.SPELL][1],
                    "landmarks": d[Card.Type.LANDMARK][1],
                },
                "total_count": d[Card.Type.CHARACTER][1] + d[Card.Type.SPELL][1] + d[Card.Type.LANDMARK][1],
                "mana_distribution": {
                    "hand": hand_counter,
                    "recall": recall_counter,
                },
            },
        }

        return context


@transaction.atomic
def create_new_deck(user, deck_form):
    decklist = deck_form["decklist"]
    deck = Deck.objects.create(
        name=deck_form["name"], owner=user, is_public=deck_form["is_public"]
    )
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
                try:
                    deck.hero = Hero.objects.get(reference=reference)
                except Hero.DoesNotExist:
                    # This situation would imply a database inconsistency.
                    raise MalformedDeckException(f"Card '{reference}' does not exist")
                deck.save()
                has_hero = True
            else:
                # Report error
                raise MalformedDeckException("Two heroes present in the decklist")
        else:
            CardInDeck.objects.create(deck=deck, card=card, quantity=count)

    if not has_hero:
        # Report error
        raise MalformedDeckException("Missing hero in decklist")

    return deck


class NewDeckFormView(FormView):
    template_name = "decks/new_deck.html"
    form_class = DecklistForm

    def form_valid(self, form):
        # Create deck
        try:
            self.deck = create_new_deck(self.request.user, form.cleaned_data)
        except MalformedDeckException as e:
            form.add_error("decklist", e.detail)
            return render(self.request, self.template_name, {"form": form})

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("deck-detail", kwargs={"pk": self.deck.id})


def cards(request):
    cards = Card.objects.order_by("reference")[:20]

    context = {"card_list": cards}
    return render(request, "decks/cards.html", context)
