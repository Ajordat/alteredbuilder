
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