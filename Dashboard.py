import streamlit as st
import pandas as pd
from database import engine
from sqlalchemy import text
import os
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import requests  # 🔥 新增：用于调用 API
import time      # 🔥 新增：用于时间戳

# ==========================================
# 0. 全局配置 & API 设置
# ==========================================
# ⚠️ 注意：这里要改成你的 FastAPI 后端地址
# 如果是在本地跑，通常是 http://127.0.0.1:8000/api/v1
# 如果上了云，就换成云端地址
API_BASE_URL = "http://127.0.0.1:8000/api/v1" 

st.set_page_config(page_title="SRAMS Command Center", page_icon="📡", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="datarefresher")

# ==========================================
# 1. 辅助函数：获取评论
# ==========================================
def fetch_report_comments(report_id):
    """从后端获取特定 Report 的评论数据"""
    try:
        # 加时间戳防止缓存
        url = f"{API_BASE_URL}/reports/{report_id}/comments?_t={int(time.time())}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        # 生产环境可以注释掉这行，免得报错太丑
        # st.error(f"API Error: {e}") 
        return []

# ==========================================
# 2. CSS 美化
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    h1, h2, h3 { color: #4ea8de !important; }
    div[data-testid="stMetric"] { background-color: #1f2937; padding: 15px; border-radius: 8px; border-left: 5px solid #0d6efd; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2.5em; }
    div[data-testid="stMetricLabel"] { white-space: normal !important; font-size: 0.9em !important; color: #9ca3af !important; }
    
    /* 评论区样式 */
    .comment-card {
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #ddd;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 标题 & 数据加载
# ==========================================
st.title("📡 SRAMS Digital Command Center")
st.caption("Live Feed from JalanSafe AI Database | Auto-refreshes every 30 seconds")

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

# ==========================================
# 4. 🔥 侧边栏：核心交互区 (Evidence & Feedback)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=100)
    st.header("Admin Controls")
    
    # 成本计算器
    st.subheader("💰 Cost Model")
    cost_per_pothole = st.slider("Cost/Pothole (RM)", 100, 1000, 200, step=50)
    cost_per_traffic = st.slider("Cost/Signal (RM)", 200, 2000, 500, step=100)
    
    st.markdown("---")
    
    # --- 证据与反馈查看器 ---
    st.subheader("📸 Evidence & Feedback")
    
    # A. 选择 Report ID (可以从地图点击联动，也可以手动选)
    # 如果 session_state 里有（从地图点的），就默认选那个
    default_index = 0
    if 'selected_report_id' in st.session_state and not df.empty:
        try:
            # 找到该 ID 在列表中的位置
            ids = df["id"].tolist()
            if st.session_state.selected_report_id in ids:
                default_index = ids.index(st.session_state.selected_report_id)
        except:
            pass

    selected_report_id = st.selectbox(
        "Select Report ID:",
        df["id"].tolist() if not df.empty else [],
        index=default_index,
        format_func=lambda x: f"Report #{x}"
    )

    # B. 显示详情
    if selected_report_id:
        # 获取当前选中的 Report 数据
        report_data = df[df["id"] == selected_report_id].iloc[0]
        
        # 显示基础信息
        st.info(f"**Status:** Verified (ID: #{selected_report_id})")
        st.write(f"**Type:** {report_data['report_type']}")
        st.write(f"**Note:** {report_data['description']}")
        
        # 显示照片
        if report_data.get('photo_url'):
            # 这里做个兼容：如果是本地路径，直接读；如果是 URL，也可以
            clean_path = report_data['photo_url'].replace("\\", "/")
            if os.path.exists(clean_path):
                st.image(clean_path, caption=f"Time: {report_data['created_at']}", width="stretch")
            else:
                st.warning("⚠️ Photo file missing locally.")
        
        st.markdown("---")
        
        # 🔥 C. 实时评论区 (Real-time Feedback)
        st.markdown("#### 💬 Public Comments")
        
        # 呼叫 API 获取评论
        comments = fetch_report_comments(selected_report_id)
        
        if comments:
            # 统计
            agree_num = sum(1 for c in comments if c.get('vote') == 'agree')
            disagree_num = sum(1 for c in comments if c.get('vote') == 'disagree')
            
            # 显示红绿条
            c1, c2 = st.columns(2)
            c1.metric("✅ Agree", agree_num)
            c2.metric("❌ Disagree", disagree_num)
            
            # 滚动显示评论列表
            with st.container(height=250):
                for c in comments:
                    # 处理数据
                    username = c.get("owner", {}).get("username", "Citizen") if c.get("owner") else "Citizen"
                    text = c.get("comment_text", "No content")
                    vote = str(c.get("vote", "")).lower()
                    
                    # 样式逻辑
                    if "agree" in vote and "disagree" not in vote:
                        border_color = "#28a745" # Green
                        bg_color = "rgba(40, 167, 69, 0.1)"
                        icon = "👍"
                    elif "disagree" in vote:
                        border_color = "#dc3545" # Red
                        bg_color = "rgba(220, 53, 69, 0.1)"
                        icon = "👎"
                    else:
                        border_color = "#6c757d" # Grey
                        bg_color = "rgba(255, 255, 255, 0.05)"
                        icon = "💬"
                        
                    # 渲染 HTML 卡片
                    st.markdown(
                        f"""
                        <div class="comment-card" style="background-color: {bg_color}; border-left: 3px solid {border_color};">
                            <div style="font-weight:bold; margin-bottom:2px;">{icon} {username}</div>
                            <div style="opacity:0.9;">{text}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        else:
            st.caption("No community feedback yet.")
            
        # D. 操作按钮
        if st.button("🛠️ Generate Work Order", key="btn_wo"):
            st.success("Work Order sent to Contractor! (Simulation)")
            
    else:
        st.info("Select a report to view details.")

# ==========================================
# 5. 主面板 (Main Dashboard)
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
        # 地图中心设为所有点的平均值
        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=11, tiles="CartoDB dark_matter")
        
        for index, row in df.iterrows():
            # Tooltip 显示 ID，方便点击
            tooltip_html = f"<b>ID: #{row['id']}</b> | Click to inspect"
            
            # 根据类型换颜色
            icon_color = "red" if row['report_type'] == 'road_condition' else "orange"
            
            folium.Marker(
                location=[row['latitude'], row['longitude']], 
                tooltip=tooltip_html, 
                icon=folium.Icon(color=icon_color, icon="exclamation-triangle", prefix='fa')
            ).add_to(m)
            
        # 渲染地图并监听点击
        map_data = st_folium(m, width="100%", height=500, key="folium_map")
        
        # 🔥 地图点击联动逻辑
        if map_data and map_data["last_object_clicked_tooltip"]:
            try:
                # 解析 ID: "ID: #123 | ..." -> 123
                report_id_str = map_data["last_object_clicked_tooltip"].split("#")[1].split("|")[0].strip()
                report_id = int(report_id_str)
                
                # 如果点击了新的点，更新 session_state 并刷新页面
                if st.session_state.get('selected_report_id') != report_id:
                    st.session_state.selected_report_id = report_id
                    st.rerun()
            except (IndexError, ValueError):
                pass
    else:
        st.warning("No geospatial data.")

    # 图片墙 (保持原样)
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