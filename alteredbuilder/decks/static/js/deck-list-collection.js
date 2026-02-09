
function markDeckAvailability() {
    var collection = fetchCollection();

    if (!collection || Object.keys(collection).length === 0) {
        return;
    }

    var deckCardsRaw = document.getElementById("deck-cards-data");
    if (!deckCardsRaw) {
        return;
    }

    var deckCards;
    try {
        deckCards = JSON.parse(JSON.parse(deckCardsRaw.textContent));
    } catch (e) {
        console.error("Failed to parse deck cards data:", e);
        return;
    }

    var settings = fetchSettings();

    // Build collection lookup with mergeSets support (same logic as deck-detail.js)
    var finalCollection = {};
    var familyCollection = {};

    if (settings.mergeSets) {
        for (var ref in collection) {
            var cardFamily = ref.split("_").slice(3, 6).join("_");
            if (!cardFamily.includes("_U")) {
                familyCollection[cardFamily] = collection[ref] + (familyCollection[cardFamily] || 0);
            } else {
                finalCollection[ref] = 1;
            }
        }
    } else {
        for (var ref in collection) {
            finalCollection[ref] = collection[ref];
        }
    }

    var deckDisplays = document.querySelectorAll(".deck-display[data-deck-id]");

    for (var i = 0; i < deckDisplays.length; i++) {
        var deckEl = deckDisplays[i];
        var deckId = deckEl.getAttribute("data-deck-id");
        var cards = deckCards[deckId];

        if (!cards || cards.length === 0) {
            continue;
        }

        var allAvailable = true;
        for (var j = 0; j < cards.length; j++) {
            var cardRef = cards[j].ref;
            var needed = cards[j].qty;

            // Check exact reference first
            var owned = finalCollection[cardRef] || 0;

            // If not found and mergeSets is enabled, check by family
            if (owned < needed && settings.mergeSets) {
                var family = cardRef.split("_").slice(3, 6).join("_");
                if (!family.includes("_U")) {
                    owned = familyCollection[family] || 0;
                }
            }

            if (owned < needed) {
                allAvailable = false;
                break;
            }
        }

        var badge = deckEl.querySelector(".deck-availability-badge");
        if (badge) {
            badge.classList.remove("d-none");
            if (allAvailable) {
                badge.innerHTML = '<span class="badge bg-success shadowed ms-2"><i class="fa-solid fa-check"></i> Available</span>';
            } else {
                badge.innerHTML = '<span class="badge bg-danger shadowed ms-2"><i class="fa-solid fa-xmark"></i> Missing</span>';
            }
        }
    }
}

markDeckAvailability();