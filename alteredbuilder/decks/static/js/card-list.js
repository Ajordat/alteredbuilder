let cardModal = document.getElementById('add-card-modal');

if (cardModal) {
    cardModal.addEventListener('show.bs.modal', event => {
        // Button that triggered the modal
        let button = event.relatedTarget;
        let cardNameElement = document.getElementById("modal-card-name");
        let cardReferenceElement = document.getElementById("modal-card-reference");

        cardNameElement.value = button.getAttribute('data-bs-name');
        cardReferenceElement.value = button.getAttribute('data-bs-reference');
    });
}

let searchButton = document.getElementById("filterSearchButton");

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

searchButton.onclick = function() {
    let filters = [];

    let factions = parseFilter(["Axiom", "Bravos", "Lyra", "Muna", "Ordis", "Yzmir"]);
    if (factions.length > 0) {
        filters.push("faction=" + factions.join(","));
    }

    let rarities = parseFilter(["Common", "Rare", "Unique"]);
    if (rarities.length > 0) {
        filters.push("rarity=" + rarities.join(","));
    }

    let types = parseFilter(["Character", "Hero", "Permanent", "Spell"]);
    if (types.length > 0) {
        filters.push("type=" + types.join(","));
    }

    let url = window.location.pathname + "?" + filters.join("&");
    window.location.href = url;
}