
// class DecklistChanges {
//     constructor (storageKey) {
//         this.storageKey = storageKey;
//     }
//     save() {
//         sessionStorage.setItem(this.storageKey, JSON.stringify(this.changes));
//     }
//     load() {
//         this.changes = JSON.parse(sessionStorage.getItem(this.storageKey)) || {};
//     }
//     addChange(reference, key, value) {
//         if (!this.changes[reference]) {
//             this.changes[reference] = {};
//         }
//         this.changes[reference][key] = value;
//     }
// }
var decklistChanges;
// var testDecklistChanges = new DecklistChanges("decklistChanges");
var deckId = document.getElementById("deckSelector").value;

function getRowId(cardReference) {
    return "row-" + cardReference;
}

function saveDecklist() {
    sessionStorage.setItem("decklistChanges", JSON.stringify(decklistChanges));
}

function updateDecklist(reference, key, value) {
    if (!decklistChanges[reference]) {
        decklistChanges[reference] = {}
    }
    decklistChanges[reference][key] = value
}

if (deckId !== sessionStorage.getItem("deckId")) {
    sessionStorage.removeItem("decklistChanges");
    sessionStorage.setItem("deckId", deckId);
} else {
    decklistChanges = JSON.parse(sessionStorage.getItem("decklistChanges")) || {};
    if (decklistChanges) {
        for (let [cardReference, quantity] of Object.entries(decklistChanges)) {
            console.log(cardReference, quantity);
            let cardRow = document.getElementById(getRowId(cardReference));
            if (cardRow) {
                if (quantity > 0) {
                    cardRow.getElementsByClassName("card-quantity")[0].innerText = quantity;
                } else {
                    cardRow.remove();
                }
            } else {
                if (quantity > 0) {
                    createCardRow(quantity, cardReference, "test");
                }
            }
        }
    }
}


document.getElementById("deckSelector").addEventListener("change", (e) => {
    e.preventDefault();

    let params = new URLSearchParams(window.location.search);
    params.delete("deck");
    params.append("deck", e.target.value);
    let url = window.location.pathname + "?" + params.toString();
    window.open(url, "_self");

    return false;
});

// Decrease the quantity of the card
function decreaseCardQuantity(event) {
    let quantityElement = event.currentTarget.nextElementSibling;
    let cardReference = quantityElement.dataset.cardReference;
    let quantity = Number(quantityElement.innerText) - 1;
    
    if (quantity > 0) {
        quantityElement.innerText = quantity;
    } else {
        // If the quantity reaches 0, remove the card from the deck list
        event.currentTarget.parentElement.parentElement.parentElement.remove();
    }
    // decklistChanges[cardReference] = Math.max(quantity, 0);
    updateDecklist(cardReference, "quantity", Math.max(quantity, 0));
    saveDecklist();
}

// Increase the quantity of the card
function increaseCardQuantity(event) {
    let quantityElement = event.currentTarget.previousElementSibling;
    let cardReference = quantityElement.dataset.cardReference;
    let quantity = Number(quantityElement.innerText) + 1;

    quantityElement.innerText = quantity;
    updateDecklist(cardReference, "quantity", quantity);
    saveDecklist();
}

// Retrieve all the buttons to decrease the card quantity
let removeCardButtons = document.getElementsByClassName("remove-card-btn");
Array.from(removeCardButtons).forEach(function(element) {
    element.addEventListener("click", decreaseCardQuantity);
});

// Retrieve all the buttons to increase the card quantity
let addCardButtons = document.getElementsByClassName("add-card-btn");
Array.from(addCardButtons).forEach(function(element) {
    element.addEventListener("click", increaseCardQuantity);
});

let removeHeroButton = document.getElementById("remove-hero");
removeHeroButton.addEventListener("click", function(event) {
    let heroTextElement = event.currentTarget.previousElementSibling;
    let heroReference = heroTextElement.dataset.cardReference;

    heroTextElement.value = "";
    heroTextElement.dataset.cardReference = "";
    event.currentTarget.disabled = true;

    if (heroReference in decklistChanges) {
        delete decklistChanges[heroReference];
    } else {
        updateDecklist(heroReference, "quantity", 0);
        updateDecklist(heroReference, "isHero", true);
    }
    saveDecklist();
});

function createCardRow(quantity, reference, name) {
    let editDeckColumn = document.getElementById("decklist-cards");
    let newCardElement = editDeckColumn.lastElementChild.cloneNode(true);
    newCardElement.id = getRowId(reference);
    newCardElement.getElementsByClassName("card-quantity")[0].innerText = quantity;
    newCardElement.getElementsByClassName("card-quantity")[0].dataset.cardReference = reference;
    newCardElement.getElementsByClassName("card-name")[0].innerText = name;
    newCardElement.getElementsByClassName("remove-card-btn")[0].addEventListener("click", decreaseCardQuantity);
    newCardElement.getElementsByClassName("add-card-btn")[0].addEventListener("click", increaseCardQuantity);
    newCardElement.hidden = false;
    editDeckColumn.appendChild(newCardElement);
}

// Retrieve all the buttons to increase the card quantity
let cardDisplayElements = document.getElementsByClassName("card-display");
Array.from(cardDisplayElements).forEach(function(element) {
    element.addEventListener("click", function(event) {
        let cardReference = event.currentTarget.dataset.cardReference;
        let cardName = event.currentTarget.dataset.cardName;
        let cardType = event.currentTarget.dataset.cardType;
        
        if (cardType === "hero") {
            let heroElement = document.getElementById("hero-name");
            let removeHeroButton = document.getElementById("remove-hero");

            if (heroElement.value === "") {
                heroElement.value = cardName;
                heroElement.dataset.cardReference = cardReference;
                removeHeroButton.disabled = false;
                updateDecklist(cardReference, "quantity", 1);
                saveDecklist();
            }
            return;
        }

        let cardElement = document.getElementById(getRowId(cardReference));

        if (cardElement){
            let quantity = decklistChanges[cardReference] || Number(cardElement.getElementsByClassName("card-quantity")[0].innerText);

            updateDecklist(cardReference, "quantity", quantity + 1);
            cardElement.getElementsByClassName("card-quantity")[0].innerText = decklistChanges[cardReference];

        } else {
            createCardRow(1, cardReference, cardName);
            updateDecklist(cardReference, "quantity", 1);
            updateDecklist(cardReference, "name", cardName);
        }
        saveDecklist();
    });
});


let saveDeckButton = document.getElementById("save-deck");
let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
saveDeckButton.addEventListener("click", function(event) {
    event.preventDefault();
    let deckId = document.getElementById("deckSelector").value;
    let deckName = document.getElementById("deck-name").value;
    let url = window.location.pathname.slice(0, 4) + "decks/" + deckId + "/update/";

    fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({
            action: "patch",
            decklist: decklistChanges,
            name: deckName
        })
    })
    .then(response => response.json())
    .then(payload => {
        if ("error" in payload) {
            console.log("Unable to update deck:");
            console.log(payload);
            if (payload.error.code == 400) {
                displaySimpleToast(gettext("Unable to update deck"));
            } else {
                displaySimpleToast(payload.error.message);
            }
        } else {
            let params = new URLSearchParams(window.location.search);
            params.delete("deck");
            params.append("deck", payload.data.deck);
            let url = window.location.pathname + "?" + params.toString();
            sessionStorage.removeItem("decklistChanges");
            sessionStorage.removeItem("deckId");
            window.open(url, "_self");
        }
        return false;
    });
    return false;
});