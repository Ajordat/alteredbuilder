// Retrieve the JSON data left on the template
var deckStats = JSON.parse(document.getElementById('deck-stats').textContent);

const chartBackgroundColor = "#212529";
const chartTextColor = "white";

google.charts.load('current', {'packages':['corechart', 'bar']});
google.charts.setOnLoadCallback(drawChart);
google.charts.setOnLoadCallback(drawStats);
google.charts.setOnLoadCallback(drawManaCurve);

function drawChart() {
    // Draw the card type distribution in a pie chart
    let chartElement = document.getElementById('distribution-pie-chart');
    let deckStatsI18n = {};
    deckStatsI18n[gettext("characters")] = deckStats["type_distribution"]["characters"];
    deckStatsI18n[gettext("spells")] = deckStats["type_distribution"]["spells"];
    deckStatsI18n[gettext("permanents")] = deckStats["type_distribution"]["permanents"];

    let data = google.visualization.arrayToDataTable(
        [['Card Type', 'Amount']].concat(Object.entries(deckStatsI18n))
    );
    
    let options = {};
    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options = {
            backgroundColor: chartBackgroundColor,
            legend: {
                textStyle: {
                    color: chartTextColor
                }
            }
        };
    }
    
    options["slices"] = [
        {color: "#3F9B0B"},
        {color: "#CD853F"},
        {color: "#D4A017"},
    ];

    let chart = new google.visualization.PieChart(chartElement);

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
            for(let i = cardCount - cardTypeCount - handSize + 1; i < cardCount-handSize + 1; i++){handNumerator *= i;};
            for(let i = cardCount - cardTypeCount + 1; i < cardCount + 1; i++){handDenominator *= i;};
            handDraw = 1 - handNumerator / handDenominator;
        } else {
            handDraw = cardTypeCount > 0;
        }

        anytimeElement.innerText = Math.trunc(individualDraw * 10000) / 100 + "%";
        initialElement.innerText = Math.trunc(handDraw * 10000) / 100 + "%";
    });
}

function drawManaCurve() {
    // Draw the vertical bars plot that depicts the mana curve

    let data = [[gettext('Cost'), gettext('Hand'), gettext('Reserve')]];
    let handCosts = deckStats["mana_distribution"]["hand"];
    let recallCosts = deckStats["mana_distribution"]["recall"];
    for (let cost = 1; cost < 8; cost++) {
        let costRow = [cost.toString(), handCosts[cost] || 0, recallCosts[cost] || 0];
        data.push(costRow);
    }
    data = google.visualization.arrayToDataTable(data);

    let options = {};
    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options = {
            backgroundColor: chartBackgroundColor,
            chartArea: {
                backgroundColor: chartBackgroundColor
            },
            hAxis: {
                textStyle: {
                    color: chartTextColor
                }
            },
            vAxis: {
                textStyle: {
                    color: chartTextColor
                }
            },
            legend: {
                textStyle: {
                    color: chartTextColor
                }
            }
        };
    }
    
    options["bars"] = "vertical";

    let chart = new google.charts.Bar(document.getElementById('mana-curve-chart'));
    chart.draw(data, google.charts.Bar.convertOptions(options));
}