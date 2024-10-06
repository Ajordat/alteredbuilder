
const factionColors = {
    "axiom": "#7e4b36",
    "bravos": "#ff1a1a",
    "lyra": "#d12358",
    "muna": "#4c7245",
    "ordis": "#00628b",
    "yzmir": "#483b66",
}

let factionStats = JSON.parse(document.getElementById('faction-distribution').textContent);
factionStats = Object.entries(factionStats).sort((a, b) => b[1] - a[1]);
let labels = factionStats.map((dataPoint) => dataPoint[0]);
let data = factionStats.map((dataPoint) => dataPoint[1]);

let pieChartElement = document.getElementById('deckPieChart');
if (pieChartElement) {
    let ctx = pieChartElement.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        plugins: [ChartDataLabels],
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: Array.from(labels, (faction) => factionColors[faction]),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                datalabels: {
                    anchor: 'center',
                    align: 'end',
                    color: "#fff",
                    formatter: (value, ctx) => {
                        let datapoints = ctx.chart.data.datasets[0].data;
                        let total = datapoints.reduce((total, datapoint) => total + datapoint, 0);
                        let percentage = value / total * 100;
                        return percentage.toFixed(2) + "%";
                    }
                }
            }
        }
    });
}