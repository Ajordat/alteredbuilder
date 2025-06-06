// Retrieve the JSON data left on the template
var deckStats = JSON.parse(document.getElementById('deck-stats').textContent);

const chartBackgroundColor = "#212529";
const chartTextColor = "white";

google.charts.load('current', { 'packages': ['corechart', 'bar'] });
google.charts.setOnLoadCallback(drawTypeChart);
google.charts.setOnLoadCallback(drawPowerChart);
google.charts.setOnLoadCallback(drawStats);
google.charts.setOnLoadCallback(drawManaCurve);

function drawTypeChart() {
    // Draw the card type distribution in a pie chart
    let chartElement = document.getElementById('distribution-pie-chart');
    let deckStatsI18n = {};
    deckStatsI18n[gettext("characters")] = deckStats["type_distribution"]["characters"];
    deckStatsI18n[gettext("spells")] = deckStats["type_distribution"]["spells"];
    deckStatsI18n[gettext("permanents")] = deckStats["type_distribution"]["permanents"];

    let data = google.visualization.arrayToDataTable(
        [['Card Type', 'Amount']].concat(Object.entries(deckStatsI18n))
    );

    let options = {
        backgroundColor: "transparent",
        chartArea: {
            left: "25%",
            top: "4%",
            width: "100%",
            height: "92%"
        },
        slices: [
            { color: "#3F9B0B" },
            { color: "#CD853F" },
            { color: "#D4A017" },
        ],
        fontName: "Gabriela"
    };

    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options["legend"] = {
            textStyle: {
                color: chartTextColor
            }
        };
    }

    let chart = new google.visualization.PieChart(chartElement);

    chart.draw(data, options);
}

function drawPowerChart() {
    // Draw the card type distribution in a pie chart
    let chartElement = document.getElementById('power-distribution-pie-chart');
    let deckStatsI18n = {};
    deckStatsI18n[gettext("forest")] = deckStats["region_distribution"]["forest"];
    deckStatsI18n[gettext("mountain")] = deckStats["region_distribution"]["mountain"];
    deckStatsI18n[gettext("ocean")] = deckStats["region_distribution"]["ocean"];

    let totalPower = Object.values(deckStatsI18n).reduce((sum, val) => sum + val, 0);
    if (totalPower == 0) {
        document.getElementById('power-distribution-container').classList.add("d-none");
    }

    let data = google.visualization.arrayToDataTable(
        [['Region', 'Power']].concat(Object.entries(deckStatsI18n))
    );

    let options = {
        backgroundColor: "transparent",
        pieSliceText: "value",
        chartArea: {
            left: "25%",
            top: "4%",
            width: "100%",
            height: "92%"
        },
        slices: [
            { color: "#91b14e" },
            { color: "#c17e51" },
            { color: "#6075a4" },
        ],
        fontName: "Gabriela"
    };

    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options["legend"] = {
            textStyle: {
                color: chartTextColor
            }
        };
    }

    let chart = new google.visualization.PieChart(chartElement);

    chart.draw(data, options);
}

function drawStats() {
    // Fill the table with the chances of drawing all card types at any given time and
    // in the initial hand
    let cardType = ["characters", "spells", "permanents"];
    let cardCount = deckStats["total_count"];
    let handSize = 6;

    cardType.forEach(function (cardType) {
        let anytimeElement = document.getElementById(cardType + "-anytime-draw");
        let initialElement = document.getElementById(cardType + "-initial-draw");
        let cardTypeCount = deckStats["type_distribution"][cardType];

        if (cardTypeCount == 0) {
            anytimeElement.innerText = "0%";
            initialElement.innerText = "0%";
            return;
        }

        let individualDraw = cardTypeCount / cardCount;

        let handNumerator = 1;
        let handDenominator = 1;
        if (cardCount > handSize) {
            // Hypergeometric distribution
            for (let i = cardCount - cardTypeCount - handSize + 1; i < cardCount - handSize + 1; i++) { handNumerator *= i; };
            for (let i = cardCount - cardTypeCount + 1; i < cardCount + 1; i++) { handDenominator *= i; };
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

    let maxCost = Math.max(...Object.keys(handCosts).map(x => parseInt(x)), ...Object.keys(recallCosts).map(x => parseInt(x)), 8);

    for (let cost = 1; cost < maxCost + 1; cost++) {
        let costRow = [cost.toString(), handCosts[cost] || 0, recallCosts[cost] || 0];
        data.push(costRow);
    }
    data = google.visualization.arrayToDataTable(data);

    let options = {
        bars: "vertical",
        chartArea: {
            backgroundColor: "transparent",
            left: "100%",
            top: "0%",
            width: "100%",
            height: "100%",
        },
        legend: {
            position: "top"
        },
        fontName: "Gabriela"
    };
    if (window.innerWidth < 500) {
        options["legend"]["position"] = "none";
    }
    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options = {
            ...options, ...{
                backgroundColor: "transparent",
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
            }
        };
    }

    let chart = new google.charts.Bar(document.getElementById('mana-curve-chart'));
    chart.draw(data, google.charts.Bar.convertOptions(options));
}