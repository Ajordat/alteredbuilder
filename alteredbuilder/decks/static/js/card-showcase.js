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

function displaySimpleToast(displayText) {
    let myToastEl = document.getElementById('simple-toast');
    let myToast = bootstrap.Toast.getOrCreateInstance(myToastEl);
    let toastText = document.getElementById('toast-text');
    toastText.innerHTML = displayText;
    myToast.show();
}

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

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));