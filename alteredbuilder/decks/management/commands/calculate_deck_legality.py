from typing import Any

from config.commands import BaseCommand
from decks.game_modes import update_deck_legality
from decks.models import Deck


class Command(BaseCommand):
    help = "Recalculates the legality of the decks"
    version = "1.0.0"

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-illegal",
            action="store_true",
            help="Limit the update to illegal decks",
        )
        parser.add_argument(
            "--chunk-size",
            action="store",
            default=1000,
            help="Maximum amount of decks to hold in memory before saving them into the database",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """The command's entrypoint. Queries the API for each language."""

        qs = Deck.objects.prefetch_related("cardindeck_set__card")
        if options["only_illegal"]:
            qs = qs.filter(is_standard_legal=False)

        update_fields = [
            "is_standard_legal",
            "standard_legality_errors",
            "is_exalts_legal",
            "is_doubles_legal",
        ]
        decks_chunk = []
        chunk_size = 0
        max_chunk_size = options["chunk_size"]
        deck_count = 0
        for deck in qs:
            update_deck_legality(deck)
            decks_chunk.append(deck)
            chunk_size += 1
            if chunk_size >= max_chunk_size:
                deck_count += Deck.objects.bulk_update(decks_chunk, update_fields)
                decks_chunk = []
                chunk_size = 0

        deck_count += Deck.objects.bulk_update(decks_chunk, update_fields)

        self.stdout.write(f"Updated {deck_count} decks")
