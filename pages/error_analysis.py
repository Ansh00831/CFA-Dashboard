"""
Error log UI mapped directly to SQLite
"""
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from models.study_plan import TOPICS
from db.schema import DB_PATH

st.title("❌ Error Log")

with st.form("error_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    err_topic = c1.selectbox("Topic", [td["label"] for td in TOPICS.values()])
    err_type  = c2.selectbox("Error type",["Concept gap", "Formula error", "Vignette misread", "Calculation slip"])
    concept = st.text_area("Correct concept — write it in your own words", height=80)
    
    if st.form_submit_button("Log Error", type="primary", use_container_width=True) and concept.strip():
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO error_logs (date, topic, error_type, concept) VALUES (?,?,?,?)",
                (date.today().isoformat(), err_topic, err_type, concept)
            )
        st.toast("Error logged! 📝")
        st.rerun()

st.divider()

df_err = pd.read_sql("SELECT date, topic, error_type, concept FROM error_logs ORDER BY id DESC", sqlite3.connect(DB_PATH))

if df_err.empty:
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: var(--secondary-background-color); border-radius: 8px;">
        <h2>📝</h2>
        <h4 style="color: var(--text-color);">Your error log is clean</h4>
        <p style="color: gray;">Log mistakes here to build your revision Bible.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.dataframe(df_err, use_container_width=True, hide_index=True)