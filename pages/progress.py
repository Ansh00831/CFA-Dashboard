"""
Frontend Improvement #7: Emoji buttons instead of slider
"""
import streamlit as st
import sqlite3
import pandas as pd
from models.study_plan import TOPICS, PRIORITY_ORDER
from db.schema import DB_PATH
from db.queries import update_module_state, update_module_conf

st.title("📚 Curriculum Tracker")

# Load states
df_states = pd.read_sql("SELECT * FROM module_states", sqlite3.connect(DB_PATH))
state_map = {f"{r['topic_key']}||{r['module']}": r for _, r in df_states.iterrows()}

for priority in PRIORITY_ORDER:
    topics =[(tk, td) for tk, td in TOPICS.items() if td.get("priority") == priority]
    if not topics: continue
    
    for tk, td in topics:
        with st.expander(f"**{td['label']}** — {priority}", expanded=True):
            for mod in td["modules"]:
                mk = f"{tk}||{mod}"
                row = state_map.get(mk, {})
                is_done = bool(row.get("is_done", False))
                conf = row.get("confidence", 3)

                c1, c2 = st.columns([3, 2])
                
                new_done = c1.checkbox(mod, value=is_done, key=f"chk_{mk}")
                if new_done != is_done:
                    update_module_state(tk, mod, new_done)
                    st.rerun()
                
                if new_done:
                    # Frontend Improvement #7: Emoji Buttons
                    col_emojis = c2.columns(5)
                    emojis = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "✅"}
                    for val, emo in emojis.items():
                        # Highlight active button
                        btn_label = f"[{emo}]" if val == conf else emo
                        if col_emojis[val-1].button(btn_label, key=f"emo_{mk}_{val}"):
                            update_module_conf(tk, mod, val)
                            st.rerun()