document.addEventListener('DOMContentLoaded', function () {
    fetchData();
    setInterval(fetchData, 5000); // Fetch new data every 5000 milliseconds (5 seconds)
});

function fetchData() {
    fetch('/api/get-sensor-data')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('weather');
            container.innerHTML = ''; // Clear previous data

            if (data.length > 0) {
                const latestData = data[0]; // Assumes latest data is at the end
                displayData(latestData, container);
            } else {
                container.textContent = 'No data available.';
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('weather').textContent = 'Failed to load data.';
        });

    fetch('/api/get-predicted-data')
        .then(response => response.json())
        .then(predictedData => {
            const container = document.getElementById('predicted-weather');
            container.innerHTML = ''; // Clear previous data

            if (predictedData.length > 0) {
                const latestPredictedData = predictedData[0]; // Assumes latest predicted data is at the end
                displayPredictedData(latestPredictedData, container);
            } else {
                container.textContent = 'No predicted data available.';
            }
        })
        .catch(error => {
            console.error('Error fetching predicted data:', error);
            document.getElementById('predicted-weather').textContent = 'Failed to load predicted data.';
        });
}

function displayData(latestData, container) {
    const dataEntry = document.createElement('div');
    dataEntry.className = 'sensordata';

    const timeElem = document.createElement('div');
    timeElem.className = 'timestamp';
    timeElem.textContent = `Timestamp: ${latestData.timestamp}`;

    const humidityElem = document.createElement('div');
    humidityElem.className = 'humidity';
    humidityElem.textContent = `Humidity: ${latestData.humidity}`;

    const tempElem = document.createElement('div');
    tempElem.className = 'temperature';
    tempElem.textContent = `Temperature: ${latestData.temperature}`;

    dataEntry.appendChild(timeElem);
    dataEntry.appendChild(humidityElem);
    dataEntry.appendChild(tempElem);

    container.appendChild(dataEntry);
}

function displayPredictedData(latestPredictedData, container) {
    const dataEntry = document.createElement('div');
    dataEntry.className = 'predictdata';

    const predTimeElem = document.createElement('div');
    predTimeElem.className = 'predtimestamp';
    predTimeElem.textContent = `Predicted Timestamp: ${latestPredictedData.predtimestamp}`;

    const predHumidityElem = document.createElement('div');
    predHumidityElem.className = 'predhumidity';
    predHumidityElem.textContent = `Predicted Humidity: ${latestPredictedData.predhumidity}`;

    const predTempElem = document.createElement('div');
    predTempElem.className = 'predtemperature';
    predTempElem.textContent = `Predicted Temperature: ${latestPredictedData.predtemperature}`;

    dataEntry.appendChild(predTimeElem);
    dataEntry.appendChild(predHumidityElem);
    dataEntry.appendChild(predTempElem);

    container.appendChild(dataEntry);
}
