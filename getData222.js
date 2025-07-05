const API_KEY = 'a57be93e6b755d4f85fe6c922f3084ab';
const POLYGON_ID = '6818b7dbd23361542f21605b';
const url = `https://api.agromonitoring.com/agro/1.0/soil?polyid=${POLYGON_ID}&appid=${API_KEY}`;

function fetchRealTimeSoilData() {
  fetch(url)
    .then(res => res.json())
    .then(data => {
      if (data && typeof data === 'object') {
        const t10 = data.t10 ? (data.t10 - 273.15).toFixed(2) : '--';
        const t0 = data.t0 ? (data.t0 - 273.15).toFixed(2) : '--';
        const moisture = data.moisture !== undefined ? (data.moisture * 100).toFixed(0) + '%' : '--';
        const ph = data.ph !== undefined ? data.ph.toFixed(1) : '--';

        // Update HTML elements
        document.getElementById('soil-temp').textContent = `${t0} °C`;
document.getElementById('soil-temp10').textContent = `${t10} °C`;
document.getElementById('soil-moisture').textContent = moisture; // Already has %
document.getElementById('soil-ph').textContent = ph;
      } else {
        console.warn("No real-time soil data received.");
      }
    })
    .catch(error => {
      console.error('Error fetching soil data:', error);
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  fetchRealTimeSoilData();
  setInterval(fetchRealTimeSoilData, 10 * 60 * 1000); // refresh every 10 minutes
});
