
document.getElementById("recommenderModalTrigger").addEventListener("click", fetchRecommendations);

async function fetchRecommendations() {
    try {
        displayRecommenderStatus("recommenderLoading");
        const deckData = gatherDeckData();
        if (!deckData || Object.keys(deckData).length === 0) {
            displayRecommenderStatus("recommenderMissingCards");
            return;
        }

        const recommenderUrl = window.location.pathname.slice(0, 4) + "recommender/next-card/";
        const response = await fetch(recommenderUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify(deckData)
        });

        if (!response.ok) {
            const failedResponse = await response.json();
            if (failedResponse.human_readable) {
                displayRecommenderError(failedResponse.error);
                return;
            }
            throw new Error(`API error: ${response.statusText}`);
        }

        const recommendations = await response.json();
        displayRecommendations(recommendations);
    } catch (error) {
        console.error("Error fetching recommendations:", error);
        displayRecommenderError("Unable to retrieve a recommendation. Try it again later.");
    }
}

function gatherDeckData() {
    const heroElement = document.getElementById("hero-name");
    if (!heroElement) {
        return null;
    }
    let hero = heroElement.dataset.cardReference;
    if (!hero) {
        return null;
    }

    const decklistElements = document.querySelectorAll("#decklist-cards .row:not(#row-empty) .card-quantity");
    let decklist = {};
    for (let card of decklistElements) {
        decklist[card.dataset.cardReference] = parseInt(card.innerText);
    }

    return {
        "faction": hero.split("_")[3],
        "hero": hero,
        "decklist": decklist
    };
}

function displayRecommendations(recommendations) {
    console.log("Recommended cards:", recommendations);

    const container = document.getElementById("recommenderResults");
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }
    if (recommendations["recommended_cards"].length == 0) {
        displayRecommenderError("Add more cards to receive a recommendation!");
        return;
    }

    recommendations["recommended_cards"].forEach(card => {
        const cardElement = document.createElement("div");
        cardElement.classList.add("card-display", "click-animation", "rounded-3", "px-0", "mx-2")
        cardElement.dataset.cardReference = card.reference;
        cardElement.dataset.cardName = card.name;
        cardElement.dataset.cardType = card.type;
        cardElement.dataset.cardRarity = card.rarity;
        cardElement.dataset.cardImage = card.image;
        cardElement.style.position = "relative";

        cardElement.innerHTML = `<img src="${card.image}" class="card-img-top rounded-3" alt="${card.name}">`;
        cardElement.addEventListener("click", addCardFromDisplay);

        container.appendChild(cardElement);
    });
    displayRecommenderStatus("recommenderResults");
}

function displayRecommenderStatus(elementId) {
    const elements = document.getElementById("recommenderModal").querySelectorAll(`.status-report:not(#${elementId})`);
    for (let statusReport of elements) {
        statusReport.classList.add("d-none");
    }
    document.getElementById(elementId).classList.remove("d-none");
}
function displayRecommenderError(msg) {
    document.getElementById("recommenderError").querySelector(".status-message").innerText = msg;
    displayRecommenderStatus("recommenderError");
}