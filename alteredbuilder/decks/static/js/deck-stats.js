var deckStats = JSON.parse(document.getElementById('deck-stats').textContent);

google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);
google.charts.setOnLoadCallback(drawStats);

function drawChart() {

    let data = google.visualization.arrayToDataTable(
        [['Task', 'Hours per Day']].concat(Object.entries(deckStats["distribution"]))
    );

    let options = {
        title: 'Card Type Distribution'
    };

    let chart = new google.visualization.PieChart(document.getElementById('distribution-pie-chart'));

    chart.draw(data, options);
}

function drawStats() {
    let cardType = ["characters", "spells", "landmarks"];
    let cardCount = deckStats["total_count"];
    let handSize = 6;

    cardType.forEach(function(cardType){
        let anytimeElement = document.getElementById(cardType + "-anytime-draw");
        let initialElement = document.getElementById(cardType + "-initial-draw");
        let cardTypeCount = deckStats["distribution"][cardType];
        
        let individualDraw = cardTypeCount / cardCount;

        let handNumerator = 1;
        let handDenominator = 1;
        for(let i = cardCount-cardTypeCount-handSize+1; i < cardCount-handSize+1; i++){handNumerator*=i;};
        for(let i = cardCount-cardTypeCount+1; i < cardCount+1; i++){handDenominator*=i;};

        anytimeElement.innerText = (individualDraw * 100).toFixed(2) + "%";
        initialElement.innerText = ((1 - handNumerator / handDenominator) * 100).toFixed(2) + "%";
    });
}