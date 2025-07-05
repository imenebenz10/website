// document.addEventListener('DOMContentLoaded', function () {
//     fetchData();
//     setInterval(fetchData, 5000); // Fetch new data every 5000 milliseconds (5 seconds)
// });

// function fetchData() {
//     fetch('/api/get-sensor-data')
//         .then(response => response.json())
//         .then(data => {
//             const container = document.getElementById('weather');
//             container.innerHTML = ''; // Clear previous data

//             if (data.length > 0) {
//                 const latestData = data[0]; // Assumes latest data is at the end
//                 displayData(latestData, container);
//             } else {
//                 container.textContent = 'No data available.';
//             }
//         })
//         .catch(error => {
//             console.error('Error fetching data:', error);
//             document.getElementById('weather').textContent = 'Failed to load data.';
//         });

//     fetch('/api/get-predicted-data')
//         .then(response => response.json())
//         .then(predictedData => {
//             const container = document.getElementById('predicted-weather');
//             container.innerHTML = ''; // Clear previous data

//             if (predictedData.length > 0) {
//                 const latestPredictedData = predictedData[0]; // Assumes latest predicted data is at the end
//                 displayPredictedData(latestPredictedData, container);
//             } else {
//                 container.textContent = 'No predicted data available.';
//             }
//         })
//         .catch(error => {
//             console.error('Error fetching predicted data:', error);
//             document.getElementById('predicted-weather').textContent = 'Failed to load predicted data.';
//         });
// }

// function displayData(latestData, container) {
//     const dataEntry = document.createElement('div');
//     dataEntry.className = 'sensordata';

//     const timeElem = document.createElement('div');
//     timeElem.className = 'timestamp';
//     timeElem.textContent = `Timestamp: ${latestData.timestamp}`;

//     const humidityElem = document.createElement('div');
//     humidityElem.className = 'humidity';
//     humidityElem.textContent = `Humidity: ${latestData.humidity}`;

//     const tempElem = document.createElement('div');
//     tempElem.className = 'temperature';
//     tempElem.textContent = `Temperature: ${latestData.temperature}`;

//     dataEntry.appendChild(timeElem);
//     dataEntry.appendChild(humidityElem);
//     dataEntry.appendChild(tempElem);

//     container.appendChild(dataEntry);
// }

// function displayPredictedData(latestPredictedData, container) {
//     const dataEntry = document.createElement('div');
//     dataEntry.className = 'predictdata';

//     const predTimeElem = document.createElement('div');
//     predTimeElem.className = 'predtimestamp';
//     predTimeElem.textContent = `Predicted Timestamp: ${latestPredictedData.predtimestamp}`;

//     const predHumidityElem = document.createElement('div');
//     predHumidityElem.className = 'predhumidity';
//     predHumidityElem.textContent = `Predicted Humidity: ${latestPredictedData.predhumidity}`;

//     const predTempElem = document.createElement('div');
//     predTempElem.className = 'predtemperature';
//     predTempElem.textContent = `Predicted Temperature: ${latestPredictedData.predtemperature}`;

//     dataEntry.appendChild(predTimeElem);
//     dataEntry.appendChild(predHumidityElem);
//     dataEntry.appendChild(predTempElem);

//     container.appendChild(dataEntry);
// }



// fetchSoilData.js

// fetchSoilData.js
////////////////////////////////////////////////////////////////////////////////////////

// async function fetchAndPlotSoilData() {
//   const API_KEY = 'a57be93e6b755d4f85fe6c922f3084ab';
//   const POLYGON_ID = '6818b7dbd23361542f21605b';
//   const start = Math.floor(new Date('2025-03-10').getTime() / 1000);
//   const end = Math.floor(Date.now() / 1000);

//   // Use CORS proxy (if needed)
//   const proxy = 'https://corsproxy.io/?';
//   const url = `${proxy}http://api.agromonitoring.com/agro/1.0/soil?polyid=${POLYGON_ID}&start=${start}&end=${end}&appid=${API_KEY}`;

//   try {
//     const response = await fetch(url);
//     const data = await response.json();

//     if (!Array.isArray(data) || data.length === 0) {
//       console.error('No valid soil data available');
//       return;
//     }

//     const labels = data.map(d => new Date(d.dt * 1000).toLocaleDateString());
//     const t0 = data.map(d => (d.t0 - 273.15).toFixed(2));    // Surface temp
//     const t10 = data.map(d => (d.t10 - 273.15).toFixed(2));  // Temp at 10cm
//     const moisture = data.map(d => d.moisture);              // Soil moisture

//     const ctx = document.getElementById('soilChart');
//     new Chart(ctx, {
//       type: 'line',
//       data: {
//         labels: labels,
//         datasets: [
//           {
//             label: 'Temp at surface',
//             data: t0,
//             borderColor: 'yellow',
//             backgroundColor: 'rgba(255, 255, 0, 0.1)',
//             tension: 0.4,
//             fill: false
//           },
//           {
//             label: 'Temp at depth 10cm',
//             data: t10,
//             borderColor: 'blue',
//             backgroundColor: 'rgba(0, 0, 255, 0.1)',
//             tension: 0.4,
//             fill: false
//           },
//           {
//             label: 'Soil moisture',
//             data: moisture,
//             borderColor: 'green',
//             backgroundColor: 'rgba(0, 128, 0, 0.1)',
//             tension: 0.4,
//             fill: false
//           }
//         ]
//       },
//       options: {
//         responsive: true,
//         maintainAspectRatio: false,
//         plugins: {
//           legend: { display: false }
//         },
//         scales: {
//           y: {
//             beginAtZero: false,
//             ticks: { color: '#f0f0f0' },
//             grid: { color: 'rgba(240, 240, 240, 0.1)' }
//           },
//           x: {
//             ticks: { color: '#f0f0f0' },
//             grid: { color: 'rgba(240, 240, 240, 0.1)' }
//           }
//         }
//       }
//     });

//   } catch (error) {
//     console.error('Error fetching or rendering soil data:', error);
//   }
// }

// window.addEventListener('DOMContentLoaded', fetchAndPlotSoilData);

 const POLYGON_ID = '6818b7dbd23361542f21605b';
const SOIL_API_KEY = 'a57be93e6b755d4f85fe6c922f3084ab';

async function fetchSoilData() {
    try {
        // Sample soil data with multiple dates
        const data = [
            {
                dt: 1751390400, // 2025-07-01 13:00:00
                t0: 301.244, // Surface temp (K)
                t10: 298.08, // 10cm depth temp (K)
                moisture: 0.162
            },
            {
                dt: 1751304000, // 2025-06-30 13:00:00
                t0: 299.15,
                t10: 296.22,
                moisture: 0.180
            },
            {
                dt: 1751217600, // 2025-06-29 13:00:00
                t0: 297.65,
                t10: 294.85,
                moisture: 0.195
            },
            {
                dt: 1751131200, // 2025-06-28 13:00:00
                t0: 296.48,
                t10: 293.75,
                moisture: 0.210
            }
        ];

        if (!Array.isArray(data) || data.length === 0) {
            throw new Error("No soil data available");
        }

        const labels = data.map(entry =>
            new Date(entry.dt * 1000).toLocaleDateString("en-GB", {
                day: "2-digit",
                month: "short",
                year: "numeric"
            })
        );

        const surfaceTemps = data.map(entry => (entry.t0 - 273.15).toFixed(2));
        const depthTemps = data.map(entry => (entry.t10 - 273.15).toFixed(2));
        const moisture = data.map(entry => entry.moisture);

        const ctx = document.getElementById('soilChart').getContext('2d');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Surface Temperature (°C)',
                        data: surfaceTemps,
                        borderColor: 'yellow',
                        backgroundColor: 'rgba(255, 255, 0, 0.1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Temp at 10cm Depth (°C)',
                        data: depthTemps,
                        borderColor: 'blue',
                        backgroundColor: 'rgba(0, 0, 255, 0.1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Soil Moisture (m³/m³)',
                        data: moisture,
                        borderColor: 'green',
                        backgroundColor: 'rgba(0, 128, 0, 0.1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Value'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Soil data fetch error:', error);
        const container = document.getElementById('soilChart').parentNode;
        container.innerHTML += '<div class="error">Unable to load soil data.</div>';
    }
}

document.addEventListener("DOMContentLoaded", fetchSoilData);
