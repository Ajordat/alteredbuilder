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