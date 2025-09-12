# All comments, variable names, and API outputs are in English as requested.
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import time
import requests
import ee

# Import our ultimate, robust GEE functions module
# Ensure 'gee_functions_professional.py' (the ultimate "defensive programming" version) is in the same directory.
import gee_functions_professional as gee_pro

# --- API Models ---

class OnClickAnalysisRequest(BaseModel):
    lat: float = Field(..., example=5.95)
    lon: float = Field(..., example=102.25)
    buffer_degree: Optional[float] = Field(0.05)

class AnalysisTask(BaseModel):
    """
    [V7.1 Fix] Added request_data to ensure locationName can be passed through the API response.
    The model is now robust for all task states (PENDING, RUNNING, COMPLETED, FAILED).
    """
    task_id: str
    status: str
    submitted_at: float
    request_data: Dict[str, Any]
    completed_at: Optional[float] = None
    result: Optional[dict] = None

class AnalysisSubmitResponse(BaseModel):
    message: str
    task_id: str
    status_endpoint: str

# --- In-memory Task Storage ---
TASKS: Dict[str, Dict] = {}

# --- [V7.1] Core Backend Logic ---
def get_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Gets 7-day daily and hourly weather forecast from Open-Meteo API.
    """
    try:
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,weathercode",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,windspeed_10m_max",
            "timezone": "Asia/Kuala_Lumpur"
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_risk_assessment_hypothesis(historical_analysis: Dict, forecast_data: Dict) -> Dict:
    """
    Fuses historical vulnerability (from SAR) with future weather threats (from forecast)
    to generate an explainable risk assessment. This is a rule-based XAI engine.
    """
    risk_level, confidence, primary_cause = "Low", "Medium", "No significant threats identified."
    historical_flood_area = historical_analysis.get("area_sq_km", 0)
    
    if not forecast_data.get("success"):
        risk_level, primary_cause = "Indeterminate", "Could not retrieve weather forecast data."
    else:
        daily_forecast = forecast_data["data"]["daily"]
        precip_3_days = sum(daily_forecast.get("precipitation_sum", [0])[:3])
        prob_3_days = max(daily_forecast.get("precipitation_probability_max", [0])[:3])
        
        if historical_flood_area > 1.0 and precip_3_days > 50 and prob_3_days > 70:
            risk_level, confidence, primary_cause = "High", "High", f"Area is historically vulnerable (recent flood of {historical_flood_area:.2f} sq km). Forecast predicts significant rainfall ({precip_3_days:.1f} mm over 3 days) with high probability ({prob_3_days}%)."
        elif precip_3_days > 80 and prob_3_days > 75:
            risk_level, confidence, primary_cause = "Medium", "High", f"Area may not be recently flooded, but the upcoming weather forecast predicts very heavy rainfall ({precip_3_days:.1f} mm over 3 days)."
        elif historical_flood_area > 1.0 and precip_3_days > 20:
            risk_level, confidence, primary_cause = "Medium", "Medium", "Area is historically vulnerable. While the forecast rainfall is moderate, it may be sufficient to trigger localized flooding."
        else:
            primary_cause = f"No significant recent flooding detected and forecast rainfall is low ({precip_3_days:.1f} mm over 3 days)."
            
    return {"risk_level": risk_level, "confidence": confidence, "summary": f"The flood risk for the next 3-5 days is assessed as **{risk_level}**.", "evidence": {"historical_vulnerability": f"Analysis of the past 90 days shows a maximum flood extent of {historical_flood_area:.2f} sq km.", "future_threat": primary_cause}}

def run_on_click_analysis_task(task_id: str, request: OnClickAnalysisRequest):
    """
    The ultimate background task runner that dynamically creates an AOI from a point,
    runs SAR analysis, gets weather forecast, and fuses them into a risk assessment.
    """
    TASKS[task_id]['status'] = "RUNNING"
    try:
        request_data = request.dict()
        lat, lon, buffer = request_data['lat'], request_data['lon'], request_data['buffer_degree']
        
        clicked_point = ee.Geometry.Point([lon, lat])
        analysis_geometry = clicked_point.buffer(buffer * 111320).bounds()
        
        today = datetime.utcnow()
        analysis_date = (today - timedelta(days=15)).strftime('%Y-%m-%d')
        
        gee_results = gee_pro.analyze_flood_ultimate(geometry=analysis_geometry, analysis_date=analysis_date, before_days=90, after_days=15)
        historical_flood_mask = gee_results['final_flood_mask']
        historical_area_km2 = gee_pro.get_area_stats(historical_flood_mask, analysis_geometry) / 1_000_000
        historical_tile_url = gee_pro.get_tile_url(historical_flood_mask, {'palette': ['#0000FF'], 'min': 0, 'max': 1})
        
        historical_analysis = {"area_sq_km": round(historical_area_km2, 2), "tile_url": historical_tile_url}
        forecast_data = get_weather_forecast(lat, lon)
        risk_assessment = generate_risk_assessment_hypothesis(historical_analysis, forecast_data)
        
        result_payload = {"risk_assessment": risk_assessment, "historical_context": historical_analysis, "weather_forecast": forecast_data, "analyzed_geojson": analysis_geometry.getInfo()}
        
        TASKS[task_id]['status'] = "COMPLETED"
        TASKS[task_id]['result'] = result_payload
        TASKS[task_id]['completed_at'] = time.time()
        
    except Exception as e:
        TASKS[task_id]['status'] = "FAILED"
        TASKS[task_id]['result'] = {"error": f"Backend task failed: {type(e).__name__} - {str(e)}"}
        TASKS[task_id]['completed_at'] = time.time()

# --- FastAPI App & Routes (V7.1) ---
app = FastAPI(title="Dynamic Interactive SAR-Weather Analysis API", version="7.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Dynamic Interactive Analysis API! See /docs for details."}

@app.post("/api/v7/analyze_on_click", response_model=AnalysisSubmitResponse, status_code=202, tags=["Interactive Analysis"])
async def submit_on_click_analysis(request: OnClickAnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"task_id": task_id, "status": "PENDING", "submitted_at": time.time(), "request_data": request.dict(), "result": None, "completed_at": None}
    background_tasks.add_task(run_on_click_analysis_task, task_id, request)
    return {"message": "Dynamic analysis task submitted successfully for the clicked location.", "task_id": task_id, "status_endpoint": f"/api/v7/tasks/{task_id}"}

@app.get("/api/v7/tasks/{task_id}", response_model=AnalysisTask, tags=["Interactive Analysis"])
def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task ID '{task_id}' not found.")
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_professional:app", host="0.0.0.0", port=8000, reload=True)