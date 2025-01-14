
document.addEventListener("DOMContentLoaded", () => {
    startCollection();
    displayTextCollection();
});

document.getElementById("save-collection").addEventListener("click", () => {

    const collectionListEl = document.getElementById("collection-list");

    let cardEntries = textCollectionToEntries(collectionListEl.value);
    let collection = parseCardEntries(cardEntries);

    saveCollection(collection);

    startCollection();
});

document.getElementById("update-collection-settings").addEventListener("click", () => {
    const mergeSetsEl = document.getElementById("merge-sets-check");

    let settings = {
        mergeSets: mergeSetsEl.checked
    };
    saveSettings(settings);

    startCollection();
});

function displayTextCollection() {
    let collection = fetchCollection();
    if (!collection) {
        return;
    }
    printCollection(collection);
}

function printCollection(collection) {
    document.getElementById("collection-list").value = collectionToText(collection);
}

function startCollection() {

    resetCollectedCards();

    let collection = fetchCollection();

    console.log(collection);

    if (!collection) {
        return;
    }

    let settings = fetchSettings();
    printSettings(settings);

    markCollectedCards(collection, settings);
}

function resetCollectedCards() {
    const badges = document.querySelectorAll('.card-badge');
    badges.forEach(badge => badge.remove());
}

function markCollectedCards(collection, settings) {

    const cards = document.getElementsByClassName('card-display');
    var finalCollection = {};

    if (settings.mergeSets) {
        for (let [reference, quantity] of Object.entries(collection)) {
            finalCollection[reference] = quantity + (finalCollection[reference] || 0);
            if (reference.includes("_CORE_")) {
                let altRef = reference.replace("_CORE_", "_COREKS_");
                finalCollection[altRef] = quantity + (finalCollection[altRef] || 0);
            } else if (reference.includes("_COREKS_")) {
                let altRef = reference.replace("_COREKS_", "_CORE_");
                finalCollection[altRef] = quantity + (finalCollection[altRef] || 0);
            }
        }
    } else {
        finalCollection = { ...collection };
    }

    for (let card of cards) {
        const cardReference = card.getAttribute('data-card-reference');

        if (finalCollection[cardReference]) {

            const badge = document.createElement('div');
            badge.textContent = finalCollection[cardReference];
            badge.className = 'card-badge px-2 py-1 border border-white';

            card.style.position = 'relative';
            card.appendChild(badge);
        }
    }
}

function printSettings(settings) {
    document.getElementById("merge-sets-check").checked = settings.mergeSets;
}