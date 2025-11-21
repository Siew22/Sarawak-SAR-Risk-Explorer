# main_professional.py

# ==========================================================================
#
#   main_professional.py - SUPER APP FINAL & COMPLETE VERSION
#
#   This file integrates BOTH the original NASA Geo-Intel logic and the
#   new, GPS-optimized JalanSafe AI logic into a single backend server.
#   NO CODE HAS BEEN OMITTED.
#
# ==========================================================================

# --- Core Python Libraries ---
import os
import shutil
import uuid
import time
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import traceback

# --- FastAPI, SQLAlchemy & Pydantic Libraries ---
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse # <--- 新增引用

# --- Project-Specific Modules (Both Projects) ---
try:
    import gee_functions_professional as gee_pro
    import ee
    print("Geo-Intel Module: Google Earth Engine loaded successfully.")
except Exception as e:
    print(f"CRITICAL WARNING: Geo-Intel module failed to load. Error: {e}")
    gee_pro = ee = None

try:
    import crud, models, schemas, services
    from schemas import ReportTypeEnum
    from database import engine, get_db
    print("JalanSafe AI Module: Database and services loaded successfully.")
except ImportError as e:
    print(f"CRITICAL WARNING: JalanSafe AI modules failed to load. Error: {e}")
    crud = models = schemas = services = engine = get_db = None

# ==========================================================================
# --- DATABASE INITIALIZATION for JalanSafe AI ---
# ==========================================================================
if models and engine:
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database tables for JalanSafe AI checked/created successfully.")
    except Exception as e:
        print(f"CRITICAL ERROR: DB connection/table creation failed. Error: {e}")

# ==========================================================================
# --- FASTAPI APPLICATION SETUP ---
# ==========================================================================
app = FastAPI(title="JalanSafe & SAR Risk Explorer SUPER APP", version="3.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================================================
# --- NASA GEO-INTEL MODULE (COMPLETE & UNOMITTED) ---
# ==========================================================================

class OnClickAnalysisRequest(BaseModel):
    lat: float; lon: float; analysis_type: str; buffer_degree: Optional[float] = Field(0.1)

class AnalysisTask(BaseModel):
    task_id: str; status: str; submitted_at: float; request_data: Dict[str, Any]
    completed_at: Optional[float] = None; result: Optional[dict] = None

class AnalysisSubmitResponse(BaseModel):
    message: str; task_id: str; status_endpoint: str

TASKS: Dict[str, Dict] = {}

def get_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:
    try:
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon, "hourly": "temperature_2m,weathercode", "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,windspeed_10m_max", "timezone": "Asia/Kuala_Lumpur"}
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_risk_assessment_hypothesis(h_ana: Dict, f_data: Dict) -> Dict:
    risk, conf, cause = "Low", "Medium", "No significant threats identified."
    h_area = h_ana.get("area_sq_km", 0)
    if not f_data.get("success"):
        risk, cause = "Indeterminate", "Could not retrieve weather forecast data."
    else:
        d_cast = f_data["data"]["daily"]
        p_3d = sum(d_cast.get("precipitation_sum", [0])[:3])
        prob_3d = max(d_cast.get("precipitation_probability_max", [0])[:3])
        if h_area > 1.0 and p_3d > 50 and prob_3d > 70:
            risk, conf, cause = "High", "High", f"Area is historically vulnerable ({h_area:.2f} sq km). Forecast predicts significant rainfall ({p_3d:.1f} mm over 3 days) with high probability ({prob_3d}%)."
        elif p_3d > 80 and prob_3d > 75:
            risk, conf, cause = "Medium", "High", f"Area may not be recently flooded, but upcoming weather predicts very heavy rainfall ({p_3d:.1f} mm over 3 days)."
        elif h_area > 1.0 and p_3d > 20:
            risk, conf, cause = "Medium", "Medium", f"Area is historically vulnerable. While forecast rainfall is moderate, it may trigger localized flooding."
        else: cause = f"No significant recent flooding detected and forecast rainfall is low ({p_3d:.1f} mm over 3 days)."
    return {"risk_level": risk, "confidence": conf, "summary": f"Flood risk for the next 3-5 days is assessed as **{risk}**.", "evidence": {"historical_vulnerability": f"Analysis of the past 90 days shows a maximum flood extent of {h_area:.2f} sq km.", "future_threat": cause}}

def generate_deforestation_hypothesis(gee_res, geom, p1, p2):
    area_km2 = gee_pro.get_area_stats(gee_res, geom) / 1_000_000
    summary = f"Detected ~{area_km2:.2f} sq km of potential deforestation."
    if area_km2 < 0.1: summary = "No significant deforestation detected."
    story = {"title": "Deforestation Analysis", "summary": summary, "evidence": [{"indicator": "SAR & Optical Fusion", "finding": "Result based on drop in SAR backscatter and NDVI."}, {"indicator": "Comparison Period", "finding": f"Analyzed changes between {p1} and {p2}."}]}
    return {"story": story, "area_sq_km": round(area_km2, 2)}

def run_on_click_analysis_task(task_id: str, request: OnClickAnalysisRequest):
    TASKS[task_id]['status'] = "RUNNING"
    try:
        if not ee or not gee_pro: raise Exception("Google Earth Engine modules are not loaded.")
        r_data = request.dict()
        lat, lon, buffer, a_type = r_data['lat'], r_data['lon'], r_data['buffer_degree'], r_data['analysis_type']
        geom = ee.Geometry.Point([lon, lat]).buffer(buffer * 111320).bounds()
        res_payload = {}
        if a_type == 'flood':
            a_date = (datetime.utcnow() - timedelta(days=15)).strftime('%Y-%m-%d')
            gee_res = gee_pro.analyze_flood_ultimate(geometry=geom, analysis_date=a_date)
            h_mask = gee_res['final_flood_mask']
            h_area_km2 = gee_pro.get_area_stats(h_mask, geom) / 1_000_000
            h_ana, f_data = {"area_sq_km": h_area_km2}, get_weather_forecast(lat, lon)
            risk_ass = generate_risk_assessment_hypothesis(h_ana, f_data)
            res_payload = {"analysis_type": "flood", "risk_assessment": risk_ass, "historical_context": {"area_sq_km": round(h_area_km2, 2), "tile_url": gee_pro.get_tile_url(h_mask, {'palette': ['#0000FF'], 'min': 0, 'max': 1})}, "weather_forecast": f_data, "analyzed_geojson": geom.getInfo()}
        elif a_type == 'deforestation':
            today = datetime.utcnow()
            e_r, s_r = today.strftime('%Y-%m-%d'), (today - timedelta(days=90)).strftime('%Y-%m-%d')
            e_h, s_h = (today - timedelta(days=365)).strftime('%Y-%m-%d'), (today - timedelta(days=365 + 90)).strftime('%Y-%m-%d')
            gee_mask = gee_pro.analyze_deforestation_between_periods(geometry=geom, start_date_period1=s_h, end_date_period1=e_h, start_date_period2=s_r, end_date_period2=e_r)
            hypo_data = generate_deforestation_hypothesis(gee_mask, geom, f"~{s_h}", f"~{e_r}")
            res_payload = {"analysis_type": "deforestation", "analysis_report": hypo_data, "deforestation_context": {"area_sq_km": hypo_data['area_sq_km'], "tile_url": gee_pro.get_tile_url(gee_mask, {'palette': ['#FF0000'], 'min': 0, 'max': 1})}, "analyzed_geojson": geom.getInfo()}
        TASKS[task_id].update({"status": "COMPLETED", "result": res_payload, "completed_at": time.time()})
    except Exception as e:
        print(f"ERROR in GEE Task: {traceback.format_exc()}")
        TASKS[task_id].update({"status": "FAILED", "result": {"error": str(e)}, "completed_at": time.time()})

# ==========================================================================
# --- API ENDPOINTS ---
# ==========================================================================

@app.get("/", tags=["System"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Super App API v3.3.0"}

# --- NASA Geo-Intel API Endpoints ---
@app.post("/api/v9/analyze", response_model=AnalysisSubmitResponse, status_code=202, tags=["NASA Geo-Intel Analysis"])
async def submit_analysis(request: OnClickAnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"task_id": task_id, "status": "PENDING", "submitted_at": time.time(), "request_data": request.dict()}
    background_tasks.add_task(run_on_click_analysis_task, task_id, request)
    return {"message": "Smart analysis task submitted successfully.", "task_id": task_id, "status_endpoint": f"/api/v9/tasks/{task_id}"}

@app.get("/api/v9/tasks/{task_id}", response_model=AnalysisTask, tags=["NASA Geo-Intel Analysis"])
def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task: raise HTTPException(status_code=404, detail=f"Task ID '{task_id}' not found.")
    return task

# --- JalanSafe AI API Endpoints ---
@app.post("/api/v1/routes/from-current-location", response_model=List[schemas.RouteResult], tags=["JalanSafe AI - Routing"])
def get_smart_routes_from_gps(request: schemas.RouteRequestWithStartCoords, db: Session = Depends(get_db)):
    start_point = schemas.Point(lat=request.start_lat, lon=request.start_lon)
    end_point = services.geocode_location(request.end_name)
    if not end_point:
        raise HTTPException(status_code=404, detail=f"Could not find a location for destination: '{request.end_name}'.")
    
    routes = services.get_multiple_routes_with_fallback(start_point, end_point)
    
    if not routes:
        raise HTTPException(status_code=404, detail="No routes could be found. The destination may be too far or unreachable by car.")
        
    smart_routes = services.calculate_ai_smart_routes(routes, db)
    return smart_routes

@app.post("/api/v1/routes/by-name", response_model=List[schemas.RouteResult], tags=["JalanSafe AI - Routing"])
def get_smart_routes_by_name(request: schemas.RouteRequestByName, db: Session = Depends(get_db)):
    proximity = None
    if request.current_lat is not None and request.current_lon is not None:
        proximity = schemas.Point(lat=request.current_lat, lon=request.current_lon)

    start_point = services.geocode_location(request.start_name, proximity_point=proximity)
    end_point = services.geocode_location(request.end_name, proximity_point=proximity)
    
    if not start_point or not end_point:
        raise HTTPException(status_code=404, detail="Could not geocode one or both locations.")
        
    routes = services.get_multiple_routes_with_fallback(start_point, end_point)
    
    if not routes: 
        raise HTTPException(status_code=404, detail="No route could be found, even with the primary routing service.")
        
    smart_routes = services.calculate_ai_smart_routes(routes, db) 
    return smart_routes

@app.post("/api/v1/reports", response_model=schemas.Report, status_code=201, tags=["JalanSafe AI - Contribution"])
async def create_new_report(db: Session = Depends(get_db), photo: UploadFile = File(...), user_id: int = Form(...), latitude: float = Form(...), longitude: float = Form(...), report_type: ReportTypeEnum = Form(...), description: str = Form(...)):
    upload_dir = "uploads"; os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(photo.filename)[1]
    unique_fn = f"{user_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
    file_path = os.path.join(upload_dir, unique_fn)
    with open(file_path, "wb") as buffer: shutil.copyfileobj(photo.file, buffer)
    report_data = schemas.ReportCreate(user_id=user_id, latitude=latitude, longitude=longitude, report_type=report_type, description=description, photo_url=file_path)
    return crud.create_report(db=db, report=report_data)

@app.post("/api/v1/reports/{report_id}/comments", response_model=schemas.Comment, status_code=201, tags=["JalanSafe AI - Contribution"])
def create_new_comment(report_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    if crud.get_comment_count(db=db, report_id=report_id) >= 10:
        raise HTTPException(status_code=403, detail="Maximum number of comments (10) reached.")
    crud.update_report_score_based_on_comment(db, report_id, comment.vote)
    return crud.create_comment(db=db, comment=comment, report_id=report_id)

@app.get("/api/v1/rank", response_model=List[schemas.UserRank], tags=["JalanSafe AI - Contribution"])
def get_leaderboard(db: Session = Depends(get_db)):
    return crud.get_user_rankings(db=db)

@app.post("/api/v1/routes/choose", response_model=schemas.RouteChoiceCreate, tags=["JalanSafe AI - User Interaction"])
def choose_route(choice: schemas.RouteChoiceCreate, db: Session = Depends(get_db)):
    print(f"User {choice.user_id} chose route with hash: {choice.chosen_route_hash}")
    return crud.create_route_choice(db=db, choice=choice)

@app.post("/api/v1/users", response_model=schemas.User, status_code=201, tags=["User Management"])
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/api/v1/reports", response_model=List[schemas.Report], tags=["JalanSafe AI - Data"])
def get_all_reports(db: Session = Depends(get_db)):
    return db.query(models.Report).order_by(models.Report.created_at.desc()).all()

@app.get("/api/v1/reports/{report_id}/comments", response_model=List[schemas.Comment], tags=["JalanSafe AI - Contribution"])
def get_comments(report_id: int, db: Session = Depends(get_db)):
    return crud.get_comments_for_report(db, report_id=report_id)

@app.get("/", response_class=FileResponse) # <--- 修改这里
async def read_root():
    return "static/index.html" # <--- 让 APP 打开就看到地图

class TrafficSimulationRequest(BaseModel):
    route_hash: str
    count: int

@app.post("/api/v1/simulate/traffic", tags=["Demo Tools"])
def simulate_traffic(req: TrafficSimulationRequest, db: Session = Depends(get_db)):
    """
    Demo Tool: Instantly adds 'count' fake users to a specific route to simulate congestion.
    """
    for _ in range(req.count):
        # Use user_id 999 for simulated traffic bots
        fake_choice = models.RouteChoice(user_id=999, chosen_route_hash=req.route_hash)
        db.add(fake_choice)
    db.commit()
    return {"message": f"Successfully injected {req.count} fake users onto route {req.route_hash[:8]}..."}

class ClearTrafficRequest(BaseModel):
    route_hash: str

@app.post("/api/v1/simulate/clear_traffic", tags=["Demo Tools"])
def clear_traffic(req: ClearTrafficRequest, db: Session = Depends(get_db)):
    """
    Demo Tool: Instantly clears all traffic records for a route.
    Simulates that users have passed the road and it is now clear.
    """
    db.query(models.RouteChoice).filter(
        models.RouteChoice.chosen_route_hash == req.route_hash
    ).delete()
    db.commit()
    return {"message": f"Traffic cleared for route {req.route_hash[:8]}..."}

# --- Main App Runner ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_professional:app", host="0.0.0.0", port=8000, reload=True)