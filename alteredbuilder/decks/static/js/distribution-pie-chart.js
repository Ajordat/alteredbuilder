var deckStats = JSON.parse(document.getElementById('deck-stats').textContent);

anychart.onDocumentReady(function () {
    // add the data
    let data = anychart.data.set(Object.entries(deckStats["distribution"]));
    // create a pie chart with the data
    let chart = anychart.pie(data);
    // set the chart title
    chart.title("Card Distribution");
    // set container id for the chart
    chart.container("distribution-pie-chart");
    // initiate chart drawing
    chart.draw();
});