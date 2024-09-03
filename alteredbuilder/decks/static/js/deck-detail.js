// When a card's row is hovered, change the card display to show the hovered card
let deckRows = document.querySelectorAll(".card-hover");
deckRows.forEach(function(element) {
    element.addEventListener("mouseover", function() {
        // Change the display image to show the current (or last) card hovered
        if (element.dataset.imageUrl !== undefined) {
            document.getElementById("card-showcase").src = element.dataset.imageUrl;
        }
    });
});

// Functionality to save the link of a deck into the clipboard 
let copyLinkElement = document.getElementById("copy-self-link");
copyLinkElement.onclick = function() {
    // Retrieve self-link and write it into the clipboard
    navigator.clipboard.writeText(window.location.href);

    // Initialize toaster and show it
    displaySimpleToast(gettext("Link copied into clipboard!"));

    // Return false to avoid redirection
    return false;
}

// Functionality to save the decklist of a deck into the clipboard
let copyDecklistElement = document.getElementById("copy-decklist");
copyDecklistElement.onclick = function() {
    // Retrieve self-link and write it into the clipboard
    let decklistElement = document.getElementById("decklist-text");
    navigator.clipboard.writeText(decklistElement.dataset.decklist);

    // Initialize toaster and show it
    displaySimpleToast(gettext("Decklist copied into clipboard!"));

    // Return false to avoid redirection
    return false;
}

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
                    element.classList.remove("btn-outline-primary");
                    element.classList.add("btn-primary");
                } else if ("deleted" in payload.data && payload.data["deleted"]) {
                    voteCountEl.innerText = Number(voteCountEl.innerText) - 1;
                    element.classList.remove("btn-primary");
                    element.classList.add("btn-outline-primary");
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