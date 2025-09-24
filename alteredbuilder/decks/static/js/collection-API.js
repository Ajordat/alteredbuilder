
const LS_COLLECTION_KEY = "collectionContent";
const LS_SETTINGS_KEY = "collectionSettings";


function saveCollectionLocal(collection) {
    localStorage.setItem(LS_COLLECTION_KEY, JSON.stringify(collection));
}

function saveCollectionRemote(textCollection, displayToast) {
    // Requires deckfmt being imported
    let encodedCollection;
    try {
        encodedCollection = deckfmt.encodeList(textCollection);
    } catch (e) {
        console.error(e);
        displaySimpleToast(gettext("Failed to save collection remotely."));
        return false;
    }

    let url = window.location.origin + window.location.pathname.slice(0, 4) + "decks/collection/update/";
    ajaxRequest(url, { collection: encodedCollection })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            let errorMsgToast;
            if (response.status == 403) {
                errorMsgToast = gettext("Login to save your collection remotely.");
            } else {
                errorMsgToast = gettext("Failed to save collection remotely.");
            }
            if (displayToast) {
                displaySimpleToast(errorMsgToast);
            }
            throw new Error(`Failed to store collection: ${response.statusText}`);
        })
        .then(payload => {
            if (!displayToast) {
                return false;
            }
            if (!payload.data || !payload.data.success) {
                displaySimpleToast(gettext("Failed to save collection remotely."));
            } else {
                displaySimpleToast(gettext("Saved collection remotely."));
            }
            return false;
        }).catch(error => {
            console.error("Store error:", error);
        });
}

function fetchCollection() {
    try {
        let encodedCollection = document.getElementById('user-collection').textContent;
        if (!encodedCollection || encodedCollection == "null" || encodedCollection == '""') {
            console.log("no remote collection");
            // If no collection is given remotely, check if there's a local collection
            // and if so, send it to the server and return it.
            let savedCollection = localStorage.getItem(LS_COLLECTION_KEY);
            if (!savedCollection) {
                console.log("no local collection");
                return {};
            }
            console.log("found local collection");
            // saveCollectionRemote(collectionToText(savedCollection), false);
            return JSON.parse(savedCollection);
        }
        console.log("found remote collection");
        return textCollectionToEntries(deckfmt.decodeList(encodedCollection));
    } catch (e) {
        console.error(e);
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
            mergeSets: true
        }
        saveSettings(settings);
    }

    return settings;
}

function textCollectionToEntries(textCollection) {
    const cardEntries = textCollection.trim().split("\n");
    let collection = {};
    for (let cardEntry of cardEntries) {
        if (!cardEntry || cardEntry.includes("_FOILER_")) {
            console.log(`skipped ${cardEntry}`)
            continue;
        }
        let card = cardEntry.split(" ");
        collection[card[1]] = parseInt(card[0]);
    }
    return collection;
}

function collectionToText(collection) {
    return Object.entries(collection).filter(([ref, _]) => !ref.includes("_FOILER_")).map(([reference, quantity]) => `${Math.min(quantity, 65)} ${reference}`).join("\n");
}

function importUniqueCards(collection) {
    const uniqueCards = Object.keys(collection).filter((reference) => reference.includes("_U_"));

    if (uniqueCards.length == 0) {
        return;
    }
    console.log(uniqueCards);

    fetch("/es/decks/import-multiple-cards/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            references: uniqueCards
        })
    })
}
