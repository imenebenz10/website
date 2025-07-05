import requests
from datetime import datetime

# Your AgroMonitoring API key
API_KEY = 'a57be93e6b755d4f85fe6c922f3084ab'
# Your polygon ID (already created)
POLYGON_ID = '6818b7dbd23361542f21605b'


# Date range: from June 20, 2025 to now
start_date = datetime(2025, 3, 10)  # June 20, 2025
end_date = datetime.now()  # Current date and time

# Convert to Unix timestamps (required by API)
start_timestamp = int(start_date.timestamp())
end_timestamp = int(end_date.timestamp())

print(f"Fetching soil data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"Timestamp range: {start_timestamp} to {end_timestamp}")
print("-" * 50)

# API endpoint with date range parameters
url = f"http://api.agromonitoring.com/agro/1.0/soil?polyid={POLYGON_ID}&start={start_timestamp}&end={end_timestamp}&appid={API_KEY}"

try:
    # Make the GET request
    response = requests.get(url)
    
    # Check and handle the response
    if response.status_code == 200:
        soil_data = response.json()
        
        if soil_data:  # Check if data exists
            print("Soil Data:")
            print("=" * 50)
            
            # Handle multiple measurements (list format) - this is what we expect with date range
            if isinstance(soil_data, list):
                if len(soil_data) == 0:
                    print("No measurements found in the specified date range.")
                else:
                    print(f"Found {len(soil_data)} measurements:")
                    print("=" * 70)
                    
                    for i, measurement in enumerate(soil_data):
                        if isinstance(measurement, dict):
                            print(f"\nMeasurement {i + 1}:")
                            
                            if 'dt' in measurement:
                                try:
                                    date = datetime.fromtimestamp(measurement['dt'])
                                    print(f"  Date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
                                except (ValueError, OSError):
                                    print(f"  Timestamp: {measurement['dt']} (invalid)")
                            
                            # Print soil parameters with descriptions
                            parameter_descriptions = {
                                't10': 'Soil Temperature (10cm)',
                                't0': 'Surface Temperature', 
                                'moisture': 'Soil Moisture'
                            }
                            
                            for key, value in measurement.items():
                                if key != 'dt':
                                    description = parameter_descriptions.get(key, key)
                                    if key in ['t10', 't0']:
                                        celsius = value - 273.15
                                        print(f"  {description}: {celsius:.2f}°C")
                                    elif key == 'moisture':
                                        print(f"  {description}: {value:.3f}")
                                    else:
                                        print(f"  {description}: {value}")
                        else:
                            print(f"  Unexpected format: {measurement}")
                    
                    # Summary statistics
                    print("\n" + "=" * 70)
                    print("SUMMARY:")
                    if soil_data:
                        temps_10cm = [m.get('t10', 0) - 273.15 for m in soil_data if 't10' in m]
                        surface_temps = [m.get('t0', 0) - 273.15 for m in soil_data if 't0' in m]
                        moisture_levels = [m.get('moisture', 0) for m in soil_data if 'moisture' in m]
                        
                        if temps_10cm:
                            print(f"Soil Temperature (10cm): Min={min(temps_10cm):.1f}°C, Max={max(temps_10cm):.1f}°C, Avg={sum(temps_10cm)/len(temps_10cm):.1f}°C")
                        if surface_temps:
                            print(f"Surface Temperature: Min={min(surface_temps):.1f}°C, Max={max(surface_temps):.1f}°C, Avg={sum(surface_temps)/len(surface_temps):.1f}°C")
                        if moisture_levels:
                            print(f"Soil Moisture: Min={min(moisture_levels):.3f}, Max={max(moisture_levels):.3f}, Avg={sum(moisture_levels)/len(moisture_levels):.3f}")
            
            # Handle single measurement (dictionary format)
            elif isinstance(soil_data, dict):
                # Convert timestamp to readable date
                if 'dt' in soil_data:
                    try:
                        date = datetime.fromtimestamp(soil_data['dt'])
                        print(f"Date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
                    except (ValueError, OSError):
                        print(f"Timestamp: {soil_data['dt']} (invalid timestamp)")
                
                # Print soil parameters with descriptions
                parameter_descriptions = {
                    't10': 'Soil Temperature (10cm depth)',
                    't0': 'Surface Temperature', 
                    'moisture': 'Soil Moisture'
                }
                
                for key, value in soil_data.items():
                    if key != 'dt':  # Skip timestamp as we already formatted it
                        description = parameter_descriptions.get(key, key)
                        if key in ['t10', 't0']:
                            # Convert from Kelvin to Celsius for temperature
                            celsius = value - 273.15
                            print(f"{description}: {celsius:.2f}°C ({value}K)")
                        elif key == 'moisture':
                            print(f"{description}: {value:.3f} (0-1 scale)")
                        else:
                            print(f"{description}: {value}")
            
            else:
                print(f"Unexpected data format: {soil_data}")
        else:
            print("No soil data available for this polygon")
            
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Network error occurred: {e}")
except Exception as e:
    print(f"An error occurred: {e}")