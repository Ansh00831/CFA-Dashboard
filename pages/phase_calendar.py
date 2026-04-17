import streamlit as st
from datetime import date
from models.study_plan import PHASES, TOPICS

st.title("📅 Phase Calendar")
today = date.today()

for p in PHASES:
    # Logic for status and coloring
    if today > p.end:
        status, badge_color = "Completed", "#27500A"
    elif p.start <= today <= p.end:
        days_in = (today - p.start).days + 1
        days_total = (p.end - p.start).days + 1
        status, badge_color = f"Active — day {days_in} of {days_total}", "#185FA5"
    else:
        days_to = (p.start - today).days
        status, badge_color = f"Starts in {days_to} days", "#888780"

    # Container styling
    with st.container():
        border = "2px solid #185FA5" if p.start <= today <= p.end else "1px solid var(--secondary-background-color)"
        topics_str = ", ".join(TOPICS.get(t,{}).get("label",t) for t in p.topics)
        
        st.markdown(
            f'<div style="border:{border}; border-bottom: none; border-radius:10px 10px 0 0; padding:14px 18px; margin-top:15px; background:var(--secondary-background-color);">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">'
            f'<span style="font-size:16px;font-weight:600;color:var(--text-color)">{p.name}</span>'
            f'<span style="font-size:12px;font-weight:500;padding:4px 10px;border-radius:4px;background:{badge_color}22;color:{badge_color}">{status}</span>'
            f'</div>'
            f'<div style="font-size:13px;color:gray">'
            f'{p.start.strftime("%b %d")} – {p.end.strftime("%b %d, %Y")}  ·  '
            f'{(p.end-p.start).days+1} days  ·  <b>{p.hrs} hrs</b>  ·  '
            f'Topics: {topics_str}'
            f'</div></div>', unsafe_allow_html=True
        )
        
        # New Feature: The Dropdown / Expander mapping tasks to modules
        with st.expander("🔽 **View detailed tasks & modules for this phase**"):
            if not p.tasks:
                st.write("No specific sub-tasks listed for this phase.")
            
            for task in p.tasks:
                st.markdown(f"**{task['period']}** — {task['title']} (`{task['hrs']} hrs`)")
                st.markdown(f"<div style='color:gray; font-size:13.5px; margin-bottom:8px;'>{task['desc']}</div>", unsafe_allow_html=True)
                
                # Check and list assigned Curriculum modules
                if task.get('modules'):
                    for mod in task['modules']:
                        st.markdown(
                            f"<div style='padding-left: 15px; font-size: 13.5px; margin-bottom: 2px;'>"
                            f"🔸 {mod}</div>", 
                            unsafe_allow_html=True
                        )
                st.write("") # Margin