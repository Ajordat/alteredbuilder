
const tableRows = document.querySelectorAll(".table-clickable tbody tr");

for (const tableRow of tableRows) {
    tableRow.addEventListener("click", function () {
        window.open(this.dataset.href, "_self");
    });
}

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

function searchCards(e) {
    e.preventDefault();
    let filters = [];

    let factions = parseFilter(["Axiom", "Bravos", "Lyra", "Muna", "Ordis", "Yzmir"]);
    if (factions.length > 0) {
        filters.push("faction=" + factions.join(","));
    }

    let rarities = parseFilter(["Standard", "Draft"]);
    if (rarities.length > 0) {
        filters.push("legality=" + rarities.join(","));
    }

    let queryElement = document.getElementById("querySearch");
    if (queryElement.value != "") {
        filters.push("query=" + queryElement.value);
    }

    let url = window.location.pathname + "?" + filters.join("&");
    window.open(url, "_self");
    return false;
}

document.getElementById("filterSearchButton").addEventListener("click", searchCards);
document.getElementById("querySearchForm").addEventListener("submit", searchCards);