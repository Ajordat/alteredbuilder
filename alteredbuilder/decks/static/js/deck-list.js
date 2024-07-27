// Retrieve the table rows to make them clickable to open the Deck's detail
const tableRows = document.querySelectorAll(".table-clickable tbody tr");

function openDeck(event) {
    window.open(this.dataset.href, "_self");
}
for (const tableRow of tableRows) {
    tableRow.addEventListener("click", openDeck);
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
        if (labelElement.checked) {
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
 */
function searchCards(e) {
    e.preventDefault();
    let params = new URLSearchParams();

    // Retrieve the FACTION filters
    let factions = parseFilter(["Axiom", "Bravos", "Lyra", "Muna", "Ordis", "Yzmir"]);
    if (factions.length > 0) {
        params.append("faction", factions.join(","));
    }

    // Retrieve the LEGALITY filters
    let legality = parseFilter(["Standard", "ExAlts", "Draft"]);
    if (legality.length > 0) {
        params.append("legality", legality.join(","));
    }

    // Retrieve the OTHER filters
    let other = parseFilter(["Loved"]);
    if (other.length > 0) {
        params.append("other", other.join(","));
    }

    // Retrieve the QUERY from the search input
    let queryElement = document.getElementById("querySearch");
    if (queryElement.value != "") {
        params.append("query", queryElement.value);
    }

    // Go to the built URL
    let url = window.location.pathname + "?" + params.toString();
    window.open(url, "_self");
    return false;
}

let element = document.getElementById("filterSearchButton");
if (element) element.addEventListener("click", searchCards);
element = document.getElementById("querySearchForm");
if (element) element.addEventListener("submit", searchCards);