
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
                "Content-Type": "application/json"
            },
            body: JSON.stringify(deckData)
        });

        if (!response.ok) {
            displayRecommenderError("Unable to retrieve a recommendation. Try it again later.");
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

    recommendations["recommended_cards"].forEach(card => {
        const cardElement = document.createElement("div");
        cardElement.classList.add("card-display", "click-animation", "rounded-3")
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