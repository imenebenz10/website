from flask import Flask, jsonify, send_file
import ee
import pandas as pd
import folium
import threading
import os
import numpy as np
from io import BytesIO
from flask_cors import CORS
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

static_dir = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Earth Engine
ee.Initialize(project='project7-463821')

# Configuration
API_KEY = "a57be93e6b755d4f85fe6c922f3084ab"
POLYGON_ID = "6818b7dbd23361542f21605b"

# Nitrogen estimation model coefficients
MODEL_COEFFICIENTS = {
    'ndvi_weight': 0.5,    # Contribution of NDVI to nitrogen estimate
    'ndre_weight': 0.7,    # Contribution of NDRE to nitrogen estimate
    'intercept': 0.2,      # Baseline nitrogen level
    'max_nitrogen': 3.0    # Maximum nitrogen value for scaling
}

# Global variables for cached data
ndvi_data = None
ndre_data = None
nitrogen_data = None
latest_ndvi_image = None
latest_ndre_image = None
ee_polygon = None

def initialize_polygon():
    global ee_polygon
    try:
        # Fetch polygon from AgroMonitoring API
        import requests
        url = f"https://api.agromonitoring.com/agro/1.0/polygons/{POLYGON_ID}?appid={API_KEY}"
        response = requests.get(url)
        polygon_data = response.json()
        geojson_geometry = polygon_data["geo_json"]
        
        # Create Earth Engine geometry
        if geojson_geometry["type"] == "Feature" and "geometry" in geojson_geometry:
            geometry_part = geojson_geometry["geometry"]
            ee_polygon = ee.Geometry(geometry_part)
        else:
            ee_polygon = ee.Geometry(geojson_geometry)
            
        print("Successfully loaded polygon into GEE")
    except Exception as e:
        print(f"Error initializing polygon: {str(e)}")
        # Fallback to a default polygon if API fails
        ee_polygon = ee.Geometry.Polygon(
            [[[-2.6, 51.45],
              [-2.6, 51.46],
              [-2.58, 51.46],
              [-2.58, 51.45],
              [-2.6, 51.45]]])
        print("Using fallback polygon")

def get_sentinel2_collection(start_date, end_date):
    return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(ee_polygon) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

def calculate_ndvi():
    global ndvi_data, latest_ndvi_image
    try:
        s2 = get_sentinel2_collection('2015-01-01', '2025-07-01')
        
        # Function to calculate NDVI for a single image
        def add_ndvi(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi)
        
        # Apply NDVI calculation to the entire collection
        ndvi_collection = s2.map(add_ndvi).select('NDVI')
        latest_ndvi_image = ndvi_collection.sort('system:time_start', False).first()
        
        # Extract mean NDVI values for the polygon
        def get_mean_ndvi(img):
            date = img.date().format('YYYY-MM-dd')
            mean = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee_polygon,
                scale=10
            ).get('NDVI')
            return ee.Feature(None, {'date': date, 'NDVI': mean})
        
        # Get NDVI statistics as a list
        ndvi_stats = ndvi_collection.map(get_mean_ndvi).getInfo()
        
        # Convert to DataFrame
        ndvi_data = pd.DataFrame([{
            'Date': f['properties']['date'],
            'NDVI': f['properties']['NDVI']
        } for f in ndvi_stats['features'] if f['properties']['NDVI'] is not None])
        
        print("NDVI data loaded successfully")
    except Exception as e:
        print(f"Error calculating NDVI: {str(e)}")

def calculate_ndre():
    global ndre_data, latest_ndre_image
    try:
        s2 = get_sentinel2_collection('2015-01-01', '2025-07-01')
        
        def add_ndre(image):
            ndre = image.normalizedDifference(['B8', 'B5']).rename('NDRE')
            return image.addBands(ndre)
        
        ndre_collection = s2.map(add_ndre).select('NDRE')
        latest_ndre_image = ndre_collection.sort('system:time_start', False).first()
        
        def get_mean_ndre(img):
            date = img.date().format('YYYY-MM-dd')
            mean = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee_polygon,
                scale=10
            ).get('NDRE')
            return ee.Feature(None, {'date': date, 'NDRE': mean})
        
        ndre_stats = ndre_collection.map(get_mean_ndre).getInfo()
        
        ndre_data = pd.DataFrame([{
            'Date': f['properties']['date'],
            'NDRE': f['properties']['NDRE']
        } for f in ndre_stats['features'] if f['properties']['NDRE'] is not None])
        
        print("NDRE data loaded successfully")
    except Exception as e:
        print(f"Error calculating NDRE: {str(e)}")

def estimate_nitrogen():
    global nitrogen_data, ndvi_data, ndre_data
    try:
        if ndvi_data is None or ndre_data is None:
            print("NDVI or NDRE data not available for nitrogen estimation")
            return
            
        # Merge datasets on date
        combined_df = pd.merge(ndvi_data, ndre_data, on='Date', how='inner')
        
        # Apply nitrogen estimation
        combined_df['Estimated_N'] = combined_df.apply(
            lambda row: np.clip(
                (MODEL_COEFFICIENTS['ndvi_weight'] * row['NDVI'] +
                 MODEL_COEFFICIENTS['ndre_weight'] * row['NDRE'] +
                 MODEL_COEFFICIENTS['intercept']),
                0, 
                MODEL_COEFFICIENTS['max_nitrogen']
            ),
            axis=1
        )
        
        # Calculate additional metrics
        combined_df['NDRE/NDVI_ratio'] = combined_df['NDRE'] / combined_df['NDVI']
        combined_df['NDRE-NDVI_diff'] = combined_df['NDRE'] - combined_df['NDVI']
        
        # Convert dates to datetime
        combined_df['Date'] = pd.to_datetime(combined_df['Date'])
        
        nitrogen_data = combined_df
        print("Nitrogen estimates calculated successfully")
        
        # Generate and save visualizations
        generate_nitrogen_visualizations()
    except Exception as e:
        print(f"Error estimating nitrogen: {str(e)}")

# At the start of your nitrogen visualization function
import os
os.environ['MPLBACKEND'] = 'Agg'  # Force backend before importing pyplot
import matplotlib.pyplot as plt

def generate_nitrogen_visualizations():
    try:
        if nitrogen_data is None:
            return
            
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Nitrogen estimates over time
        plt.subplot(2, 2, 1)
        plt.plot(nitrogen_data['Date'], nitrogen_data['Estimated_N'], 'o-', color='green')
        plt.title('Estimated Nitrogen Over Time')
        plt.xlabel('Date')
        plt.ylabel('Nitrogen (relative units)')
        plt.grid(True)
        
        # Plot 2: NDVI vs NDRE colored by nitrogen
        plt.subplot(2, 2, 2)
        scatter = plt.scatter(nitrogen_data['NDVI'], nitrogen_data['NDRE'], 
                            c=nitrogen_data['Estimated_N'], cmap='viridis')
        plt.colorbar(scatter, label='Estimated Nitrogen')
        plt.xlabel('NDVI')
        plt.ylabel('NDRE')
        plt.title('NDVI vs NDRE Colored by Nitrogen')
        
        # Plot 3: Nitrogen vs NDRE/NDVI ratio
        plt.subplot(2, 2, 3)
        plt.scatter(nitrogen_data['NDRE/NDVI_ratio'], nitrogen_data['Estimated_N'])
        plt.xlabel('NDRE/NDVI Ratio')
        plt.ylabel('Estimated Nitrogen')
        plt.title('Nitrogen vs NDRE/NDVI Ratio')
        plt.grid(True)
        
        # Plot 4: Histogram of nitrogen estimates
        plt.subplot(2, 2, 4)
        plt.hist(nitrogen_data['Estimated_N'], bins=15, color='lightgreen')
        plt.xlabel('Nitrogen Level')
        plt.ylabel('Frequency')
        plt.title('Distribution of Nitrogen Estimates')
        
        plt.tight_layout()
        plt.savefig('/Users/siddig/Desktop/untitled folder/static/nitrogen_analysis.png')
        plt.close()  # Important: close the figure to free memory
        
        # Generate report
        generate_nitrogen_report()
    except Exception as e:
        print(f"Error generating nitrogen visualizations: {str(e)}")

def generate_nitrogen_report():
    try:
        if nitrogen_data is None:
            return
            
        report = f"""
Nitrogen Estimation Report (Empirical Regression Model)
=====================================================
Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
Time Period Covered: {nitrogen_data['Date'].min().strftime('%Y-%m-%d')} to {nitrogen_data['Date'].max().strftime('%Y-%m-%d')}

Model Parameters:
- NDVI Weight: {MODEL_COEFFICIENTS['ndvi_weight']}
- NDRE Weight: {MODEL_COEFFICIENTS['ndre_weight']}
- Intercept: {MODEL_COEFFICIENTS['intercept']}
- Maximum Nitrogen Value: {MODEL_COEFFICIENTS['max_nitrogen']}

Results Summary:
- Mean Estimated Nitrogen: {nitrogen_data['Estimated_N'].mean():.2f}
- Maximum Nitrogen: {nitrogen_data['Estimated_N'].max():.2f} on {nitrogen_data.loc[nitrogen_data['Estimated_N'].idxmax(), 'Date'].strftime('%Y-%m-%d')}
- Minimum Nitrogen: {nitrogen_data['Estimated_N'].min():.2f} on {nitrogen_data.loc[nitrogen_data['Estimated_N'].idxmin(), 'Date'].strftime('%Y-%m-%d')}

Data Quality Indicators:
- NDVI-NDRE Correlation: {nitrogen_data['NDVI'].corr(nitrogen_data['NDRE']):.2f}
- Average NDRE/NDVI Ratio: {nitrogen_data['NDRE/NDVI_ratio'].mean():.2f}
"""
        
        with open('static/nitrogen_estimation_report.txt', 'w') as f:
            f.write(report)
            
        print("Nitrogen report generated successfully")
    except Exception as e:
        print(f"Error generating nitrogen report: {str(e)}")

def create_satellite_map():
    try:
        # Get the latest Sentinel-2 image
        s2 = get_sentinel2_collection('2023-01-01', '2023-12-31')
        latest_image = s2.sort('system:time_start', False).first()
        
        # Create base map
        centroid = ee_polygon.centroid().getInfo()['coordinates']
        m = folium.Map(location=[centroid[1], centroid[0]], zoom_start=12)
        
        # Define all visualization parameters
        vis_params = {
            'ndvi': {
                'bands': ['NDVI'],
                'min': -1,
                'max': 1,
                'palette': ['red', 'yellow', 'green']
            },
            'ndre': {
                'bands': ['NDRE'],
                'min': -1,
                'max': 1,
                'palette': ['red', 'yellow', 'green']
            },
            'true_color': {
                'bands': ['B4', 'B3', 'B2'],
                'min': 0,
                'max': 3000
            },
            'false_color': {
                'bands': ['B8', 'B4', 'B3'],
                'min': 0,
                'max': 3000
            }
        }
        
        # Add all layers to the map
        for name, params in vis_params.items():
            try:
                if name in ['ndvi', 'ndre']:
                    # Use pre-calculated NDVI/NDRE images
                    image = latest_ndvi_image if name == 'ndvi' else latest_ndre_image
                    if not image:
                        continue
                else:
                    # Use the original Sentinel-2 image
                    image = latest_image
                
                map_id_dict = image.getMapId(params)
                folium.raster_layers.TileLayer(
                    tiles=map_id_dict['tile_fetcher'].url_format,
                    attr='Google Earth Engine',
                    name=name.replace('_', ' ').title(),
                    overlay=True
                ).add_to(m)
            except Exception as e:
                print(f"Error adding {name} layer: {str(e)}")
                continue
        
        # Add polygon boundary
        folium.GeoJson(
            data=ee_polygon.getInfo(),
            name='Field Boundary',
            style_function=lambda x: {'color': 'blue', 'fill': False}
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save the map
        map_path = os.path.join(static_dir, 'satellite_map.html')
        m.save(map_path)
        return map_path
        
    except Exception as e:
        print(f"Error creating satellite map: {str(e)}")
        return None


def load_all_data():
    initialize_polygon()
    calculate_ndvi()
    calculate_ndre()
    estimate_nitrogen()
    create_satellite_map()


# API Endpoints
@app.route('/api/ndvi')
def get_ndvi():
    if ndvi_data is None:
        return jsonify({"error": "NDVI data not loaded yet"}), 503
    return jsonify(ndvi_data.to_dict(orient='records'))

@app.route('/api/ndre')
def get_ndre():
    if ndre_data is None:
        return jsonify({"error": "NDRE data not loaded yet"}), 503
    return jsonify(ndre_data.to_dict(orient='records'))

@app.route('/api/nitrogen')
def get_nitrogen():
    if nitrogen_data is None:
        return jsonify({"error": "Nitrogen data not loaded yet", "status": "loading"}), 202
    
    # Convert DataFrame to list of dicts and ensure date formatting
    result = nitrogen_data.to_dict(orient='records')
    
    # Convert numpy types to native Python types
    for item in result:
        for key, value in item.items():
            if isinstance(value, (np.floating, np.integer)):
                item[key] = float(value)
            elif isinstance(value, np.bool_):
                item[key] = bool(value)
            elif isinstance(value, pd.Timestamp):
                item[key] = value.strftime('%Y-%m-%d')
    
    return jsonify(result)

@app.route('/api/satellite/map')
def get_satellite_map():
    try:
        map_path = create_satellite_map()
        if not map_path or not os.path.exists(map_path):
            raise FileNotFoundError("Satellite map file not generated")
        return send_file(map_path, mimetype='text/html')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nitrogen/analysis')
def get_nitrogen_analysis():
    try:
        return send_file('static/nitrogen_analysis.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/nitrogen/report')
def get_nitrogen_report():
    try:
        return send_file('static/nitrogen_estimation_report.txt', mimetype='text/plain')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def get_status():
    return jsonify({
        'ndvi_loaded': ndvi_data is not None,
        'ndre_loaded': ndre_data is not None,
        'nitrogen_loaded': nitrogen_data is not None,
        'polygon_loaded': ee_polygon is not None
    })

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/style.css')
def serve_css():
    return send_file('style.css')

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Start data loading in background
    threading.Thread(target=load_all_data).start()
    
    # Run the server
    app.run(host='0.0.0.0', port=5001, debug=True)