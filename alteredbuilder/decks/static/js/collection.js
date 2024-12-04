
const LS_COLLECTION_KEY = "collection";

document.addEventListener("DOMContentLoaded", () => {
    startCollection();
});

document.getElementById("save-collection").addEventListener("click", () => {

    const collectionListEl = document.getElementById("collection-list");

    let cardEntries = collectionListEl.value.trim().split("\n");

    let collection = parseCardEntries(cardEntries);

    saveCollection(collection);

    resetCollectedCards();
    markCollectedCards(collection);
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

    markCollectedCards(collection);
}

function saveCollection(collection) {
    localStorage.setItem(LS_COLLECTION_KEY, JSON.stringify(collection));
}
function fetchCollection() {
    return JSON.parse(localStorage.getItem(LS_COLLECTION_KEY));
}

function resetCollectedCards() {
    const badges = document.querySelectorAll('.card-badge');
    badges.forEach(badge => badge.remove());
}

function markCollectedCards(collection) {
    console.log(collection);

    const cards = document.getElementsByClassName('card-display');

    for (let card of cards) {
        const cardReference = card.getAttribute('data-card-reference');

        if (collection[cardReference]) {

            const badge = document.createElement('div');
            badge.textContent = collection[cardReference];
            badge.className = 'card-badge px-2 py-1 border border-white';

            card.style.position = 'relative';
            card.appendChild(badge);
        }
    }
}