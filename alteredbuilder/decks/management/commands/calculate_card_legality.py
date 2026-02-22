from typing import Any

from config.commands import BaseCommand
from decks.models import BannedCard, Card


class Command(BaseCommand):
    help = "Updates the legality of cards"
    version = "1.0.0"

    def handle(self, *args: Any, **options: Any) -> None:
        """The command's entrypoint"""

        for faction in Card.Faction.as_list():
            self.update_faction(faction)

    def update_faction(self, faction: Card.Faction):
        banned_cards = BannedCard.objects.filter(faction=faction)
        banned_cards = [ban.family_name for ban in banned_cards]

        card_chunk = []
        for card in Card.objects.filter(faction=faction):
            if card.get_card_code() in banned_cards:
                if card.is_legal:
                    card.is_legal = False
                    card_chunk.append(card)
                    self.stdout.write(
                        f"The {card.rarity} version of card {card.name} in {card.faction} has been banned"
                    )

            elif not card.is_legal:
                card.is_legal = True
                card_chunk.append(card)
                self.stdout.write(
                    f"The {card.rarity} version of card {card.name} in {card.faction} is now legal"
                )

        if card_chunk:
            updated = Card.objects.bulk_update(card_chunk, ["is_legal"])
            self.stdout.write(f"Updated {updated} cards in {faction}")
        else:
            self.stdout.write(f"All cards in {faction} are up to date")
