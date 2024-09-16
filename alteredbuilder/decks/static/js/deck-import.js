

async function importOfficialDeck(deckCode) {

    let url = `https://api.altered.gg/deck_user_lists/${deckCode}`;
    
    let response = await fetch(url);
    let payload = await response.json();

    if (!response.ok) {
        reportError(interpolate(gettext('The deck with ID "%(code)s" was not found'), {code: deckCode}, true));
        return;
    }

    let hero = payload.alterator.reference;
    let decklist = [`1 ${hero}`];
    
    for (let card in payload.cardIndexes) {
        decklist.push(`${payload.cardIndexes[card]} ${card.split("/")[2]}`);
    }
    
    document.getElementById("id_decklist").value = decklist.join("\n");
    document.getElementById("id_name").value = payload.name;
    document.getElementById("id_description").value = payload.description;
}

function setLoadingStatus() {
    let elementIds = ["official_deck_id", "load_deck", "id_name", "id_description", "id_decklist", "submit-new-deck"];
    for (let elementId of elementIds) {
        document.getElementById(elementId).disabled = true;
    }
    document.getElementById("load-icon").hidden = false;
    document.getElementById("ready-icon").hidden = true;
}

function setReadyStatus() {
    let elementIds = ["official_deck_id", "load_deck", "id_name", "id_description", "id_decklist", "submit-new-deck"];
    for (let elementId of elementIds) {
        document.getElementById(elementId).disabled = false;
    }
    document.getElementById("load-icon").hidden = true;
    document.getElementById("ready-icon").hidden = false;
}

function reportError(message) {
    document.getElementById("deck_builder_id-validation").innerText = message;
    let officialDeckElement = document.getElementById("official_deck_id");
    officialDeckElement.setCustomValidity(message);
    officialDeckElement.reportValidity();
}

document.getElementById("load_deck_form").addEventListener("submit", async (event) => {
    event.preventDefault();

    let officialDeckElement = document.getElementById("official_deck_id");

    if (officialDeckElement.value) {
        setLoadingStatus();
        let code = officialDeckElement.value.split("/").at(-1);
        await importOfficialDeck(code);
        setReadyStatus();
    } else {
        reportError(gettext("Input the Deck's ID or its URL."));
    }
});
