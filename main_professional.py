# All comments, variable names, and API outputs are in English as requested.
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import uuid
import time
import requests
import ee


# Ensure 'gee_functions_professional.py' (the ultimate dual-core version) is in the same directory.
import gee_functions_professional as gee_pro

# --- [V9] Final API Models - Simplified for better UX ---
class OnClickAnalysisRequest(BaseModel):
    lat: float = Field(..., example=1.557)
    lon: float = Field(..., example=110.35)
    analysis_type: str = Field(..., example="flood", description="Type of analysis: 'flood' or 'deforestation'")
    buffer_degree: Optional[float] = Field(0.1)

class AnalysisTask(BaseModel):
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

# --- Helper Functions (Weather & XAI) ---
def get_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:
    try:
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
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

def generate_deforestation_hypothesis(gee_result, geometry, period1_str, period2_str):
    deforestation_area_km2 = gee_pro.get_area_stats(gee_result, geometry) / 1_000_000
    summary = f"Detected approximately {deforestation_area_km2:.2f} sq km of potential deforestation."
    if deforestation_area_km2 < 0.1:
        summary = "No significant deforestation detected when comparing the two periods."
    story = {
        "title": "Deforestation 'Then vs. Now' Analysis", "confidence": "High",
        "summary": summary,
        "evidence": [
            {"indicator": "SAR & Optical Fusion", "finding": "Result based on a drop in both SAR backscatter (surface roughness) and NDVI (vegetation health)."},
            {"indicator": "Comparison Period", "finding": f"Analyzed changes between a historical baseline ({period1_str}) and the recent period ({period2_str})."},
        ],
        "next_steps": "Recommend cross-validation with high-resolution imagery or field reports."
    }
    return {"story": story, "area_sq_km": round(deforestation_area_km2, 2)}

# --- [V9] Ultimate Background Task Runner with Smart "Then vs Now" Logic ---
def run_on_click_analysis_task(task_id: str, request: OnClickAnalysisRequest):
    TASKS[task_id]['status'] = "RUNNING"
    try:
        request_data = request.dict()
        lat, lon, buffer = request_data['lat'], request_data['lon'], request_data['buffer_degree']
        analysis_type = request_data['analysis_type']
        
        clicked_point = ee.Geometry.Point([lon, lat])
        analysis_geometry = clicked_point.buffer(buffer * 111320).bounds()
        
        result_payload = {}

        if analysis_type == 'flood':
            today = datetime.utcnow()
            analysis_date = (today - timedelta(days=15)).strftime('%Y-%m-%d')
            gee_results = gee_pro.analyze_flood_ultimate(geometry=analysis_geometry, analysis_date=analysis_date)
            
            historical_flood_mask = gee_results['final_flood_mask']
            historical_area_km2 = gee_pro.get_area_stats(historical_flood_mask, analysis_geometry) / 1_000_000
            
            historical_analysis = {"area_sq_km": historical_area_km2}
            forecast_data = get_weather_forecast(lat, lon)
            risk_assessment = generate_risk_assessment_hypothesis(historical_analysis, forecast_data)

            result_payload = {
                "analysis_type": "flood",
                "risk_assessment": risk_assessment,
                "historical_context": {
                    "area_sq_km": round(historical_area_km2, 2),
                    "tile_url": gee_pro.get_tile_url(historical_flood_mask, {'palette': ['#0000FF'], 'min': 0, 'max': 1})
                },
                "weather_forecast": forecast_data,
                "analyzed_geojson": analysis_geometry.getInfo()
            }

        elif analysis_type == 'deforestation':
            today = datetime.utcnow()
            end_date_recent = today.strftime('%Y-%m-%d')
            start_date_recent = (today - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date_historical = (today - timedelta(days=365)).strftime('%Y-%m-%d')
            start_date_historical = (today - timedelta(days=365 + 90)).strftime('%Y-%m-%d')
            
            gee_results_mask = gee_pro.analyze_deforestation_between_periods(
                geometry=analysis_geometry,
                start_date_period1=start_date_historical,
                end_date_period1=end_date_historical,
                start_date_period2=start_date_recent,
                end_date_period2=end_date_recent
            )
            
            hypothesis_data = generate_deforestation_hypothesis(
                gee_results_mask,
                analysis_geometry,
                f"~{start_date_historical}",
                f"~{end_date_recent}"
            )

            result_payload = {
                "analysis_type": "deforestation",
                "analysis_report": hypothesis_data,
                "deforestation_context": {
                    "area_sq_km": hypothesis_data['area_sq_km'],
                    "tile_url": gee_pro.get_tile_url(gee_results_mask, {'palette': ['#FF0000'], 'min': 0, 'max': 1})
                },
                "analyzed_geojson": analysis_geometry.getInfo()
            }

        TASKS[task_id]['status'] = "COMPLETED"
        TASKS[task_id]['result'] = result_payload
        TASKS[task_id]['completed_at'] = time.time()

    except Exception as e:
        TASKS[task_id]['status'] = "FAILED"
        TASKS[task_id]['result'] = {"error": f"Backend task failed: {type(e).__name__} - {str(e)}"}
        TASKS[task_id]['completed_at'] = time.time()

# --- FastAPI App & Routes (V9) ---
app = FastAPI(title="Smart 'Then vs Now' Analysis API", version="10.0.0")
allowed_origin = os.getenv("VERCEL_URL", "http://localhost:3000") # Default for local dev
origins = [
    "http://localhost",
    "http://localhost:8080",
    # This is your main production URL
    "https://sarawak-sar-risk-explorer.vercel.app", 
    # This is the specific Git branch deployment URL, also good to include
    "https://sarawak-sar-risk-explorer-git-main-chiu-siew-sengs-projects.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow requests from ANY origin
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Smart Analysis API! See /docs for details."}

@app.post("/api/v9/analyze", response_model=AnalysisSubmitResponse, status_code=202, tags=["Interactive Analysis"])
async def submit_analysis(request: OnClickAnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"task_id": task_id, "status": "PENDING", "submitted_at": time.time(), "request_data": request.dict(), "result": None, "completed_at": None}
    background_tasks.add_task(run_on_click_analysis_task, task_id, request)
    return {"message": "Smart analysis task submitted successfully.", "task_id": task_id, "status_endpoint": f"/api/v9/tasks/{task_id}"}

@app.get("/api/v9/tasks/{task_id}", response_model=AnalysisTask, tags=["Interactive Analysis"])
def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task ID '{task_id}' not found.")
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_professional:app", host="0.0.0.0", port=8000, reload=True)