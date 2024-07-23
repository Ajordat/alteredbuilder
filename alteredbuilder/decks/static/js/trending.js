google.charts.load('current', {'packages':['corechart', 'bar']});
google.charts.setOnLoadCallback(drawCharts);


function drawCharts() {
    drawChart("faction-pie-chart", "faction-trends");
    drawChart("hero-pie-chart", "hero-trends");
    drawChart("card-pie-chart", "card-trends");
}


function drawChart(elementId, dataElementId) {
    // Draw the card type distribution in a pie chart
    let chartElement = document.getElementById(elementId);
    let dataElement = JSON.parse(document.getElementById(dataElementId).textContent);
    
    let data = google.visualization.arrayToDataTable(
        [['Faction', 'Amount']].concat(Object.entries(dataElement))
    );
    
    let options = {
        backgroundColor: "transparent",
        slices: [
            {color: "#3F9B0B"},
            {color: "#CD853F"},
        ]
    };

    if (document.documentElement.getAttribute("data-bs-theme") === "dark") {
        options["legend"] = {
            textStyle: {
                color: "white"
            }
        };
    }

    let chart = new google.visualization.PieChart(chartElement);

    chart.draw(data, options);
}
