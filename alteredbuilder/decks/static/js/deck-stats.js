// Retrieve the JSON data left on the template
var deckStats = JSON.parse(document.getElementById('deck-stats').textContent);

google.charts.load('current', {'packages':['corechart', 'bar']});
google.charts.setOnLoadCallback(drawChart);
google.charts.setOnLoadCallback(drawStats);
google.charts.setOnLoadCallback(drawManaCurve);

function drawChart() {
    // Draw the card type distribution in a pie chart

    let data = google.visualization.arrayToDataTable(
        [['Card Type', 'Amount']].concat(Object.entries(deckStats["type_distribution"]))
    );

    let options = {title: 'Card Type Distribution'};

    let chart = new google.visualization.PieChart(document.getElementById('distribution-pie-chart'));

    chart.draw(data, options);
}

function drawStats() {
    // Fill the table with the chances of drawing all card types at any given time and
    // in the initial hand
    let cardType = ["characters", "spells", "permanents"];
    let cardCount = deckStats["total_count"];
    let handSize = 6;

    cardType.forEach(function(cardType){
        let anytimeElement = document.getElementById(cardType + "-anytime-draw");
        let initialElement = document.getElementById(cardType + "-initial-draw");
        let cardTypeCount = deckStats["type_distribution"][cardType];
        
        let individualDraw = cardTypeCount / cardCount;

        let handNumerator = 1;
        let handDenominator = 1;
        if (cardCount > handSize) {
            // Hypergeometric distribution
            for(let i = cardCount-cardTypeCount-handSize+1; i < cardCount-handSize+1; i++){handNumerator*=i;};
            for(let i = cardCount-cardTypeCount+1; i < cardCount+1; i++){handDenominator*=i;};
            handDraw = 1 - handNumerator / handDenominator;
        } else {
            handDraw = cardTypeCount > 0;
        }

        anytimeElement.innerText = (individualDraw * 100).toFixed(2) + "%";
        initialElement.innerText = (handDraw * 100).toFixed(2) + "%";
    });
}

function drawManaCurve() {
    // Draw the vertical bars plot that depicts the mana curve

    let data = [['Cost', 'Hand', 'Reserve']];
    let handCosts = deckStats["mana_distribution"]["hand"];
    let recallCosts = deckStats["mana_distribution"]["recall"];
    for (let cost = 1; cost < 8; cost++) {
        let costRow = [cost.toString(), handCosts[cost] || 0, recallCosts[cost] || 0];
        data.push(costRow);
    }
    data = google.visualization.arrayToDataTable(data);

    var options = {
        chart: {
            title: 'Mana curve',
        },
        bars: 'vertical'
    };

    let chart = new google.charts.Bar(document.getElementById('mana-curve-chart'));
    chart.draw(data, google.charts.Bar.convertOptions(options));
}