// Retrieve all the rows of the tables containing cards
let deckRows = document.querySelectorAll(".card-table tbody tr")

deckRows.forEach(function(element) {
    element.addEventListener("mouseover", function() {
        // Change the display image to show the current (or last) card hovered
        if (element.dataset.imageUrl !== undefined) {
            document.getElementById("card-showcase").src = element.dataset.imageUrl;
        }
    });
});

let copyLinkElement = document.getElementById("copy-self-link");
copyLinkElement.onclick = function() {
    // Retrieve self-link and write it into the clipboard
    navigator.clipboard.writeText(window.location.href);

    // Initialize toaster and show it
    displaySimpleToast("Link copied into clipboard!");

    // Return false to avoid redirection
    return false;
}

let copyDecklistElement = document.getElementById("copy-decklist");
copyDecklistElement.onclick = function() {
    // Retrieve self-link and write it into the clipboard
    let decklistElement = document.getElementById("decklist-text");
    navigator.clipboard.writeText(decklistElement.dataset.decklist);

    // Initialize toaster and show it
    displaySimpleToast("Decklist copied into clipboard!");

    // Return false to avoid redirection
    return false;
}

let removeCardEls = document.getElementsByClassName("remove-card-trigger");

for (let element of removeCardEls) {
    
    element.addEventListener("click", (event) => {
        event.preventDefault();
        let url = window.location.origin + window.location.pathname + "update/";
    
        cardReference = element.getAttribute('data-card-reference');

        fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                action: "delete",
                card_reference: cardReference
            })
        })
        .then(response => response.json())
        .then(payload => {
            if ("error" in payload) {
                console.log("Unable to delete card:");
                console.log(payload);
                if (payload.error.code == 400) {
                    displaySimpleToast("Unable to delete card from deck");
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


