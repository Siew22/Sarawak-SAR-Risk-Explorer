# SAR-Weather Risk Explorer: A Dynamic Earth Observation Platform

## 🏆 Project for NASA Space Apps Sarawak 2025

This project is a submission for the **"Through the Radar Looking Glass: Revealing Earth Processes with SAR"** challenge. It is an interactive, real-time platform designed to assess flood risk by intelligently fusing historical SAR (Synthetic Aperture Radar) data with live weather forecasts.

Inspired by the immersive experience of professional meteorological platforms, this tool goes a step further by integrating a unique **Historical Vulnerability Index** calculated on-demand from Sentinel-1 SAR data, providing an unparalleled layer of explainable insight (XAI) into localized flood risk.

---

##  Key Features

- ** Global On-Demand Analysis:** Click anywhere on the map or search for any location to get an instant, localized risk assessment.
- ** SAR-Powered Vulnerability:** Automatically analyzes 90 days of historical Sentinel-1 SAR data to determine an area's recent vulnerability to flooding.
- ** Real-time Weather Integration:** Fuses SAR analysis with a 7-day weather forecast from multiple sources.
- ** Explainable AI (XAI) Engine:** A rule-based engine provides a clear, evidence-based summary explaining *why* the risk is assessed as Low, Medium, or High.
- ** Immersive UI/UX:** A full-screen, dark-themed map interface with floating panels and dynamic data layers.
- ** Multi-Layer Data Exploration:** Dynamically toggle between live weather radar (from RainViewer), forecast layers, and our unique historical SAR flood analysis.

---

##  Technology Stack

- **Backend:** Python, FastAPI, Google Earth Engine (GEE) Python API
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6), Leaflet.js
- **Data Sources:** NASA/ESA Sentinel-1, OpenWeatherMap, Open-Meteo, Nominatim, RainViewer

---

##  How to Run

### Backend Setup (main_professional.py)

1.  Create and activate a Python virtual environment (e.g., env).
2.  Install dependencies: pip install -r requirements.txt
3.  Authenticate with Google Earth Engine (one-time setup): earthengine authenticate
4.  Run the server: uvicorn main_professional:app --reload
    - The backend will be running at http://127.0.0.1:8000.

### Frontend Setup (map.html)

1.  Open the map.html file in your web browser.
2.  **[IMPORTANT]** You need to get a free API key from [OpenWeatherMap](https://openweathermap.org/appid) and paste it into the OWM_API_KEY constant inside the HTML file's <script> tag.

---

##  Team Members

- **[Your Name/Team Name]** - [Your Role, e.g., Lead Developer]
