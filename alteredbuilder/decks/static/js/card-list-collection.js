
document.addEventListener("DOMContentLoaded", () => {
    startCollection();
    displayTextCollection();
});

document.getElementById("save-collection").addEventListener("click", () => {

    const textCollection = document.getElementById("collection-list").value;

    let collection = textCollectionToEntries(textCollection);

    saveCollectionLocal(collection);
    // We parse again the collection from the entries because there might have been changes
    saveCollectionRemote(collectionToText(collection), true);
    importUniqueCards(collection);

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
    const badges = document.querySelectorAll('.card-in-collection');
    badges.forEach(badge => badge.classList.add("d-none"));
}

function markCollectedCards(collection, settings) {

    const cards = document.getElementsByClassName('card-display');
    var finalCollection = {};
    var familyCollection = {};

    if (settings.mergeSets) {
        for (let [reference, quantity] of Object.entries(collection)) {
            let cardFamily = reference.split("_").slice(3, 6).join("_");
            if (!cardFamily.includes("_U")) {
                familyCollection[cardFamily] = quantity + (familyCollection[cardFamily] || 0);
            } else {
                finalCollection[reference] = 1;
            }
        }
    } else {
        finalCollection = { ...collection };
    }

    for (let card of cards) {
        const cardReference = card.getAttribute('data-card-reference');

        if (finalCollection[cardReference]) {
            setCardCount(card, finalCollection[cardReference]);
            continue;
        }
        const cardFamily = card.getAttribute('data-card-family');

        if (familyCollection[cardFamily]) {
            setCardCount(card, familyCollection[cardFamily]);
            continue;
        }
    }
}

function printSettings(settings) {
    document.getElementById("merge-sets-check").checked = settings.mergeSets;
}

function setCardCount(parentElement, count) {
    parentElement.querySelector(".collection-count").textContent = count;
    parentElement.querySelector(".card-in-collection").classList.remove("d-none");
}
