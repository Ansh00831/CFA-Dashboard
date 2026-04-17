"""
Frontend Improvement #4: Added st.toast on save
Frontend Improvement #5: Empty state styling
"""
import streamlit as st
import sqlite3
import pandas as pd
from db.schema import DB_PATH

st.title("📊 Mock Analytics")

conn = sqlite3.connect(DB_PATH)
df_mocks = pd.read_sql("SELECT * FROM mock_scores", conn)

st.markdown("#### Enter / update mock scores")
edited = st.data_editor(
    df_mocks,
    hide_index=True,
    use_container_width=True,
    column_config={"mock": st.column_config.TextColumn("Mock", disabled=True)}
)

if not edited.equals(df_mocks):
    edited.to_sql("mock_scores", conn, if_exists="replace", index=False)
    st.toast("Mock scores saved! ✅")  # Frontend #4 Fixed
    st.rerun()

taken = edited[edited["overall"] > 0]

if taken.empty:
    # Frontend Improvement #5: Nicer empty states
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: var(--secondary-background-color); border-radius: 8px; margin-top: 20px;">
        <h2>📭</h2>
        <h4 style="color: var(--text-color);">No mocks taken yet</h4>
        <p style="color: gray;">Take your first mock and log the scores above to unlock analytics.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=taken["mock"], y=taken["overall"], mode="lines+markers", name="Your Score", line=dict(color="#185FA5", width=3)))
    fig.add_hline(y=65, line_dash="dot", line_color="#639922", annotation_text="Pass confidence")
    fig.update_layout(yaxis_range=[0,100], template="plotly_white", height=320)
    st.plotly_chart(fig, use_container_width=True)