
const LS_COLLECTION_KEY = "collectionContent";
const LS_SETTINGS_KEY = "collectionSettings";


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
