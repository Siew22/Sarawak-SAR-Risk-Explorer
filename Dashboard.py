import streamlit as st
import pandas as pd
from database import engine
from sqlalchemy import text
import os
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. 页面配置
st.set_page_config(page_title="SRAMS Command Center", page_icon="📡", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="datarefresher")

# 2. CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    h1, h2, h3 { color: #4ea8de !important; }
    div[data-testid="stMetric"] { background-color: #1f2937; padding: 15px; border-radius: 8px; border-left: 5px solid #0d6efd; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2.5em; }
    div[data-testid="stMetricLabel"] { white-space: normal !important; font-size: 0.9em !important; color: #9ca3af !important; }
    iframe {
        border-radius: 10px;
        border: 2px solid #374151;
        sandbox: "allow-scripts allow-popups allow-forms allow-same-origin";
    }
</style>
""", unsafe_allow_html=True)

# 3. 标题
st.title("📡 SRAMS Digital Command Center")
st.caption("Live Feed from JalanSafe AI Database | Auto-refreshes every 30 seconds")

# 4. 加载数据
@st.cache_data(ttl=10)
def load_data():
    try:
        query = "SELECT * FROM reports ORDER BY created_at DESC"
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
        return df
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()
df = load_data()

# 侧边栏
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=100)
    st.header("Admin Controls")
    st.subheader("💰 Cost Analysis Model")
    cost_per_pothole = st.slider("Cost per Pothole (RM)", 100, 1000, 200, step=50)
    cost_per_traffic = st.slider("Cost per Signal Fault (RM)", 200, 2000, 500, step=100)
    st.markdown("---")
    st.subheader("📸 Evidence Viewer")
    st.caption("Click a marker on the map to view details here.")
    details_placeholder = st.container()
    if 'selected_report_id' in st.session_state and not df.empty and st.session_state.selected_report_id is not None:
        selected_report_df = df[df['id'] == st.session_state.selected_report_id]
        if not selected_report_df.empty:
            selected_report = selected_report_df.iloc[0]
            with details_placeholder:
                st.info(f"**Viewing Report #{selected_report['id']}**")
                st.write(f"**Description:** {selected_report['description']}")
                if selected_report['photo_url']:
                    clean_path = selected_report['photo_url'].replace("\\", "/")
                    if os.path.exists(clean_path):
                        st.image(clean_path, caption="Evidence Photo")
    else:
        details_placeholder.info("No report selected.")

# ==========================================
# 🔥 核心修复：把主面板内容全部放进一个 container 里
# ==========================================
main_container = st.container()

with main_container:
    # KPI 指标
    if not df.empty:
        total_reports = len(df)
        pothole_count = len(df[df['report_type'] == 'road_condition'])
        traffic_count = len(df[df['report_type'] == 'traffic_light'])
        money_saved = (pothole_count * cost_per_pothole) + (traffic_count * cost_per_traffic)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Intelligence", f"{total_reports}", "Reports")
        c2.metric("Potholes", f"{pothole_count}", "Requires Action", delta_color="inverse")
        c3.metric("Signal Faults", f"{traffic_count}", "Urgent", delta_color="inverse")
        c4.metric("Est. OpEx Saved", f"RM {money_saved:,}", "Dynamic Model")
    else:
        st.info("System Online. Awaiting data...")

    st.markdown("---")

    # 地图
    st.subheader("🗺️ Geospatial Situation Room")
    if not df.empty:
        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=11, tiles="CartoDB dark_matter")
        for index, row in df.iterrows():
            tooltip_html = f"<b>ID: #{row['id']}</b> | Click to view evidence"
            folium.Marker(location=[row['latitude'], row['longitude']], tooltip=tooltip_html, icon=folium.Icon(color="red" if row['report_type'] == 'road_condition' else "orange", icon="exclamation-triangle", prefix='fa')).add_to(m)
        map_data = st_folium(m, width="100%", height=500, key="folium_map")
        if map_data and map_data["last_object_clicked_tooltip"]:
            try:
                report_id = int(map_data["last_object_clicked_tooltip"].split("#")[1].split("|")[0].strip())
                st.session_state.selected_report_id = report_id
                st.rerun()
            except (IndexError, ValueError):
                pass
    else:
        st.warning("No geospatial data.")

    # 分页图片墙
    st.markdown("---")
    st.subheader("📸 Incoming Evidence Stream")
    if not df.empty:
        PAGE_SIZE = 4
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        total_pages = (len(df) // PAGE_SIZE) + (1 if len(df) % PAGE_SIZE > 0 else 0)
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Previous", disabled=(st.session_state.current_page <= 1)):
                st.session_state.current_page -= 1
                st.rerun()
        with col_next:
            if st.button("Next ➡️", disabled=(st.session_state.current_page >= total_pages)):
                st.session_state.current_page += 1
                st.rerun()
        with col_page:
            st.write(f"**Page {st.session_state.current_page} of {total_pages}**")
        start_index = (st.session_state.current_page - 1) * PAGE_SIZE
        end_index = start_index + PAGE_SIZE
        page_df = df.iloc[start_index:end_index]
        cols = st.columns(PAGE_SIZE)
        for i, (index, row) in enumerate(page_df.iterrows()):
            with cols[i % PAGE_SIZE]:
                st.markdown(f"**ID: #{row['id']}** | <span style='color:gray'>{row['created_at']}</span>", unsafe_allow_html=True)
                if row['photo_url']:
                    clean_path = row['photo_url'].replace("\\", "/")
                    if os.path.exists(clean_path):
                        st.image(clean_path)
                        st.caption(f"📍 {row['latitude']}, {row['longitude']}")
                else:
                    st.error("Image file missing")