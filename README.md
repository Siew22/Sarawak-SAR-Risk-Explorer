# Global SAR-Weather Risk & Change Explorer

![NASA Space Apps 2025](https://img.shields.io/badge/NASA_Space_Apps-Sarawak_2025-blue?style=for-the-badge)
![Challenge](https://img.shields.io/badge/Challenge-Through_the_Radar_Looking_Glass-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)

**A Windy.com-inspired, dual-core analysis platform that fuses historical SAR data with real-time weather to provide on-demand, explainable insights into global flood risks and deforestation.**

This project is a submission for the **"Through the Radar Looking Glass: Revealing Earth Processes with SAR"** challenge. We didn't just build a tool; we created an immersive exploration experience. Our platform empowers any user—from a concerned citizen to a policy maker—to click anywhere on Earth and instantly receive a sophisticated, AI-driven analysis of environmental changes and risks, explained in clear, simple terms.

main_completely_framework_interface_platform_is_index.html_ya, the spare.html is just for my spare only ya, if you wanted to see also can.

---

## 🚀 Live Demo & Presentation

[![Project Demo GIF]([PASTE_YOUR_GIF_LINK_HERE])]([PASTE_A_LINK_TO_YOUR_YOUTUBE_DEMO_VIDEO_HERE]) 
*Click the image above to watch a full video demonstration of our platform in action.*

Access Public URL Website to Explore the Web App interface and function

[[https://sarawak-sar-risk-explorer.vercel.app/](https://sarawak-sar-risk-explorer-git-main-chiu-siew-sengs-projects.vercel.app?_vercel_share=6zALNX4ybJRtlfPFxprzTOHA4J8OKAUU)](https://sarawak-sar-risk-explorer.vercel.app/)

---

## Challenge Response Approach (Our Approach to the Challenge)

The "Through the Radar Looking Glass" challenge is not just about processing SAR data; it's a call to become a data detective. It asks us to solve riddles hidden within radar imagery, to hypothesize about the unseen forces shaping our planet, and to tell a compelling story with our findings. Our platform was architected from the ground up to answer these core questions.

#### **Challenge: "What can you hypothesize about the physical drivers behind what you see?"**

**Our Solution: An Explainable AI (XAI) Engine.** We moved beyond simple change detection. Our platform automatically fuses the **effect** (a flood detected by SAR) with its most likely **cause** (extreme precipitation from weather data). The result is an instant, evidence-based hypothesis generated for any location, such as: *"The flood risk is High because this area is historically vulnerable (proven by SAR) AND a significant rainfall event is forecasted (the physical driver)."*

#### **Challenge: "Can you tell the trees and the water apart? Can you detect how the forest is changing over time?"**

**Our Solution: A "Zero-Input" Dual-Core Analysis Engine.** We recognized that a user shouldn't need to be an expert to detect change.
*   **For Water:** Our multi-criteria flood algorithm intelligently distinguishes new floodwater from permanent water bodies using the JRC Global Surface Water dataset.
*   **For Forests:** Our "Deforestation" mode requires **no date input**. It smartly compares the most recent three months against the same period from the previous year, using both SAR (for structural change) and optical NDVI (for vegetation health) to robustly detect and quantify changes over time.

#### **Challenge: "How will you present your findings? Don't forget to focus on compelling storytelling..."**

**Our Solution: An Immersive, Interactive Data-Storytelling Platform.** We rejected static reports. Inspired by Windy.com, our platform turns every analysis into an interactive story.
*   **The Map is the Narrative:** Results are not just numbers in a box; they are living layers on a dynamic map.
*   **Context is King:** The user can instantly switch between our unique SAR analysis, live weather radar, and various forecast layers, exploring the full context of the story from every angle.
*   **The Story Unfolds On-Demand:** Every click on the map generates a new, unique story for that specific location, empowering users to become explorers of their own environment.

---

## ✨ Key Features

- **🛰️ Dual-Core Analysis Engine:** Seamlessly switch between Flood Risk Assessment and our intelligent "Then vs. Now" Deforestation Watch.
- **🌍 Global On-Demand & Interactive:** Click anywhere or search for any location to get an instant, localized analysis.
- **🧠 Explainable AI (XAI) Engine:** Every result is accompanied by a clear, evidence-based report.
- **🎨 Immersive UI/UX:** A full-screen, dark-themed map with floating panels and live global temperature data.
- **📡 Multi-Layer Data Exploration:** Instantly toggle between Live Weather Radar (RainViewer), weather forecasts (OWM), and our unique SAR analysis results.

---

## 🛠️ Technology Architecture

*   **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6), Leaflet.js
*   **Backend:** Python 3.10, FastAPI, Google Earth Engine (GEE) Python API
*   **Data Sources:** NASA/ESA Sentinel-1, OpenWeatherMap, Open-Meteo, Nominatim Geocoding, RainViewer

---

## 🧰 System Architecture Figure

<img width="3840" height="3107" alt="Untitled diagram _ Mermaid Chart-2025-09-24-050315" src="https://github.com/user-attachments/assets/51c67542-773d-43b4-8e4f-88caa1776284" />

## Core Analysis Flowchart Figure
<img width="1088" height="3840" alt="Untitled diagram _ Mermaid Chart-2025-09-24-050335" src="https://github.com/user-attachments/assets/cf747617-c999-47ae-b6c4-8f9e1cf3e45f" />

## 🚀 How to Run Locally

### Prerequisites
*   Git, Python 3.10+, A Google Earth Engine enabled account

### Setup & Execution
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/[Your_Username]/[Your_Repo_Name].git
    cd [Your_Repo_Name]
    ```
2.  **Backend Setup:**
    ```bash
    # (From the project root directory)
    python -m venv env
    .\env\Scripts\activate
    pip install -r requirements.txt
    earthengine authenticate
    uvicorn main_professional:app --reload
    ```
3.  **Frontend Setup:**
    *   Get a **free API key** from [OpenWeatherMap](https://openweathermap.org/appid).
    *   Open `dashboard_windy_final.html` in a text editor.
    *   Replace `'YOUR_OPENWEATHERMAP_API_KEY'` with your actual key.
    *   Open the `dashboard_windy_final.html` file in your web browser.

---

## 🌟 Future Vision (Level 3)

Our current platform is a fully functional prototype. Our vision is to evolve it into a true AI-powered predictive engine:
1.  **Phase 1 - Automated Data Curation:** Create a massive, labeled dataset of historical weather events and their corresponding SAR-detected outcomes.
2.  **Phase 2 - Predictive Model Training:** Train an **Adaptive Neuro-Fuzzy Inference System (ANFIS)** to predict flood scale based purely on weather *forecasts*.
3.  **Phase 3 - AI Explainability with SHAP:** Integrate **SHAP** to make our AI model's predictions transparent, quantifying the contribution of each weather parameter to the final risk score.

---

## 👤 Team Members

*   Chiu Siew Seng/Team Miracle - Team Leader, Project Idea and Floor Plan Owner, Frontend and Backend Developer, AI Developer and Researcher, and Lead Developer

## Acknowledgements
This project was made possible by the incredible open data provided by NASA, ESA (Copernicus), OpenWeatherMap, RainViewer, and OpenStreetMap.
