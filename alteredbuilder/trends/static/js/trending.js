google.charts.load('current', {'packages':['corechart', 'bar']});
google.charts.setOnLoadCallback(drawCharts);

const factionColors = {
    "AX": "#7e4b36",
    "BR": "#ff1a1a",
    "LY": "#d12358",
    "MU": "#4c7245",
    "OR": "#00628b",
    "YZ": "#483b66",
}
const heroColors = {
    "AX": ["#7e4b36", "#a16045", "#ba7a5e"],
    "BR": ["#ff1a1a", "#ff4d4d", "#ff8080"],
    "LY": ["#d12358", "#de3b6c", "#e5668c"],
    "MU": ["#4c7245", "#5f8f56", "#78a970"],
    "OR": ["#00628b", "#007db3", "#00a1e6"],
    "YZ": ["#483b66", "#5b4a82", "#725da2"],
};

function drawCharts() {
    drawFactionChart();
    drawHeroChart();
}

function getBaseChartOptions() {
    let options = {
        backgroundColor: "transparent",
        tooltip: {
            ignoreBounds: true,
            isHtml: true,
            text: "percentage",
            trigger: "focus"
        }
    };

    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options["legend"] = {
            textStyle: {
                color: "white"
            }
        };
    }
    return options;
}


function drawFactionChart() {
    // Draw the card type distribution in a pie chart
    let chartElement = document.getElementById("faction-pie-chart");
    let dataElement = JSON.parse(document.getElementById("faction-trends").textContent);
    
    let options = getBaseChartOptions();
    options["slices"] = [];
    for (let faction of Object.keys(dataElement)) {
        options["slices"].push({color: factionColors[faction]});
    }

    let data = google.visualization.arrayToDataTable(
        [['Faction', 'Amount']].concat(Object.entries(dataElement))
    );
    let chart = new google.visualization.PieChart(chartElement);

    chart.draw(data, options);

    let params = new URLSearchParams(document.location.search);
    if (params.get("faction")) {
        chart.setSelection([{row:0, column:null}]);
    }
    google.visualization.events.addListener(chart, "select", () => {
        let selection = chart.getSelection();
        if (selection.length == 0) {
            // Remove selection
            window.open(window.location.pathname, "_self");
            return;
        }
        let item = Object.entries(dataElement)[selection[0].row];
        let url = window.location.pathname + "?faction=" + item[0];
        window.open(url, "_self");
    })
}

function drawHeroChart() {
    // Draw the card type distribution in a pie chart
    let chartElement = document.getElementById("hero-pie-chart");
    let dataElement = JSON.parse(document.getElementById("hero-trends").textContent);
     
    let factionOccurrence = {
        "AX": 0,
        "BR": 0,
        "LY": 0,
        "MU": 0,
        "OR": 0,
        "YZ": 0,
    };
    let options = getBaseChartOptions();
    let heroData = [];
    options["slices"] = [];
    for (let k of Object.keys(dataElement)) {
        let faction = dataElement[k]["faction"];
        options["slices"].push({color: heroColors[faction][factionOccurrence[faction]]});
        factionOccurrence[faction] += 1;
        heroData.push([k, dataElement[k]["count"]]);
    }

    let data = google.visualization.arrayToDataTable(
        [['Hero', 'Amount']].concat(heroData.slice(0, 8))
    );
 
    let chart = new google.visualization.PieChart(chartElement);
 
    chart.draw(data, options);

    let params = new URLSearchParams(document.location.search);
    if (params.get("hero")) {
        chart.setSelection([{row:0, column:null}]);
    }
    google.visualization.events.addListener(chart, "select", () => {
        let selection = chart.getSelection();

        if (selection.length == 0) {
            // Remove selection
            window.open(window.location.pathname, "_self");
            return;
        }
        let item = heroData[selection[0].row];
        console.log(item)
        let url = window.location.pathname + "?hero=" + encodeURI(item[0].split(" ")[0]);
        console.log(url)
        window.open(url, "_self");
    })
}