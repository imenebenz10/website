import ee
import requests
import folium
import json

# Initialize Earth Engine with your project ID
ee.Initialize(project='project7-463821')

API_KEY = "a57be93e6b755d4f85fe6c922f3084ab"
POLYGON_ID = "6818b7dbd23361542f21605b"

url = f"https://api.agromonitoring.com/agro/1.0/polygons/{POLYGON_ID}?appid={API_KEY}"
response = requests.get(url)

if response.status_code == 200:
    polygon_data = response.json()
    print("Raw polygon data:")
    print(json.dumps(polygon_data, indent=2))
    
    geojson_geometry = polygon_data["geo_json"]
    print("\nGeoJSON geometry:")
    print(json.dumps(geojson_geometry, indent=2))
    
    # Extract geometry from the Feature
    if geojson_geometry["type"] == "Feature" and "geometry" in geojson_geometry:
        geometry_part = geojson_geometry["geometry"]
        ee_polygon = ee.Geometry(geometry_part)
    else:
        # Fallback for other formats
        ee_polygon = ee.Geometry(geojson_geometry)
    
    print("Successfully loaded polygon into GEE:")
    print(ee_polygon.getInfo())
    
    # Create a folium map
    try:
        centroid = ee_polygon.centroid().coordinates().getInfo()
        m = folium.Map(location=[centroid[1], centroid[0]], zoom_start=12)
        
        # Use the EE polygon geometry for folium instead of original geojson
        folium_geojson = ee_polygon.getInfo()
        
        folium.GeoJson(
            data=folium_geojson, 
            name="AgroMonitoring Polygon",
            style_function=lambda x: {
                'fillColor': 'red', 
                'color': 'red', 
                'weight': 2, 
                'fillOpacity': 0.3
            }
        ).add_to(m)
        
        m.save('polygon_map.html')
        print("Map saved as 'polygon_map.html'")
        
    except Exception as e:
        print(f"Error creating map: {str(e)}")
        # Fallback: try to extract bounds for map center
        try:
            bounds = ee_polygon.bounds().getInfo()
            coords = bounds['coordinates'][0]
            center_lat = sum(coord[1] for coord in coords) / len(coords)
            center_lon = sum(coord[0] for coord in coords) / len(coords)
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            folium.GeoJson(
                data=ee_polygon.getInfo(), 
                name="AgroMonitoring Polygon",
                style_function=lambda x: {
                    'fillColor': 'red', 
                    'color': 'red', 
                    'weight': 2, 
                    'fillOpacity': 0.3
                }
            ).add_to(m)
            m.save('polygon_map.html')
            print("Map saved as 'polygon_map.html' (using bounds)")
        except Exception as e2:
            print(f"Could not create map: {str(e2)}")
    
    # Upload as an EE asset
    asset_id = "users/siddig_yasir/agromonitoring_polygon"
    
    try:
        # Create a feature collection from the geometry
        feature = ee.Feature(ee_polygon)
        feature_collection = ee.FeatureCollection([feature])
        
        # Start the export task
        task = ee.batch.Export.table.toAsset(
            collection=feature_collection,
            description='AgroMonitoring Polygon Upload',
            assetId=asset_id
        )
        task.start()
        print(f"Upload started! Check your Earth Engine Tasks tab to monitor progress.")
        print(f"Asset will be available at: {asset_id}")
        
    except Exception as e:
        print(f"Error uploading polygon: {str(e)}")
        
else:
    print(f"Error fetching polygon: {response.status_code}")
    print(response.text)