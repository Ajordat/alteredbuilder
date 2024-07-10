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
    clean() {
        sessionStorage.removeItem(this.storageKey);
        sessionStorage.removeItem("deckId");
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

/**
 * Returns the element that should be displayed in the tooltip when hovering a card.
 * 
 * @param {string} imageUrl 
 * @returns string
 */
function getImageElement(imageUrl) {
    return "<img src='" + imageUrl +  "'/>";
}

/**
 * Shows or hides the warning for a given row depending on the card's rarity and the quantity.
 * 
 * @param {Element} cardRow The element that contains the card row. 
 * @param {int} quantity The amount of times a Card is included in the Deck.
 */
function assertCardLimitWarning(cardRow, quantity) {
    let warningElement = cardRow.getElementsByClassName("card-warning")[0];
    if (quantity > 3 || cardRow.dataset.cardRarity === "U" && quantity != 1) {
        // The warning should appear when there's more than 3 cards or it's unique and there's
        // more than 1 copy
        warningElement.hidden = false;
    } else {
        warningElement.hidden = true;
    }
}

/**
 * Method to sort the card rows according to the Card references.
 */
function sortDeckCards() {
    function sortByReference(a, b) {
        return a.id.localeCompare(b.id);
    }
    
    let decklistElement = document.getElementById("decklist-cards");
    let cardRowElements = Array.prototype.slice.call(decklistElement.children, 0);
    cardRowElements.sort(sortByReference);
    for (let i = 0; i < cardRowElements.length; i++) {
        decklistElement.appendChild(cardRowElements[i]);
    }
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
                    assertCardLimitWarning(cardRow, change.quantity);
                } else {
                    // If the target quantity is 0 or negative, remove the row
                    cardRow.remove();
                }
            } else if (change.isHero) {
                // Check if the change is related to a hero
                let heroElement = document.getElementById("hero-name");
                let tooltip = bootstrap.Tooltip.getOrCreateInstance("#row-hero");
                if (change.quantity > 0) {
                    // Add the hero if it has a positive quantity
                    heroElement.value = change.name;
                    heroElement.dataset.cardReference = cardReference;
                    heroElement.nextElementSibling.disabled = false;
                    // heroElement.dataset.bsTitle = getImageElement(change.image);
                    tooltip.setContent({".tooltip-inner": getImageElement(change.image)});
                    tooltip.enable();
                } else if (change.quantity <= 0 && cardReference === heroElement.dataset.cardReference) {
                    // Remove the hero if it doesn't have a positive quantity and the
                    // displayed hero is the one removed
                    heroElement.value = "";
                    heroElement.dataset.cardReference = "";
                    heroElement.nextElementSibling.disabled = true;

                    tooltip.disable();
                }
            } else {
                if (change.quantity > 0) {
                    // Create the card row if it's a positive quantity
                    cardRow = createCardRow(change.quantity, cardReference, change.name, change.rarity, change.image);
                    assertCardLimitWarning(cardRow, change.quantity);
                }
            }
        }
        sortDeckCards();
    }
}


// Dropdown to select a deck
document.getElementById("deckSelector").addEventListener("change", (e) => {
    e.preventDefault();
    let targetDeckId = e.target.value;

    // Clean the changes on the current deck
    decklistChanges.clean();
    // Delete the existing `deck` argument
    let params = new URLSearchParams(window.location.search);
    params.delete("deck");

    if (targetDeckId != 0) {
        // If it's not a new deck, add the `deck` argument to the URI
        params.append("deck", targetDeckId);
    }
    let url = window.location.pathname + "?" + params.toString();
    // Go to the new URL
    window.open(url, "_self");

    return false;
});


/**
 * Function to decrease the card quantity on the sidebar after pressing the decrease
 * button.
 * 
 * @param {Event} event Event that triggered this function
 */
function decreaseCardQuantity(event) {
    // Retrieve the card reference and calculate the new quantity
    let quantityElement = event.currentTarget.nextElementSibling;
    let cardReference = quantityElement.dataset.cardReference;
    let quantity = Number(quantityElement.innerText) - 1;
    
    let rowId = getRowId(cardReference);
    let cardRowElement = document.getElementById(rowId);

    if (quantity > 0) {
        // If the quantity is still positive, update the value
        quantityElement.innerText = quantity;
        assertCardLimitWarning(cardRowElement, quantity);
    } else {
        // If the quantity reaches 0, remove the card from the deck list
        bootstrap.Tooltip.getInstance("#" + rowId).hide();
        cardRowElement.remove();
    }
    // Track the changes
    decklistChanges.addChange(cardReference, "quantity", Math.max(quantity, 0));
    decklistChanges.save();
}


/**
 * Function to increase the card quantity on the sidebar after pressing the increase
 * button.
 * 
 * @param {Event} event Event that triggered this function
 */
function increaseCardQuantity(event) {
    // Retrieve the card reference and calculate the new quantity
    let quantityElement = event.currentTarget.previousElementSibling;
    let cardReference = quantityElement.dataset.cardReference;
    let quantity = Number(quantityElement.innerText) + 1;
    // Update the value
    quantityElement.innerText = quantity;
    // Track the changes
    decklistChanges.addChange(cardReference, "quantity", quantity);
    decklistChanges.save();

    let cardRowElement = document.getElementById(getRowId(cardReference));
    assertCardLimitWarning(cardRowElement, quantity);
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

// Remove the hero from the sidebar
let removeHeroButton = document.getElementById("remove-hero");
removeHeroButton.addEventListener("click", function(event) {
    // Retrieve the relevant elements.
    let heroTextElement = event.currentTarget.previousElementSibling;
    let heroReference = heroTextElement.dataset.cardReference;

    // Empty the shown values and disable the button to delete the hero
    heroTextElement.value = "";
    heroTextElement.dataset.cardReference = "";
    event.currentTarget.disabled = true;
    // Hide and disable the tooltip showing the hero's image
    let tooltip = bootstrap.Tooltip.getInstance("#row-hero");
    tooltip.disable();
    tooltip.hide();

    // Track the changes
    if (decklistChanges.contains(heroReference)) {
        // If the change is already tracked it means that the hero had been added but
        // never saved, hence we can simply delete the record that added the hero
        decklistChanges.removeChange(heroReference);
    } else {
        // If the hero is not present in the changelist, add the hero removal action
        decklistChanges.addChange(heroReference, "quantity", 0);
        decklistChanges.addChange(heroReference, "isHero", true);
    }
    decklistChanges.save();
});

/**
 * Add a new card record to the list of cards. It works by duplicating the last
 * existing record, modifying its values and adding it into the document.
 * 
 * @param {int} quantity Quantity of the card present in the deck 
 * @param {string} reference Reference of the card  
 * @param {string} name Name of the card
 * @param {string} rarity Rarity of the card 
 * @param {string} image Image of the card
 */
function createCardRow(quantity, reference, name, rarity, image) {
    // Retrieve the relevant elements
    let editDeckColumn = document.getElementById("decklist-cards");
    let newCardElement = editDeckColumn.lastElementChild.cloneNode(true);
    // Set the new values
    newCardElement.id = getRowId(reference);
    newCardElement.dataset.cardRarity = rarity;
    newCardElement.dataset.bsTitle = getImageElement(image);
    newCardElement.getElementsByClassName("card-quantity")[0].innerText = quantity;
    newCardElement.getElementsByClassName("card-quantity")[0].dataset.cardReference = reference;
    newCardElement.getElementsByClassName("card-name")[0].innerText = name;
    newCardElement.getElementsByClassName("remove-card-btn")[0].addEventListener("click", decreaseCardQuantity);
    newCardElement.getElementsByClassName("add-card-btn")[0].addEventListener("click", increaseCardQuantity);
    newCardElement.style["background-image"] = `url(${image})`;
    // Enable the tooltip and display the new record on the document
    new bootstrap.Tooltip(newCardElement);
    newCardElement.hidden = false;
    editDeckColumn.appendChild(newCardElement);

    return newCardElement;
}

function addCardFromDisplay(event) {
    // Retrieve the information from the card pressed
    let cardReference = event.currentTarget.dataset.cardReference;
    let cardName = event.currentTarget.dataset.cardName;
    let cardType = event.currentTarget.dataset.cardType;
    let cardRarity = event.currentTarget.dataset.cardRarity;
    let cardImage = event.currentTarget.dataset.cardImage;

    if (cardType === "hero") {
        // If it's a hero and there's no hero on the deck, add it
        let heroElement = document.getElementById("hero-name");

        if (heroElement.value === "") {
            let removeHeroButton = document.getElementById("remove-hero");
            let tooltip = bootstrap.Tooltip.getOrCreateInstance("#row-hero");

            heroElement.value = cardName;
            heroElement.dataset.cardReference = cardReference;
            removeHeroButton.disabled = false;

            tooltip.setContent({".tooltip-inner": getImageElement(cardImage)});
            tooltip.enable();

            decklistChanges.addChange(cardReference, "quantity", 1);
            decklistChanges.addChange(cardReference, "isHero", true);
            decklistChanges.addChange(cardReference, "name", cardName);
            decklistChanges.addChange(cardReference, "image", cardImage);
            decklistChanges.save();
        }
        return;
    }

    // Attempt to retrieve the row of the clicked card
    let cardElement = document.getElementById(getRowId(cardReference));

    if (cardElement){
        // If the card exists, update the row's quantity value
        // decklistChanges is queried as a cache to avoid reading the document if possible
        let quantity = decklistChanges.getChange(cardReference, "quantity") || Number(cardElement.getElementsByClassName("card-quantity")[0].innerText);
        quantity += 1;

        decklistChanges.addChange(cardReference, "quantity", quantity);
        cardElement.getElementsByClassName("card-quantity")[0].innerText = quantity;
        assertCardLimitWarning(cardElement, quantity);
    } else {
        // If the card doesn't exist, create the card's row
        createCardRow(1, cardReference, cardName, cardRarity, cardImage);
        sortDeckCards();
        // Track the changes
        decklistChanges.addChange(cardReference, "quantity", 1);
        decklistChanges.addChange(cardReference, "name", cardName);
        decklistChanges.addChange(cardReference, "rarity", cardRarity);
        decklistChanges.addChange(cardReference, "image", cardImage);
    }
    decklistChanges.save();
}
// If a card display is clicked, add the card to the deck
let cardDisplayElements = document.getElementsByClassName("card-display");
Array.from(cardDisplayElements).forEach(function(element) {
    element.addEventListener("click", addCardFromDisplay);
});

// When the `save` button is pressed, send a request to the server with the changes tracked
let saveDeckButton = document.getElementById("save-deck");
saveDeckButton.addEventListener("click", function(event) {
    event.preventDefault();
    // Retrieve the deck's values and generate the URL to patch the deck
    let deckId = document.getElementById("deckSelector").value;
    let deckName = document.getElementById("deck-name").value;
    let url = window.location.pathname.slice(0, 4) + "decks/" + deckId + "/update/";

    if (!deckName) {
        displaySimpleToast(gettext("The deck must have a name"));
        return false;
    }

    // Send the POST request
    fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
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
            // If the request is successful, redirect to the new URL
            // This is useful to ensure the client is synced with the changes accepted
            // by the server.
            // It also allows to continue editing the deck if it's a new one
            let params = new URLSearchParams(window.location.search);
            params.delete("deck");
            params.append("deck", payload.data.deck);
            let url = window.location.pathname + "?" + params.toString();
            decklistChanges.clean();
            window.open(url, "_self");
        }
        return false;
    });
    return false;
});