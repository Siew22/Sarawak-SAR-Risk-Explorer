import os
from dotenv import load_dotenv
load_dotenv()

import hashlib
import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import time
import traceback
import random
import polyline
from datetime import datetime, timedelta
from haversine import haversine, Unit
import schemas, models
from geopy.geocoders import Nominatim
from geopy.point import Point as GeopyPoint

GRAPHHOPPER_API_KEY = os.getenv("GRAPHHOPPER_API_KEY")
OWM_API_KEY = "5f66e14d6562958e2f9fb986b4fc8bdf"

def get_weather_condition(lat: float, lon: float) -> str:
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if 'weather' in data and len(data['weather']) > 0:
                return f"{data['weather'][0]['main'].lower()}|{data['weather'][0]['description']}"
    except: pass
    return "unknown|unknown"

def geocode_location(location_name: str, proximity_point: Optional[schemas.Point] = None) -> Optional[schemas.Point]:
    print(f"\n--- [GEOCODING] '{location_name}' ---")
    geolocator = Nominatim(user_agent="jalansafe_ai_app/6.0_FIX")
    try:
        location = geolocator.geocode(location_name, country_codes='MY', limit=1, timeout=10)
        if location:
            return schemas.Point(lat=round(location.latitude, 4), lon=round(location.longitude, 4))
    except: pass
    return None

def reverse_geocode_location(point: schemas.Point) -> str:
    geolocator = Nominatim(user_agent="jalansafe_ai_app/6.0_FIX")
    try:
        location = geolocator.reverse(f"{point.lat}, {point.lon}", exactly_one=True, language='en', timeout=10)
        return location.address if location else "Unknown"
    except: return "Lookup failed"

def _fetch_graphhopper_route(points: List[str]) -> Optional[Dict]:
    if not GRAPHHOPPER_API_KEY: return None
    url = "https://graphhopper.com/api/1/route"
    params = {"point": points, "vehicle": "car", "key": GRAPHHOPPER_API_KEY, "points_encoded": "true", "instructions": "true", "calc_points": "true"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('paths'):
                p = data['paths'][0]
                id_string = "|".join(points)
                r_id = hashlib.md5(id_string.encode()).hexdigest()
                
                summary_text = "Route Option"
                if 'instructions' in p:
                    for instr in p['instructions']:
                         if 'street_name' in instr and len(instr['street_name']) > 3:
                             summary_text = "Via " + instr['street_name']
                             break
                
                return {"id": r_id, "geometry": p['points'], "base_travel_time": p['time']/1000, "distance": p['distance'], "instructions": p.get('instructions', []), "summary": summary_text}
    except: pass
    return None

def get_multiple_routes_with_fallback(start: schemas.Point, end: schemas.Point, num_alternatives: int = 2) -> List[Dict]:
    s_str = f"{start.lat:.4f},{start.lon:.4f}"
    e_str = f"{end.lat:.4f},{end.lon:.4f}"
    routes = []
    primary = _fetch_graphhopper_route([s_str, e_str])
    if primary: routes.append(primary)
    
    if primary:
        try:
            path = polyline.decode(primary['geometry'])
            if len(path) > 20:
                mid = path[len(path) // 2]
                alt1 = _fetch_graphhopper_route([s_str, f"{mid[0]+0.01:.4f},{mid[1]+0.01:.4f}", e_str])
                if alt1 and alt1['id'] != primary['id']: routes.append(alt1)
                alt2 = _fetch_graphhopper_route([s_str, f"{mid[0]-0.01:.4f},{mid[1]-0.01:.4f}", e_str])
                if alt2 and alt2['id'] != primary['id']: routes.append(alt2)
        except: pass
    return routes

# --- AI SCORING ---
def is_point_near_route_haversine(issue_point: tuple, route_geometry: str, threshold_meters: int = 300) -> bool:
    try:
        path_points = polyline.decode(route_geometry)
        for p in path_points:
            if haversine(issue_point, p, unit=Unit.METERS) <= threshold_meters: 
                return True
    except: pass
    return False

def calculate_ai_smart_routes(routes: List[Dict], db: Session) -> List[Dict]:
    if not routes: return []
    
    print(f"\n--- [AI SCORING V22.0] Adjusted Penalties ---")
    
    all_issues = db.query(models.Report).filter(models.Report.report_type == 'road_condition').all()
    
    try:
        start_coords = polyline.decode(routes[0]['geometry'])[0]
        weather_info = get_weather_condition(start_coords[0], start_coords[1])
    except: weather_info = "unknown|unknown"
    
    routes.sort(key=lambda r: r['base_travel_time'])
    optimal_time = routes[0]['base_travel_time']
    scored_routes = []
    
    time_window = datetime.utcnow() - timedelta(minutes=30)

    for i, route in enumerate(routes):
        is_shortest = (i == 0)
        
        user_count = db.query(models.RouteChoice).filter(
            models.RouteChoice.chosen_route_hash == route['id'],
            models.RouteChoice.created_at >= time_window
        ).count()
        
        issues_found = []
        for issue in all_issues:
            if is_point_near_route_haversine((issue.latitude, issue.longitude), route['geometry']):
                issues_found.append({
                    "description": issue.description, 
                    "photo_url": issue.photo_url, 
                    "type": issue.report_type.value, 
                    "date": issue.created_at.strftime("%Y-%m-%d")
                })
        
        # --- SCORING LOGIC ---
        score = 100.0
        
        # 1. Issues: Reduced penalty from 25 to 10. 
        # 4 issues = -40 points -> Score 60 -> Yellow.
        score -= len(issues_found) * 10
        
        # 2. Traffic: Keep at 5
        score -= user_count * 5
        
        # 3. Time
        time_diff = route['base_travel_time'] - optimal_time
        if optimal_time > 0: 
            score -= (time_diff / optimal_time) * 15 
            
        final_score = max(0, score)
        
        # --- COLOR LOGIC ---
        color = 'yellow'
        
        if final_score > 80: color = 'green'
        elif final_score < 50: color = 'red'
        
        # Rule: If issues exist, downgrade Green to Yellow, but NOT to Red immediately
        if len(issues_found) > 0:
            if color == 'green': color = 'yellow'
            
        # Rule: Only RED if really bad (Score < 50) OR Heavy Traffic
        if user_count > 10: color = 'red'

        # Rule: Optimal + Clean + Low Traffic = Green
        if is_shortest and len(issues_found) == 0 and user_count < 5:
            color = 'green'

        tags = []
        if is_shortest: tags.append("OPTIMAL_PATH")
        if len(issues_found) > 0: tags.append("HAS_ISSUES")
        if user_count > 0: tags.append("HAS_TRAFFIC")

        print(f"-> Route {i+1}: Issues={len(issues_found)}, Users={user_count}, Score={final_score:.0f} => {color}")

        route.update({
            'final_score': final_score, 'active_users': user_count, 'issues': issues_found,
            'color': color, 'time_slower': time_diff, 'is_optimal': is_shortest,
            'weather': weather_info, 'tags': tags, 
            'instructions': route.get('instructions', []),
            'summary': route.get('summary', 'Alternative Route')
        })
        scored_routes.append(route)
    
    scored_routes.sort(key=lambda x: x['final_score'], reverse=True)
    return scored_routes