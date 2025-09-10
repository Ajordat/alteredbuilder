// Modal to add a Card to a Deck
let cardModal = document.getElementById('add-card-modal');

if (cardModal) {
    cardModal.addEventListener('show.bs.modal', event => {
        // When the modal is to be shown, file its fields with the Card's data
        let button = event.relatedTarget;
        let cardNameElement = document.getElementById("modal-card-name");
        let cardReferenceElement = document.getElementById("modal-card-reference");

        cardNameElement.value = button.getAttribute('data-bs-name');
        cardReferenceElement.value = button.getAttribute('data-bs-reference');
    });
}

/**
 * Receive a list of labels (where each points to a checkbox input) and return a list of
 * values for each one that is checked.
 * 
 * @param {string[]} labels List of labels
 * @returns {string[]} List of values for the checked elements.
 */
function parseFilter(labels) {
    let filter = [];

    for (let label of labels) {
        let labelElement = document.getElementById("filter" + label);
        if (!!labelElement && labelElement.checked) {
          filter.push(labelElement.value);
        }
    }
    return filter;
}

/**
 * Retrieve the checked checkboxes, build the filters into the GET parameters and query
 * the server.
 * 
 * @param {HTMLElement} e Element that triggered the event.
 * @returns 
 */
function searchCards(e) {
    e.preventDefault();
    let params = new URLSearchParams();

    let currentParams = new URLSearchParams(window.location.search);
    if (currentParams.has("order")) {
        params.append("order", currentParams.get("order"));
    }

    // Retrieve the FACTION filters
    let factions = parseFilter(["Axiom", "Bravos", "Lyra", "Muna", "Ordis", "Yzmir"]);
    if (factions.length > 0) {
        params.append("faction", factions.join(","));
    }

    // Retrieve the RARITY filters
    let rarities = parseFilter(["Common", "Rare", "Unique"]);
    if (rarities.length > 0) {
        params.append("rarity", rarities.join(","));
    }

    // Retrieve the TYPE filters
    let types = parseFilter(["Character", "Hero", "Landmark Permanent", "Expedition Permanent", "Spell"]);
    if (types.length > 0) {
        params.append("type", types.join(","));
    }

    // Retrieve the SET filters
    let sets = parseFilter(["BTG", "BTG-KS", "TBF", "WFM", "SKY"]);
    if (sets.length > 0) {
        params.append("set", sets.join(","));
    }

    // Retrieve the OTHER filters
    let other = parseFilter(["Promo", "AltArt", "Owned"]);
    if (other.length > 0) {
        params.append("other", other.join(","));
    }

    // Retrieve the QUERY from the search input
    let queryElement = document.getElementById("querySearch");
    if (queryElement.value != "") {
        params.append("query", queryElement.value);
    }

    let deckId = (new URLSearchParams(window.location.search)).get("deck");
    if (deckId) {
        params.append("deck", deckId);
    }

    // Go to the built URL
    let url = window.location.pathname + "?" + params.toString();
    window.open(url, "_self");
    return false;
}

document.getElementById("filterSearchButton").addEventListener("click", searchCards);
document.getElementById("querySearchForm").addEventListener("submit", searchCards);
document.getElementById("filterOrdering").addEventListener("change", searchCards);