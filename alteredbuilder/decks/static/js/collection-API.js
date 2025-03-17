
const LS_COLLECTION_KEY = "collectionContent";
const LS_SETTINGS_KEY = "collectionSettings";


function saveCollection(collection) {
    localStorage.setItem(LS_COLLECTION_KEY, JSON.stringify(collection));
}

function fetchCollection() {
    try {
        return JSON.parse(localStorage.getItem(LS_COLLECTION_KEY));
    } catch (e) {
        return {};
    }
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

function textCollectionToEntries(textCollection) {
    return textCollection.trim().split("\n");
}

function parseCardEntries(cardEntries) {
    let collection = {};
    for (let cardEntry of cardEntries) {
        if (!cardEntry)
            continue;
        let card = cardEntry.split(" ");
        collection[card[1]] = parseInt(card[0]);
    }
    return collection;
}

function collectionToText(collection) {
    return Object.entries(collection).map(([reference, quantity]) => `${quantity} ${reference}`).join("\n");
}

function importUniqueCards(previousCollection, collection) {
    const previousUniqueCards = Object.keys(previousCollection).filter((reference) => reference.includes("_U_"));
    const uniqueCards = Object.keys(collection).filter((reference) => reference.includes("_U_") && !previousUniqueCards.includes(reference));

    if (uniqueCards.length == 0) {
        return;
    }

    fetch("/es/decks/import-card/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: JSON.stringify({
            references: uniqueCards
        })
    })
}
