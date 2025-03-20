// When a card's row is hovered, change the card display to show the hovered card
let deckRows = document.querySelectorAll(".card-hover");
function displayCard(event) {
    let element = event.currentTarget;
    // Change the display image to show the current (or last) card hovered
    if (element.dataset.imageUrl !== undefined) {
        document.getElementById("card-showcase").src = element.dataset.imageUrl;
    }
}
deckRows.forEach(function(element) {
    element.addEventListener("mouseover", displayCard);
    element.addEventListener("click", displayCard);
});

// Functionality to save the link of a deck into the clipboard 
let copyLinkElement = document.getElementById("copy-self-link");
copyLinkElement.addEventListener("click", function() {
    // Retrieve self-link and write it into the clipboard
    navigator.clipboard.writeText(window.location.href);

    // Initialize toaster and show it
    displaySimpleToast(gettext("Link copied into clipboard!"));

    // Return false to avoid redirection
    return false;
});

// Functionality to save the decklist of a deck into the clipboard
let copyDecklistElement = document.getElementById("copy-decklist");
copyDecklistElement.addEventListener("click", function() {
    // Retrieve self-link and write it into the clipboard
    let decklistElement = document.getElementById("decklist-text");
    navigator.clipboard.writeText(decklistElement.dataset.decklist);

    // Initialize toaster and show it
    displaySimpleToast(gettext("Decklist copied into clipboard!"));

    // Return false to avoid redirection
    return false;
});

// Functionality to download a QR with a link of the deck
let downloadQRElement = document.getElementById("download-qr-svg");
if (downloadQRElement) {
    downloadQRElement.addEventListener("click", () => {
        html2canvas(document.getElementById("deck-qr-code")).then(canvas => {
            Canvas2Image.saveAsPNG(canvas, canvas.width, canvas.height, "deck-qr");
            // Initialize toaster and show it
            displaySimpleToast(gettext("QR downloaded!"));
        });
    
        // Return false to avoid redirection
        return false;
    });
}

// Functionality to save a QR with a link of the deck into the clipboard
let copyQRElement = document.getElementById("copy-qr-svg");
if (copyQRElement) {
    copyQRElement.addEventListener("click", () => {
        html2canvas(document.getElementById("deck-qr-code")).then(canvas => {
            canvas.toBlob((blob) => {
                let item = new ClipboardItem({"image/png": blob});
                navigator.clipboard.write([item]);
                // Initialize toaster and show it
                displaySimpleToast(gettext("QR copied into clipboard!"));
            });
        });

        // Return false to avoid redirection
        return false;
    });
}

// Functionality to remove all copies of a Card from the deck
let removeCardEls = document.getElementsByClassName("remove-card-trigger");
for (let element of removeCardEls) {
    
    element.addEventListener("click", (event) => {
        event.preventDefault();
        let url = window.location.pathname + "update/";
    
        cardReference = element.dataset.cardReference;
        ajaxRequest(url, {
            action: "delete",
            card_reference: cardReference
        })
        .then(response => response.json())
        .then(payload => {
            if ("error" in payload) {
                console.log("Unable to delete card:");
                console.log(payload);
                if (payload.error.code == 400) {
                    displaySimpleToast(gettext("Unable to delete card from deck"));
                } else {
                    displaySimpleToast(payload.error.message);
                }
            } else {
                location.reload();
            }
            return false;
        });
        return false;
    });
};

// Functionality to save the reference of a Card into to clipboard
let copyReferenceEls = document.getElementsByClassName("card-reference-container");
for (let element of copyReferenceEls) {
    element.addEventListener("click", (event) => {
        event.preventDefault();
        // Retrieve the card link from the container and write it into the clipboard
        navigator.clipboard.writeText(event.target.dataset.cardReference);
    
        // Initialize toaster and show it
        displaySimpleToast(gettext("Card reference copied into clipboard!"));
    
        // Return false to avoid redirection
        return false;
    });
};

// Functionality to request a private link for a Deck and save it into the clipboard
let createPrivateLink = document.getElementById("create-private-link");
if (createPrivateLink) {
    createPrivateLink.addEventListener("click", (event) => {
        event.preventDefault();
        let url = window.location.origin + window.location.pathname + "privatelink/";
    
        ajaxRequest(url)
        .then(response => response.json())
        .then(payload => {
            if ("error" in payload) {
                if (payload.error.code == 400) {
                    displaySimpleToast(gettext("Cannot create a private link"));
                } else {
                    displaySimpleToast(payload.error.message);
                }
            } else {
                let url = window.location.origin + payload["data"]["link"]
                navigator.clipboard.writeText(url);
            
                // Initialize toaster and show it
                displaySimpleToast(gettext("Link copied into clipboard!"));
            }
            return false;
        });
        return false;
    });
}

// Functionality to upvote/downvote a Comment on the comments section
let upvoteCommentsEls = document.getElementsByClassName("upvote-comment");
for (let element of upvoteCommentsEls) {
    
    element.addEventListener("click", (event) => {
        event.preventDefault();
        let url = element.pathname;
    
        ajaxRequest(url)
        .then(response => response.json())
        .then(payload => {
            if ("error" in payload) {
                console.log("Unable to upvote comment:");
                console.log(payload);
                if (payload.error.code == 400) {
                    displaySimpleToast(gettext("Unable to upvote the comment"));
                } else {
                    displaySimpleToast(payload.error.message);
                }
            } else {
                let voteCountEl = element.getElementsByClassName("comment-count")[0];
                if ("created" in payload.data && payload.data["created"]) {
                    voteCountEl.innerText = Number(voteCountEl.innerText) + 1;
                    // change class
                    element.classList.remove("btn-outline");
                } else if ("deleted" in payload.data && payload.data["deleted"]) {
                    voteCountEl.innerText = Number(voteCountEl.innerText) - 1;
                    element.classList.add("btn-outline");
                }
            }
            return false;
        });
        return false;
    });
};

// Functionality to delete a Comment on the comments section
let deleteCommentsEls = document.getElementsByClassName("delete-comment");
for (let element of deleteCommentsEls) {
    
    element.addEventListener("click", (event) => {
        event.preventDefault();

        let url = element.pathname;
    
        ajaxRequest(url)
        .then(response => response.json())
        .then(payload => {
            if ("error" in payload) {
                console.log("Unable to delete comment:");
                console.log(payload);
                if (payload.error.code == 400) {
                    displaySimpleToast(gettext("Unable to delete the comment"));
                } else {
                    displaySimpleToast(payload.error.message);
                }
            } else {
                if ("deleted" in payload.data && payload.data["deleted"]) {
                    document.querySelectorAll(`.comment-body:has(a[href='${url}'])`)[0].remove();
                    let commentCount = Number(document.getElementById("comment-count-total").innerText);
                    document.getElementById("comment-count-total").innerText = commentCount - 1;
                }
            }
            return false;
        });
        return false;
    });
};

// Functionality to un-select radio buttons for playstyle selection
let primaryTagSelectors = document.getElementsByClassName("primary-tag-selector");
for (let element of primaryTagSelectors) {
    element.addEventListener("click", (event) => {
        event.preventDefault();

        let radioInput = element.getElementsByClassName("form-check-input")[0];

        if (radioInput.checked) {
            element.getElementsByClassName("form-check-label")[0].classList.remove("active");
        }
        radioInput.checked = !radioInput.checked;
    });
}

function disableCheckboxes(element) {
    let notSelectedTags = element.querySelectorAll(".secondary-tag-selector .form-check-input:not(:checked)");
    for (let tag of notSelectedTags) {
        tag.disabled = true;
    }
}

function enableCheckboxes(element) {
    let disabledTags = element.querySelectorAll(".secondary-tag-selector .form-check-input:disabled");
    for (let tag of disabledTags) {
        tag.disabled = false;
    }
}

function countCheckedCheckboxes(element) {
    return element.querySelectorAll(".secondary-tag-selector .form-check-input:checked").length
}

// Functionality to limit the amount of checkbox selected as secondary tags
let secondaryTagSelectors = document.getElementsByClassName("secondary-tag-selector");
for (let element of secondaryTagSelectors) {
    element.addEventListener("click", (event) => {
        event.preventDefault();

        let parentElement = element.parentElement;

        let checkbox = element.getElementsByClassName("form-check-input")[0];
        let checkedTagsCount = countCheckedCheckboxes(parentElement);

        if (checkbox.checked) {
            checkbox.checked = false;
            if (checkedTagsCount == 2) {
                enableCheckboxes(parentElement);
            }
        } else {
            if (checkedTagsCount == 0) {
                checkbox.checked = true;
            } else if (checkedTagsCount == 1) {
                checkbox.checked = true;
                disableCheckboxes(parentElement);
            }
        }
    });
}
let checkedTagsCount = countCheckedCheckboxes(document);
if (checkedTagsCount >= 2) {
    disableCheckboxes(document);
}


let deckShowcaseButton = document.getElementById("deckShowcaseButton");
if (deckShowcaseButton) {
    deckShowcaseButton.addEventListener("click", (event) => {
        event.preventDefault();
        let showcaseEndpoint = "https://sabotageafter.rest/d/";
        let decklistElement = document.getElementById("decklist-text");
        let deckName = document.getElementById("deckName").innerText;
        let encodedList = deckfmt.encodeList(decklistElement.dataset.decklist);
        
        window.open(showcaseEndpoint + encodedList + "?name=" + encodeURIComponent(deckName), "_blank").focus();
        return false;
    });
}


const displayStoreKey = "deckDisplayPreference";
const DISPLAY_MODE_TABLE = "table";
const DISPLAY_MODE_CARD = "card";
const DEFAULT_DISPLAY_MODE = DISPLAY_MODE_CARD;

function storeDisplayMode(displayMode) {
    localStorage.setItem(displayStoreKey, displayMode);
}
function getDisplayMode() {
    let displayMode = localStorage.getItem(displayStoreKey);
    if (displayMode) return displayMode;
    storeDisplayMode(DEFAULT_DISPLAY_MODE);
    return DEFAULT_DISPLAY_MODE;
}

function changeDisplayElements(elementsToHideClass, elementsToShowClass) {
    let cardDisplayElements = document.getElementsByClassName(elementsToHideClass);
    for (let element of cardDisplayElements) {
        element.classList.add("d-none");
    }
    let cardTableElements = document.getElementsByClassName(elementsToShowClass);
    for (let element of cardTableElements) {
        element.classList.remove("d-none");
    }
}

function changeDisplay(displayMode) {
    switch (displayMode) {
        case DISPLAY_MODE_TABLE:
            changeDisplayElements("card-display-view", "card-table-view");
            changeToTableDisplayButton.classList.add("selected");
            changeToCardDisplayButton.classList.remove("selected");
            break;
        case DISPLAY_MODE_CARD:
            changeDisplayElements("card-table-view", "card-display-view");
            changeToCardDisplayButton.classList.add("selected");
            changeToTableDisplayButton.classList.remove("selected");
            break;
    }
}

let changeToTableDisplayButton = document.getElementById("changeToTableDisplay");
if (changeToTableDisplayButton) {
    changeToTableDisplayButton.addEventListener("click", () => {
        changeDisplay(DISPLAY_MODE_TABLE);
        storeDisplayMode(DISPLAY_MODE_TABLE);
    });
}

let changeToCardDisplayButton = document.getElementById("changeToCardDisplay");
if (changeToCardDisplayButton) {
    changeToCardDisplayButton.addEventListener("click", () => {
        changeDisplay(DISPLAY_MODE_CARD);
        storeDisplayMode(DISPLAY_MODE_CARD);
    });
}

changeDisplay(getDisplayMode());


function startCollection() {

    let collection = fetchCollection();

    console.log(collection);

    if (!collection) {
        return;
    }

    let settings = fetchSettings();

    markCollectedCards(collection, settings);
}

function markCollectedCards(collection, settings) {

    if (Object.entries(collection).length === 0) {
        return;
    }

    const cards = document.querySelectorAll(".card-table tr[data-card-reference]");
    var finalCollection = {};
    var familyCollection = {};

    if (settings.mergeSets) {
        for (let [reference, quantity] of Object.entries(collection)) {
            let cardFamily = reference.split("_").slice(3, 6).join("_");
            if (!cardFamily.includes("_U")) {
                familyCollection[cardFamily] = quantity + (familyCollection[cardFamily] || 0);
            } else {
                finalCollection[reference] = 1;
            }
        }
    } else {
        finalCollection = { ...collection };
    }

    for (let card of cards) {
        const cardReference = card.getAttribute('data-card-reference');

        if (finalCollection[cardReference]) {
            setCardCount(card, finalCollection[cardReference]);
            continue;
        }
        const cardFamily = card.getAttribute('data-card-family');

        if (familyCollection[cardFamily]) {
            setCardCount(card, familyCollection[cardFamily]);
            continue;
        }
        setCardCount(card, 0);
    }
    
    const tableTitles = document.querySelectorAll(".card-table .quantity-title");
    for (let table of tableTitles) {
        table.innerHTML += ' <small>/<i class="fa-regular fa-folder-open" style="margin-left: 3px"></i></small>'
    }
}

function setCardCount(parentElement, count) {
    // const badge = document.createElement('td');
    // badge.textContent = count;
    // badge.className = 'card-badge px-2 py-1 border border-white';

    // parentElement.style.position = 'relative';
    const cell = parentElement.querySelector(".quantity");
    let quantity = parseInt(cell.innerText);
    if (quantity > count) {
        cell.innerHTML = cell.innerHTML + ` <small style="color: #808080">/<span style="margin-left: 1px">${count}</span></small>`;
    }
}

startCollection();