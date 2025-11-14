# ==========================================================================
#
#   services.py for JalanSafe AI (XAI-Enhanced Version)
#
# ==========================================================================

import os
from dotenv import load_dotenv

# --- Load .env file at the very top ---
load_dotenv()

import hashlib
import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import time
import traceback
import random  # <-- 导入 random 模块

import schemas, models # <-- 导入 models 以便查询数据库
from geopy.geocoders import Nominatim
from geopy.point import Point as GeopyPoint

# --- API Keys ---
ORS_API_KEY = os.getenv("ORS_API_KEY")
GRAPHHOPPER_API_KEY = os.getenv("GRAPHHOPPER_API_KEY")

# --- Geocoding & Routing Functions (No Changes Here) ---

def geocode_location(location_name: str, proximity_point: Optional[schemas.Point] = None) -> Optional[schemas.Point]:
    """
    Geocodes a location name to coordinates using Nominatim with a 3-step fallback.
    1. Strict proximity search. 2. Biased proximity search. 3. Global search.
    """
    print(f"\n--- [GEOCODING with Nominatim] Attempting: '{location_name}' ---")
    geolocator = Nominatim(user_agent="jalansafe_ai_app/1.5_FALLBACK")
    
    base_params = {'country_codes': 'MY', 'limit': 1}
    location = None

    # Step 1: Strict Bounded Search (Try to find it ONLY within the user's area)
    if proximity_point:
        print(f"--> Step 1: Strict search near ({proximity_point.lat}, {proximity_point.lon})")
        lat_buffer, lon_buffer = 0.5, 0.5
        southwest = GeopyPoint(latitude=proximity_point.lat - lat_buffer, longitude=proximity_point.lon - lon_buffer)
        northeast = GeopyPoint(latitude=proximity_point.lat + lat_buffer, longitude=proximity_point.lon + lon_buffer)
        
        try:
            location = geolocator.geocode(location_name, viewbox=[southwest, northeast], bounded=True, **base_params, timeout=15)
        except Exception:
            pass # Ignore errors and proceed to next step

    # Step 2: Biased Search (If strict search fails, look globally but PREFER results near the user)
    if not location and proximity_point:
        print(f"--> Step 2: Biased search, preferring results near user.")
        try:
            # viewbox without bounded=True acts as a preference
            location = geolocator.geocode(location_name, viewbox=[southwest, northeast], **base_params, timeout=15)
        except Exception:
            pass

    # Step 3: Global Search (If all else fails, search the entire country)
    if not location:
        print(f"--> Step 3: Broad search across the country.")
        try:
            location = geolocator.geocode(location_name, **base_params, timeout=15)
        except Exception as e:
            print(f"--> [FATAL ERROR] during Nominatim geocoding:")
            print(traceback.format_exc())
            return None

    # Process the final result
    if location:
        lat, lon = location.latitude, location.longitude
        print(f"--> [SUCCESS] Found '{location.address}' at ({lat}, {lon})")
        return schemas.Point(lat=lat, lon=lon)
    else:
        print(f"--> [FAILURE] Nominatim returned no results for '{location_name}'.")
        return None

def reverse_geocode_location(point: schemas.Point) -> str:
    geolocator = Nominatim(user_agent="jalansafe_ai_app/1.4_XAI_VERSION")
    try:
        location = geolocator.reverse(f"{point.lat}, {point.lon}", exactly_one=True, language='en', timeout=20)
        return location.address if location else "Address could not be determined"
    except Exception as e:
        print(f"An error occurred during reverse geocoding: {e}")
        return "Address lookup failed due to an error"

def get_routes_from_ors(start: schemas.Point, end: schemas.Point) -> List[Dict]:
    if not ORS_API_KEY or "YOUR_KEY" in ORS_API_KEY:
        print("ERROR: ORS API key not configured."); return []

    def find_nearest_routable_point(point: schemas.Point) -> Optional[List[float]]:
        print(f"--- [ORS Snapping] Finding nearest road for: ({point.lat}, {point.lon}) ---")
        url = "https://api.openrouteservice.org/geocode/reverse"
        params = {'api_key': ORS_API_KEY, 'point.lon': point.lon, 'point.lat': point.lat, 'size': 1}
        try:
            time.sleep(1.1)
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and data.get('features'):
                snapped_coords = data['features'][0]['geometry']['coordinates']
                print(f"--> [SUCCESS] Snapped point is: {snapped_coords}")
                return snapped_coords
            print("--> [FAILURE] ORS could not find a nearby road."); return None
        except requests.exceptions.RequestException as e:
            print(f"--> [FATAL ERROR] during ORS snapping: {e}"); return None

    snapped_start = find_nearest_routable_point(start)
    snapped_end = find_nearest_routable_point(end)
    if not snapped_start or not snapped_end:
        print("Could not snap one or both points to a routable road."); return []

    headers = {'Authorization': ORS_API_KEY, 'Content-Type': 'application/json'}
    body = {"coordinates": [snapped_start, snapped_end], "alternative_routes": {"target_count": 3, "weight_factor": 1.5, "share_factor": 0.6}, "instructions": "false"}
    
    try:
        response = requests.post('https://api.openrouteservice.org/v2/directions/driving-car', json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        routes = []
        for route_data in data.get('routes', []):
            route_hash = hashlib.sha256(str(route_data['geometry']).encode()).hexdigest()
            routes.append({"id": route_hash, "geometry": route_data['geometry'], "base_travel_time": route_data['summary']['duration'], "distance": route_data['summary']['distance']})
        print(f"--> [SUCCESS] ORS returned {len(routes)} routes.")
        return routes
    except requests.exceptions.RequestException as e:
        print(f"FATAL Error fetching routes from ORS: {e}")
        if e.response: print(f"--> ORS SERVER RESPONSE: {e.response.text}")
        return []

# 我们可以创建一个新的函数，或者直接替换 get_routes_from_ors
def get_routes_from_graphhopper(start: schemas.Point, end: schemas.Point) -> List[Dict]:
    """
    Fetches up to 3 driving routes from GraphHopper.
    """
    if not GRAPHHOPPER_API_KEY:
        print("ERROR: GraphHopper API key not configured.")
        return []

    url = "https://graphhopper.com/api/1/route"
    params = {
        "point": [f"{start.lat},{start.lon}", f"{end.lat},{end.lon}"],
        "vehicle": "car",
        "key": GRAPHHOPPER_API_KEY,
        "points_encoded": "true", # Important for polyline
        "instructions": "false",
        "calc_points": "true",
        "algorithm": "alternative_route", # Ask for alternatives
        "ch.disable": "true", # Disabling CH is often needed for alternative routes
        "alternative_route.max_paths": 3,
    }

    print("\n--- DEBUGGING GraphHopper Routing Request ---")
    print(f"Request URL: {url}")
    print(f"Request Params: {params}")
    print("-------------------------------------------\n")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        routes = []
        for path_data in data.get('paths', []):
            route_hash = hashlib.sha256(str(path_data['points']).encode()).hexdigest()
            routes.append({
                "id": route_hash,
                "geometry": path_data['points'], # GraphHopper uses 'points' for the polyline
                "base_travel_time": path_data['time'] / 1000, # Convert ms to seconds
                "distance": path_data['distance'] # Already in meters
            })
        print(f"--> [SUCCESS] GraphHopper returned {len(routes)} routes.")
        return routes
    except requests.exceptions.RequestException as e:
        print(f"FATAL Error fetching routes from GraphHopper: {e}")
        if e.response is not None:
            print(f"--> GraphHopper SERVER RESPONSE: {e.response.text}")
        return []

# --- 核心改造：可解释化AI评分逻辑 ---

def get_latest_issue_report(db: Session) -> Optional[models.Report]:
    """Helper to get the most recent 'road_condition' report from the DB for demo purposes."""
    return db.query(models.Report).filter(models.Report.report_type == 'road_condition').order_by(models.Report.created_at.desc()).first()

def calculate_ai_smart_routes(routes: List[Dict], db: Session) -> List[Dict]:
    if not routes:
        return []

    # Get a real issue from DB to use as "evidence" for a bad route
    latest_issue = get_latest_issue_report(db)

    scored_routes = []
    for i, route in enumerate(routes):
        # 1. 模拟实时交通：使用随机数
        traffic_congestion_factor = random.uniform(0.1, 0.5)
        traffic_score = (1 - traffic_congestion_factor) * 100

        # 2. 模拟道路质量评分和证据发现
        road_quality_score = random.uniform(85, 98) # Assume good quality by default
        issues_found = []

        # For DEMO: Deliberately assign the latest issue to the 2nd or 3rd route to make it yellow/red
        if latest_issue and i > 0:
            road_quality_score = random.uniform(40, 60) # Penalize the score
            issues_found.append({
                "issue_type": latest_issue.report_type,
                "description": latest_issue.description,
                "photo_url": latest_issue.photo_url,
                "latitude": latest_issue.latitude,
                "longitude": latest_issue.longitude,
            })
            print(f"--> DEMO: Assigned real issue '{latest_issue.description}' to route {i+1}")

        # 3. 计算总分
        W_TRAFFIC, W_ROAD_QUALITY = 0.5, 0.5
        final_score = (W_TRAFFIC * traffic_score) + (W_ROAD_QUALITY * road_quality_score)
        
        # 4. 填充所有解释字段
        route['final_score'] = final_score
        route['traffic_score'] = traffic_score
        route['road_quality_score'] = road_quality_score
        route['issues'] = issues_found
        
        scored_routes.append(route)
        
    scored_routes.sort(key=lambda x: x['final_score'], reverse=True)
    
    colors = ['green', 'yellow', 'red']
    for i, route in enumerate(scored_routes):
        route['color'] = colors[i] if i < len(colors) else 'gray'
             
    return scored_routes