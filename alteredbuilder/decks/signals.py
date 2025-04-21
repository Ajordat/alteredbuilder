from typing import Type
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from decks.models import DeckCopy


@receiver(post_save, sender=DeckCopy)
def update_deck_copy_counter(
    sender: Type[DeckCopy], instance: DeckCopy, created: bool, **kwargs
) -> None:
    if created:
        source_deck = instance.source_deck
        if source_deck:
            source_deck.copy_count = F("copy_count") + 1
            source_deck.save(update_fields=["copy_count"])
