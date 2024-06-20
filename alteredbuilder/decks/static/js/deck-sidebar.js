/**
 * Class to keep track of the changes made by editing the deck on the card list view.
 */
class DecklistChanges {
    #changes;
    constructor (storageKey) {
        this.storageKey = storageKey;
        this.#changes = {};
    }
    /**
     * Store the registered changes into the session storage.
     */
    save() {
        sessionStorage.setItem(this.storageKey, JSON.stringify(this.#changes));
    }
    /**
     * Retrieve changes from the session storage and override the current values.
     */
    load() {
        this.#changes = JSON.parse(sessionStorage.getItem(this.storageKey)) || {};
    }
    /**
     * Add a change to track.
     * 
     * @param {string} reference Reference of the card being changed
     * @param {string} key Attribute to track of the given card
     * @param {*} value Value to keep track of
     */
    addChange(reference, key, value) {
        if (!this.#changes[reference]) {
            this.#changes[reference] = {};
        }
        this.#changes[reference][key] = value;
    }
    /**
     * Returns if a card has any changes registered.
     * 
     * @param {string} reference 
     * @returns boolean
     */
    contains(reference) {
        return reference in this.#changes;
    }
    /**
     * Returns the stored attribute of a card, if it exists.
     * 
     * @param {string} reference Reference of the card
     * @param {string} key Attribute to retrieve
     * @returns {*}
     */
    getChange(reference, key) {
        if ((reference in this.#changes) && (key in this.#changes[reference])) {
            return this.#changes[reference][key];
        }
        return null;
    }
    /**
     * Remove the stored content of a card.
     * 
     * @param {string} reference Reference of the card to remove
     */
    removeChange(reference) {
        delete this.#changes[reference];
    }
    /**
     * Returns if there are any changes being tracked.
     * 
     * @returns boolean
     */
    hasChanges() {
        return !!this.#changes;
    }
    /**
     * Returns the tracked changes in the format that the server accepts.
     * 
     * @returns {*}
     */
    toFormData() {
        let data = {};
        for (let [reference, obj] of Object.entries(this.#changes)) {
            data[reference] = obj.quantity;
        }
        return data;
    }
    /**
     * Returns the tracked changes.
     */
    get changes() {
        return Object.entries(this.#changes);
    }
}

/**
 * Returns the expected ID of the HTMLelement containing the card.
 *  
 * @param {string} cardReference The card to retrieve the HTMLelement for
 * @returns string
 */
function getRowId(cardReference) {
    return "row-" + cardReference;
}

// Declare the variables to track the changes
var decklistChanges = new DecklistChanges("decklistChanges");
var deckId = document.getElementById("deckSelector").value;


if (deckId !== sessionStorage.getItem("deckId")) {
    // If the stored deck ID is different than the deck editing, discard the tracked changes
    sessionStorage.removeItem("decklistChanges");
    sessionStorage.setItem("deckId", deckId);
} else {
    // Attempt to load any previous changes
    decklistChanges.load();
    if (decklistChanges.hasChanges()) {
        // If there are previous changes, apply them so that they are reflected in the sidebar
        for (let [cardReference, change] of decklistChanges.changes) {
            let cardRow = document.getElementById(getRowId(cardReference));
            // Check if the row exists
            if (cardRow) {
                if (change.quantity > 0) {
                    // If the target quantity is positive, set the right quantity to the row
                    cardRow.getElementsByClassName("card-quantity")[0].innerText = change.quantity;
                } else {
                    // If the target quantity is 0 or negative, remove the row
                    cardRow.remove();
                }
            } else if (change.isHero) {
                let heroElement = document.getElementById("hero-name");
                if (change.quantity > 0) {
                    heroElement.value = change.name;
                    heroElement.dataset.cardReference = cardReference;
                    heroElement.nextElementSibling.disabled = false;
                } else if (change.quantity == 0 && cardReference === heroElement.dataset.cardReference) {
                    heroElement.value = "";
                    heroElement.dataset.cardReference = "";
                    heroElement.nextElementSibling.disabled = true;
                }
            } else {
                if (change.quantity > 0) {
                    createCardRow(change.quantity, cardReference, change.name);
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
    decklistChanges.addChange(cardReference, "quantity", Math.max(quantity, 0));
    decklistChanges.save();
}

// Increase the quantity of the card
function increaseCardQuantity(event) {
    let quantityElement = event.currentTarget.previousElementSibling;
    let cardReference = quantityElement.dataset.cardReference;
    let quantity = Number(quantityElement.innerText) + 1;

    quantityElement.innerText = quantity;
    decklistChanges.addChange(cardReference, "quantity", quantity);
    decklistChanges.save();
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

    if (decklistChanges.contains(heroReference)) {
        decklistChanges.removeChange(heroReference);
    } else {
        decklistChanges.addChange(heroReference, "quantity", 0);
        decklistChanges.addChange(heroReference, "isHero", true);
    }
    decklistChanges.save();
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
                decklistChanges.addChange(cardReference, "quantity", 1);
                decklistChanges.addChange(cardReference, "isHero", true);
                decklistChanges.addChange(cardReference, "name", cardName);
                decklistChanges.save();
            }
            return;
        }

        let cardElement = document.getElementById(getRowId(cardReference));

        if (cardElement){
            let quantity = decklistChanges.getChange(cardReference, "quantity") || Number(cardElement.getElementsByClassName("card-quantity")[0].innerText);

            decklistChanges.addChange(cardReference, "quantity", quantity + 1);
            cardElement.getElementsByClassName("card-quantity")[0].innerText = decklistChanges.getChange(cardReference, "quantity");

        } else {
            createCardRow(1, cardReference, cardName);
            decklistChanges.addChange(cardReference, "quantity", 1);
            decklistChanges.addChange(cardReference, "name", cardName);
        }
        decklistChanges.save();
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
            decklist: decklistChanges.toFormData(),
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