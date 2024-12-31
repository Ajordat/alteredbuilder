
const LS_COLLECTION_KEY = "collectionContent";
const LS_SETTINGS_KEY = "collectionSettings";

document.addEventListener("DOMContentLoaded", () => {
    startCollection();
});

document.getElementById("save-collection").addEventListener("click", () => {

    const collectionListEl = document.getElementById("collection-list");

    let cardEntries = collectionListEl.value.trim().split("\n");

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

function parseCardEntries(cardEntries) {
    let collection = {};
    for (let cardEntry of cardEntries) {
        let card = cardEntry.split(" ");
        collection[card[1]] = parseInt(card[0]);
    }
    return collection;
}

function startCollection() {

    resetCollectedCards();

    let collection = fetchCollection();

    console.log(collection);

    if (!collection) {
        return;
    }

    let settings = fetchSettings();

    markCollectedCards(collection, settings);
}

function saveCollection(collection) {
    localStorage.setItem(LS_COLLECTION_KEY, JSON.stringify(collection));
}
function fetchCollection() {
    return JSON.parse(localStorage.getItem(LS_COLLECTION_KEY));
}
function saveSettings(settings) {
    localStorage.setItem(LS_SETTINGS_KEY, JSON.stringify(settings));
}
function fetchSettings() {
    let settings = JSON.parse(localStorage.getItem(LS_SETTINGS_KEY));

    if (!settings) {
        settings = {
            mergeSets: false
        }
        saveSettings(settings);
    }

    return settings;
}

function resetCollectedCards() {
    const badges = document.querySelectorAll('.card-badge');
    badges.forEach(badge => badge.remove());
}

function markCollectedCards(collection, settings) {
    console.log(collection);

    const cards = document.getElementsByClassName('card-display');
    var finalCollection = {};

    if (settings.mergeSets) {
        for (let [reference, quantity] of Object.entries(collection)) {
            console.log(reference, quantity);
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
        finalCollection = {...collection};
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