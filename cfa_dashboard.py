"""
Streamlit entry point — UI rendering only
"""
import streamlit as st
from datetime import date
from db.schema import init_db
from db.queries import get_streak, get_pace, required_daily_burn, get_hours_logged

# Initialize database on startup
init_db()

# Frontend Improvement #2: Mobile responsiveness (layout="centered" instead of "wide")
st.set_page_config(
    page_title="CFA L2 Command Center",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Render Global Sidebar (Frontend #1: Overloaded sidebar fixed)
with st.sidebar:
    st.markdown("### 📡 Ansh's L2 Dashboard")
    
    exam_date = date(2026, 11, 15)
    days_remaining = max(1, (exam_date - date.today()).days)
    st.caption(f"Exam: Nov 15, 2026  ·  {days_remaining} days left")

    streak = get_streak()
    streak_color = "#639922" if streak >= 3 else "#BA7517" if streak >= 1 else "#E24B4A"
    
    st.markdown(
        f'<div style="padding:10px 14px;border-radius:8px;background:{streak_color}22;border-left:3px solid {streak_color};margin-bottom:12px">'
        f'<span style="font-size:22px;font-weight:600;color:{streak_color}">{streak}</span>'
        f'<span style="font-size:13px;color:{streak_color}"> day streak</span>'
        f'</div>', unsafe_allow_html=True
    )

    pace = get_pace(7)
    req  = required_daily_burn()
    status_str = "On track" if pace >= req else "Behind schedule"
    status_color = "#639922" if pace >= req else "#E24B4A"
    
    col1, col2 = st.columns(2)
    col1.metric("7-day pace", f"{pace} hrs/d")
    col2.metric("Need", f"{req} hrs/d")
    
    st.markdown(
        f'<div style="padding:7px 12px;border-radius:6px;background:{status_color}22;font-size:12px;color:{status_color};font-weight:500">'
        f'{status_str}</div>', unsafe_allow_html=True
    )
    
    st.divider()
    hours_logged = get_hours_logged()
    target_hours = 490.0
    hrs_pct = min(hours_logged / target_hours, 1.0)
    st.progress(hrs_pct, text=f"Hours: {hours_logged:.1f} / {target_hours}")

# Streamlit native navigation explicitly pointing to your file names
pg = st.navigation([
    st.Page("pages/today.py", title="Today's Command", icon="🏠"),
    st.Page("pages/progress.py", title="Curriculum Tracker", icon="📚"),
    st.Page("pages/mock_analytics.py", title="Mock Analytics", icon="📊"),
    st.Page("pages/error_analysis.py", title="Error Log", icon="❌"),
    st.Page("pages/phase_calendar.py", title="Phase Calendar", icon="📅"),
])
pg.run()
