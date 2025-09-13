# SAR-Weather Risk Explorer: A Dynamic Earth Observation Platform

[![NASA Space Apps 2025](https://img.shields.io/badge/NASA%20Space%20Apps-Sarawak%202025-blue.svg)](https://www.spaceappschallenge.org/)
[![Challenge](https://img.shields.io/badge/Challenge-Through%20the%20Radar%20Looking%20Glass-green.svg)](https://www.spaceappschallenge.org/2024/challenges/through-the-radar-looking-glass-revealing-earth-processes-with-sar/)

An interactive, real-time platform designed to assess flood risk by intelligently fusing historical SAR (Synthetic Aperture Radar) data with live weather forecasts. This project is a submission for the **NASA Space Apps Sarawak 2025** event.

Inspired by the immersive experience of professional meteorological platforms like Windy.com, this tool goes a step further. It integrates a unique **Historical Vulnerability Index** calculated on-demand from Sentinel-1 SAR data, providing an unparalleled layer of explainable insight (XAI) into localized flood risk.

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Live Demo & Screenshots](#-live-demo--screenshots)
- [How to Run (For Developers)](#-how-to-run-for-developers)
- [Our Team](#-our-team)

---

## 📌 The Problem

Traditional flood monitoring relies on historical data or optical satellites, which are often obscured by clouds during critical weather events. Furthermore, assessing future flood risk requires a complex understanding of both an area's inherent vulnerability and the upcoming weather threats. There is a need for a tool that can fuse these two dimensions into a single, understandable, and actionable insight, accessible to everyone from citizens to disaster response teams.

---

## 💡 Our Solution

The **SAR-Weather Risk Explorer** is a web-based platform that transforms complex geospatial and meteorological data into an intuitive, interactive experience. Our core innovation is a two-pronged analysis approach:

1.  **Retrospective Vulnerability Analysis (The "Why"):** We use Google Earth Engine to perform on-the-fly analysis of 90 days of historical **Sentinel-1 SAR data**. This allows us to cut through clouds and rain to calculate a quantitative "Historical Vulnerability Index" for any location, showing how prone it is to flooding based on recent ground conditions.

2.  **Predictive Threat Analysis (The "What's Next"):** We integrate real-time weather forecast APIs (OpenWeatherMap, Open-Meteo) to fetch the next 7 days of detailed weather predictions (precipitation, temperature, wind).

An **Explainable AI (XAI) Engine** then fuses these two analyses to produce a clear, evidence-based risk assessment (Low, Medium, High) with a detailed explanation of the contributing factors.

---

## ✨ Key Features

- **🌍 Global On-Demand Analysis:** Click anywhere on the map or search for any location to get an instant, localized risk assessment.
- **🛰️ SAR-Powered Vulnerability:** Automatically analyzes 90 days of historical Sentinel-1 SAR data to determine an area's recent vulnerability to flooding.
- **🌦️ Real-time Weather Integration:** Fuses SAR analysis with a 7-day weather forecast from multiple sources.
- **🧠 Explainable AI (XAI) Engine:** A rule-based engine provides a clear, evidence-based summary explaining *why* the risk is assessed as Low, Medium, or High.
- **🎨 Immersive UI/UX:** A full-screen, dark-themed map interface with floating panels, inspired by professional meteorological platforms.
- **📡 Multi-Layer Data Exploration:** Dynamically toggle between live weather radar (from RainViewer), forecast layers (wind, precipitation, temp), and our unique historical SAR flood analysis.
- **👆 Interactive & Intuitive:** Designed for both experts and the general public, with a "point-and-click" interface that requires no prior GIS knowledge.

---

## 🏗️ System Architecture

Our platform is built on a modern, decoupled architecture:

 <!-- 建议您创建一个简单的流程图并替换此链接 -->

1.  **Frontend (`index.html`):** A lightweight Vanilla JS application using Leaflet.js for mapping. It handles user interactions (clicks, searches) and visualizes data from both our backend and external APIs.
2.  **Backend (`main_professional.py`):** A high-performance FastAPI server that acts as the central brain. It receives requests, dynamically creates Areas of Interest (AOI), and orchestrates the analysis.
3.  **Geospatial Engine (Google Earth Engine):** The heavy-lifting is delegated to GEE's powerful cloud infrastructure for all SAR data processing and analysis.
4.  **External Data APIs:** We enrich our analysis with real-time data from OpenWeatherMap (forecasts, temperatures), RainViewer (live radar), and Nominatim (geocoding).

---

## 🛠️ Technology Stack

- **Backend:**
  - **Framework:** Python, FastAPI
  - **Geospatial Analysis:** Google Earth Engine (GEE) Python API
- **Frontend:**
  - **Core:** HTML5, CSS3, Vanilla JavaScript (ES6)
  - **Mapping Library:** Leaflet.js
- **Data Sources:**
  - **SAR:** NASA/ESA Sentinel-1
  - **Weather Forecast & Live Data:** OpenWeatherMap, Open-Meteo, RainViewer
  - **Geocoding:** Nominatim (OpenStreetMap)

---

## 🎬 Live Demo & Screenshots

*(在这里嵌入您的演示视频链接和几张最精彩的截图)*

**[Link to our Demo Video on YouTube]**

| Feature | Screenshot |
| :--- | :--- |
| **Initial Exploration View** |  |
| **On-Demand Analysis Result** |  |
| **Live Radar Layer** |  |

---

## 🚀 How to Run (For Developers)

This project is structured into a `backend` and `frontend` directory.

### Backend Setup

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a Python virtual environment:
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Crucial Step:** Authenticate with Google Earth Engine. This is a one-time setup that links your Google account.
    ```bash
    earthengine authenticate
    ```
    Follow the on-screen instructions in your browser. You will also need to enable the "Earth Engine API" in your Google Cloud project as prompted.

5.  Run the FastAPI server:
    ```bash
    uvicorn main_professional:app --reload
    ```
    - The backend will now be running at `http://127.0.0.1:8000`.

### Frontend Setup

1.  Navigate to the `frontend` directory.
2.  **Crucial Step:** You need a free API key from [OpenWeatherMap](https://openweathermap.org/appid) to enable the live weather layers and temperature data.
3.  Open the `index.html` file in a text editor.
4.  Find the line `const OWM_API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY';`
5.  Replace `'YOUR_OPENWEATHERMAP_API_KEY'` with your actual key.
6.  Save the file and open `index.html` in your favorite web browser. The application should now be fully functional.

---

## 👥 Our Team

- **Chiu Siew Seng (Andrew) / Team Miracle** - Team Leader, Lead Developer, AI Developer, Frontend & Backend Developer
