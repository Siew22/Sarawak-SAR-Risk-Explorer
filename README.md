# Global SAR-Weather Risk & Change Explorer

![NASA Space Apps 2025](https://img.shields.io/badge/NASA_Space_Apps-Sarawak_2025-blue)
![Challenge](https://img.shields.io/badge/Challenge-Through_the_Radar_Looking_Glass-green)
![Status](https://img.shields.io/badge/Status-Completed-success)

**A Windy.com-inspired, dual-core analysis platform that fuses historical SAR data with real-time weather to provide on-demand, explainable insights into global flood risks and deforestation.**

This project is a submission for the **"Through the Radar Looking Glass: Revealing Earth Processes with SAR"** challenge. We didn't just build a tool; we created an immersive exploration experience. Our platform empowers any user—from a concerned citizen to a policy maker—to click anywhere on Earth and instantly receive a sophisticated, AI-driven analysis of environmental changes and risks, explained in clear, simple terms.

---

## 🚀 Live Demo & Presentation

[![Project Demo GIF](https://github.com/user-attachments/assets/05b1853d-24ea-426b-8032-6a6c0e5a9172)](https://www.youtube.com/watch?v=dQw4w9WgXcQ) 
*Click the image above to watch a full video demonstration of our platform in action.*

---

## ✨ Core Features

Our platform is built on three foundational pillars: **On-Demand Analysis**, **Intelligent Fusion**, and **Immersive Experience**.

#### 🛰️ Dual-Core Analysis Engine
Seamlessly switch between two powerful, on-demand analysis modes with a single click:

*   **🌊 Flood Risk Assessment:**
    *   **Retrospective Analysis:** Utilizes 90 days of historical Sentinel-1 SAR data to calculate a quantitative **"Historical Vulnerability Index"** for the selected area.
    *   **Predictive Insight:** Fuses this vulnerability index with a 7-day weather forecast to generate a forward-looking, actionable risk level (Low, Medium, High).

*   **🌲 Deforestation "Then vs. Now" Watch:**
    *   **Zero-Input Intelligence:** Users no longer need to know *when* deforestation occurred. Our backend **intelligently compares** the last 3 months of satellite data against a historical baseline from the previous year.
    *   **Multi-Source Validation:** The algorithm confirms deforestation by detecting a drop in **both** SAR backscatter (indicating a change in surface roughness) and optical NDVI (indicating a loss of vegetation health), significantly reducing false positives.

#### 🧠 Explainable AI (XAI) Engine
We believe that data without explanation is just noise. Our XAI engine provides:
*   **Clear Narratives:** Every analysis is accompanied by a structured report with a clear title, confidence level, and a plain-language summary.
*   **Evidence-Based Reasoning:** The report breaks down *why* a conclusion was reached, citing specific evidence from SAR data, weather forecasts, and historical datasets.

#### 🎨 Immersive UI/UX Inspired by Windy.com
*   **Map as Interface:** A full-screen, dark-themed map is the heart of the application.
*   **Dynamic Data Layers:** A professional, always-visible right-side panel allows users to instantly toggle between multiple global data layers:
    *   **Live Weather Radar** (from RainViewer)
    *   **Forecast Layers** (Wind, Precipitation, Temp from OWM)
    *   **Our Unique SAR Analysis Results** (Flood or Deforestation)
*   **Interactive Controls:** Floating panels, an interactive forecast timeline, and seamless transitions create a fluid and engaging user experience.
*   **Live Global Data:** The map is populated with live temperature labels for major cities, making the world feel alive and data-rich from the moment you arrive.

---

## 🛠️ Technology Architecture

Our system is designed with a modern, decoupled architecture for scalability and robustness.

  
*<-- [可選] 如果您有時間，可以畫一張簡單的架構圖並替換此鏈接*

*   **Frontend (`dashboard_windy_final.html`):**
    *   **Core:** Built with pure **HTML5, CSS3, and Vanilla JavaScript (ES6)** for maximum performance and zero dependencies.
    *   **Mapping:** **Leaflet.js** for a lightweight, powerful interactive map.
    *   **Real-time Layers:** Dynamically integrates tile layers from **OpenWeatherMap** (forecasts) and **RainViewer** (live radar).

*   **Backend (`main_professional.py`):**
    *   **Framework:** A high-performance asynchronous API built with **Python 3.10** and **FastAPI**.
    *   **Geospatial Engine:** All heavy-duty satellite data processing is delegated to the **Google Earth Engine (GEE) Python API**, leveraging Google's planetary-scale computational power.
    *   **Asynchronous Tasks:** Analysis requests are handled as background tasks to ensure the API remains responsive.
    *   **API Endpoints:**
        *   `POST /api/v9/analyze`: The single, intelligent endpoint that receives a location and analysis type, and orchestrates the entire backend workflow.
        *   `GET /api/v9/tasks/{task_id}`: Allows the frontend to poll for the status and results of an analysis task.

---

## 🚀 How to Run Locally

### Prerequisites
*   Git
*   Python 3.10+
*   A Google Earth Engine enabled account

### Setup & Execution
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/[Your_Username]/[Your_Repo_Name].git
    cd [Your_Repo_Name]
    ```
2.  **Backend Setup:**
    ```bash
    cd backend
    python -m venv env
    .\env\Scripts\activate
    pip install -r requirements.txt
    earthengine authenticate
    uvicorn main_professional:app --reload
    ```
3.  **Frontend Setup:**
    *   Get a **free API key** from [OpenWeatherMap](https://openweathermap.org/appid).
    *   Open `frontend/index.html` in a text editor.
    *   Replace the placeholder `'YOUR_OPENWEATHERMAP_API_KEY'` with your actual key.
    *   Open the `index.html` file in your web browser.

---

## 🌟 Future Vision (Level 3)

While our current platform is a fully functional prototype, we have a clear vision for its evolution into a true AI-powered predictive engine:

1.  **Phase 1 - Automated Data Curation:** Develop a pipeline to systematically analyze decades of historical SAR and weather data, creating a massive, labeled dataset of weather events and their corresponding flood/deforestation outcomes.
2.  **Phase 2 - Predictive Model Training:** Train an **Adaptive Neuro-Fuzzy Inference System (ANFIS)** on this dataset. This model will learn the complex, non-linear relationships and be able to *predict* the probability and scale of a flood based purely on weather *forecast* data.
3.  **Phase 3 - AI Explainability with SHAP:** Integrate the **SHAP (SHapley Additive exPlanations)** library to make our AI model's predictions transparent. This will allow us to precisely quantify which forecast parameter (e.g., precipitation sum, wind speed) contributed most to a specific risk assessment, providing unparalleled, trustworthy insights for decision-makers.

---

## 👤 Team Members

*   Chiu Siew Seng/Miracle - Team Leader, Project Idea Owner and Floor Plan, AI Researcher/Developer, Frontend and Backend Developer, Lead Developer, and Data Scientist
