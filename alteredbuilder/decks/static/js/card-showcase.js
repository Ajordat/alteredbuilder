
let deckRows = document.querySelectorAll(".card-table tbody tr")

deckRows.forEach(function(element) {
    element.addEventListener("mouseover", function() {
        document.getElementById("card-showcase").src = element.dataset.imageUrl;
    });
});