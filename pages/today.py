import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date
from models.study_plan import TOPICS, PHASES
from db.queries import (
    get_spaced_rep_queue, log_hours, start_timer, get_timer_start, clear_timer,
    get_all_module_states, get_weakest_subjects, 
    auto_populate_daily_todos, get_active_todos_df, get_completed_todos_df, sync_todos_df, add_todo
)

# Run the auto-populator once when page loads
auto_populate_daily_todos()

st.title("🏠 Today's Command")

# Current Phase logic
today = date.today()
current_phase = next((p for p in PHASES if p.start <= today <= p.end), None)
if current_phase:
    st.info(f"**Current Phase: {current_phase.name}**  ·  Ends {current_phase.end.strftime('%b %d')}  ·  Target: {current_phase.hrs} hrs this phase")

# Keyboard Shortcut Injection
components.html("""
<script>
const doc = window.parent.document;
doc.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'l') {
        const buttons = Array.from(doc.querySelectorAll('button'));
        const logBtn = buttons.find(b => b.innerText.includes('Quick Log 1.5'));
        if(logBtn) logBtn.click();
    }
});
</script>
""", height=0)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### What to do today")
    
    # 1. Spaced Repetition Queue
    rep_queue = get_spaced_rep_queue()
    if rep_queue:
        st.markdown("**Spaced repetition — these need revisiting:**")
        conf_colors = {1:"#E24B4A", 2:"#BA7517", 3:"#378ADD", 4:"#639922", 5:"#27500A"}
        for item in rep_queue:
            color = conf_colors.get(item.conf, "#378ADD")
            st.markdown(
                f'<div style="padding:8px 12px;border-left:3px solid {color};background:{color}15;'
                f'border-radius:0 6px 6px 0;margin-bottom:6px;font-size:13px">'
                f'<b>{item.module}</b> — <span style="color:var(--text-color)">{item.topic} ({item.days_ago}d ago)</span>'
                f'</div>', unsafe_allow_html=True
            )
            
    # 2. Weakest Subjects
    weak_subs = get_weakest_subjects()
    if weak_subs:
        st.markdown("**Weakest subjects from your last mock — prioritise Q-bank here:**")
        for sub, score in weak_subs:
            label = TOPICS.get(sub, {}).get("label", sub)
            color = "#E24B4A" if score < 50 else "#BA7517"
            st.markdown(
                f'<div style="padding:8px 12px;border-left:3px solid {color};background:{color}15;'
                f'border-radius:0 6px 6px 0;margin-bottom:6px;font-size:13px">'
                f'<b style="color:{color}">{score}%</b> {label}</div>', unsafe_allow_html=True
            )

    st.divider()

    # --- ADVANCED TODO LIST ---
    st.markdown("### Daily Tasks & Modules")
    
    # Input for new custom task
    c1, c2 = st.columns([3,1])
    new_task = c1.text_input("Add manual task", label_visibility="collapsed", placeholder="Add a custom task…")
    if c2.button("Add Task", use_container_width=True) and new_task.strip():
        add_todo(new_task, due=date.today().isoformat())
        st.rerun()

    # The editable Active Tasks Table
    df_active = get_active_todos_df()
    if not df_active.empty:
        # Cleanly format for the UI
        df_ui = df_active.copy()
        
        edited_df = st.data_editor(
            df_ui,
            hide_index=True,
            use_container_width=True,
            column_config={
                "id": None, # Hide database ID
                "done": st.column_config.CheckboxColumn("Done?", default=False, width="small"),
                "task": st.column_config.TextColumn("Task / Module", width="large"),
                "due_date": st.column_config.DateColumn("Target Date", format="MMM DD, YYYY"),
                "completed_date": st.column_config.DateColumn("Done Date", format="MMM DD, YYYY")
            }
        )
        
        # If user checked "Done" or changed a date, sync and refresh
        if not edited_df.equals(df_ui):
            sync_todos_df(edited_df)
            st.toast("Tasks updated!")
            st.rerun()
    else:
        st.success("All caught up! No active tasks pending.")

    # Log of Completed Tasks
    df_completed = get_completed_todos_df()
    if not df_completed.empty:
        with st.expander(f"📁 **Completed Tasks Log ({len(df_completed)})**"):
            df_comp_ui = df_completed.copy()
            
            edited_comp_df = st.data_editor(
                df_comp_ui,
                hide_index=True,
                use_container_width=True,
                key="completed_todos_editor", # CRITICAL: Needs unique key since there are two editors on the page
                column_config={
                    "id": None, # Hide database ID
                    "due_date": None, # Hide due date to keep the log clean
                    "done": st.column_config.CheckboxColumn("Done?", default=True, width="small"),
                    "task": st.column_config.TextColumn("Completed Task", disabled=True), # Disabled so you can't rename in archive
                    "completed_date": st.column_config.DateColumn("Finished On", disabled=True)
                }
            )
            
            # If user unchecks a box, restore it to active
            if not edited_comp_df.equals(df_comp_ui):
                sync_todos_df(edited_comp_df)
                st.toast("Task restored to active! 🔄")
                st.rerun()

    st.divider()

    # Log a Session Form
    st.markdown("### Log a session")
    c1, c2, c3 = st.columns([2, 1, 1])
    log_topic = c1.selectbox("Topic", [t["label"] for t in TOPICS.values()], label_visibility="collapsed")
    log_hrs   = c2.number_input("Hours", min_value=0.25, max_value=10.0, value=1.5, step=0.25, label_visibility="collapsed")
    if c3.button("Log", use_container_width=True, type="primary"):
        log_hours(log_hrs, log_topic)
        st.toast(f"Logged {log_hrs} hrs on {log_topic}")
        st.rerun()

with col2:
    st.markdown("### ⏱ Session Timer")
    timer_start = get_timer_start()
    
    if st.button("▶ Start Timer", use_container_width=True) and not timer_start:
        start_timer()
        st.rerun()
        
    if timer_start:
        elapsed = (datetime.now() - timer_start).total_seconds() / 3600
        st.success(f"Running: {elapsed:.2f} hrs")
        if st.button("⏹ Stop & Log", use_container_width=True):
            log_hours(round(elapsed, 2))
            clear_timer()
            st.toast(f"Logged {round(elapsed, 2)} hrs!")
            st.rerun()

    st.divider()
    
    st.markdown("### Topic completion")
    states = get_all_module_states()
    for tk, td in TOPICS.items():
        total_m = len(td["modules"])
        done_m = sum(1 for m in td["modules"] if states.get(f"{tk}||{m}", False))
        pct = int(done_m / total_m * 100) if total_m else 0
        color = td["color"]
        st.markdown(
            f'<div style="margin-bottom:8px">'
            f'<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">'
            f'<span style="color:var(--text-color)">{td["label"]}</span>'
            f'<span style="color:{color};font-weight:500">{done_m}/{total_m}</span>'
            f'</div>'
            f'<div style="height:6px;background:var(--secondary-background-color);border-radius:3px;overflow:hidden">'
            f'<div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>'
            f'</div></div>', unsafe_allow_html=True
        )

    st.divider()
    
    st.markdown("### Phase overview")
    for p in PHASES:
        if today > p.end:
            badge, bc = "Done", "#27500A"
        elif p.start <= today <= p.end:
            badge, bc = "Now", "#185FA5"
        else:
            badge, bc = "Upcoming", "#888780"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:12px">'
            f'<span style="padding:2px 7px;border-radius:4px;background:{bc}22;color:{bc};font-weight:500;white-space:nowrap">{badge}</span>'
            f'<span style="color:var(--text-color)">{p.name}</span>'
            f'<span style="color:gray;margin-left:auto">{p.hrs}h</span>'
            f'</div>', unsafe_allow_html=True
        )