"""
CFA L2 Command Center — v3 (Supabase persistence)
Ansh Bahirat • CFA Level 2 • Nov 15 2026

Architecture:
  Layer 1 — Input  : hours, modules, errors, mock scores
  Layer 2 — Engine : streak, burn rate, velocity, spaced rep, prediction
  Layer 3 — Output : today's plan, charts, alerts, progress
  Layer 4 — DB     : Supabase (persistent across Streamlit restarts)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import math
from supabase import create_client, Client

# ─────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CFA L2 — Ansh's Command Center",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# SUPABASE CLIENT  (reads from st.secrets)
# ─────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

sb = get_supabase()

# ─────────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────────

def db_load_state() -> dict:
    """Load the single-row JSON state blob from Supabase."""
    try:
        res = sb.table("cfa_state").select("*").eq("id", 1).execute()
        if res.data:
            return res.data[0].get("data", {})
    except Exception as e:
        st.warning(f"Could not load state: {e}")
    return {}

def db_save_state(obj: dict):
    """Upsert the single-row JSON state blob."""
    try:
        sb.table("cfa_state").upsert({"id": 1, "data": obj}).execute()
    except Exception as e:
        st.warning(f"Could not save state: {e}")

def db_load_daily_logs() -> pd.DataFrame:
    default = pd.DataFrame(columns=["date", "hours", "topic"])
    try:
        res = sb.table("daily_logs").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # drop the Supabase auto-id column if present
            return df.drop(columns=["id"], errors="ignore")
    except Exception as e:
        st.warning(f"Could not load daily logs: {e}")
    return default

def db_save_daily_logs(df: pd.DataFrame):
    try:
        sb.table("daily_logs").delete().neq("date", "").execute()  # clear all rows
        if not df.empty:
            records = df[["date", "hours", "topic"]].to_dict(orient="records")
            sb.table("daily_logs").insert(records).execute()
    except Exception as e:
        st.warning(f"Could not save daily logs: {e}")

def db_load_error_log() -> pd.DataFrame:
    default = pd.DataFrame(columns=["date", "topic", "error_type", "concept", "tags"])
    try:
        res = sb.table("error_log").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            return df.drop(columns=["id"], errors="ignore")
    except Exception as e:
        st.warning(f"Could not load error log: {e}")
    return default

def db_save_error_log(df: pd.DataFrame):
    try:
        sb.table("error_log").delete().neq("date", "").execute()
        if not df.empty:
            records = df[["date", "topic", "error_type", "concept", "tags"]].to_dict(orient="records")
            sb.table("error_log").insert(records).execute()
    except Exception as e:
        st.warning(f"Could not save error log: {e}")

def db_load_mock_scores() -> pd.DataFrame:
    default = pd.DataFrame({
        "mock":    ["Mock 1","Mock 2","Mock 3","Mock 4","Mock 5"],
        "date":    ["2026-08-25","2026-09-13","2026-09-28","2026-10-12","2026-11-08"],
        "target":  [58, 63, 68, 70, 72],
        "overall": [0, 0, 0, 0, 0],
        "FSA": [0]*5, "Quant": [0]*5, "Fixed_Income": [0]*5,
        "Equity": [0]*5, "Ethics": [0]*5, "Derivatives": [0]*5,
        "PM": [0]*5, "Economics": [0]*5, "Corp_Issuers": [0]*5,
        "Alts": [0]*5,
    })
    try:
        res = sb.table("mock_scores").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            return df.drop(columns=["id"], errors="ignore")
    except Exception as e:
        st.warning(f"Could not load mock scores: {e}")
    return default

def db_save_mock_scores(df: pd.DataFrame):
    try:
        sb.table("mock_scores").delete().neq("mock", "").execute()
        if not df.empty:
            records = df.to_dict(orient="records")
            sb.table("mock_scores").insert(records).execute()
    except Exception as e:
        st.warning(f"Could not save mock scores: {e}")

def db_load_completed_tasks() -> pd.DataFrame:
    default = pd.DataFrame(columns=["date", "task"])
    try:
        res = sb.table("completed_tasks").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            return df.drop(columns=["id"], errors="ignore")
    except Exception as e:
        st.warning(f"Could not load completed tasks: {e}")
    return default

def db_save_completed_tasks(df: pd.DataFrame):
    try:
        sb.table("completed_tasks").delete().neq("date", "").execute()
        if not df.empty:
            records = df[["date", "task"]].to_dict(orient="records")
            sb.table("completed_tasks").insert(records).execute()
    except Exception as e:
        st.warning(f"Could not save completed tasks: {e}")

# ─────────────────────────────────────────────────────────────────
# SESSION STATE BOOTSTRAP  (loads from Supabase once per session)
# ─────────────────────────────────────────────────────────────────

def init_state():
    if "db_loaded" not in st.session_state:
        saved = db_load_state()
        st.session_state.hours_logged      = saved.get("hours_logged", 0.0)
        st.session_state.target_hours      = 490.0
        st.session_state.exam_date         = date(2026, 11, 15)
        st.session_state.start_date        = date(2026, 4, 13)
        st.session_state.todos             = saved.get("todos", [])
        st.session_state.completion_dates  = saved.get("completion_dates", {})
        st.session_state.module_states     = saved.get("module_states", {})
        st.session_state.conf_states       = saved.get("conf_states", {})
        st.session_state.timer_start       = None

        # CSVs
        st.session_state.daily_logs        = db_load_daily_logs()
        st.session_state.error_log         = db_load_error_log()
        st.session_state.mock_scores       = db_load_mock_scores()
        st.session_state.completed_tasks   = db_load_completed_tasks()

        st.session_state.db_loaded = True  # don't reload on every rerun

def persist():
    """Write everything back to Supabase."""
    db_save_state({
        "hours_logged":     st.session_state.hours_logged,
        "todos":            st.session_state.todos,
        "completion_dates": st.session_state.completion_dates,
        "module_states":    st.session_state.module_states,
        "conf_states":      st.session_state.conf_states,
    })
    db_save_daily_logs(st.session_state.daily_logs)
    db_save_error_log(st.session_state.error_log)
    db_save_mock_scores(st.session_state.mock_scores)
    db_save_completed_tasks(st.session_state.completed_tasks)

init_state()

# ─────────────────────────────────────────────────────────────────
# CURRICULUM DATA
# ─────────────────────────────────────────────────────────────────

TOPICS = {
    "FSA": {
        "label": "Financial Statement Analysis",
        "priority": "CRITICAL",
        "weight": "10–15%",
        "hours": 65,
        "color": "#E24B4A",
        "modules": [
            "Intercorporate Investments — equity method vs consolidation",
            "Intercorporate Investments — business combinations, IFRS 3 vs GAAP",
            "Employee Compensation — pensions (IAS 19 vs US GAAP)",
            "Share-based compensation",
            "Multinational Operations — current rate vs temporal method",
            "Analysis of Financial Institutions",
        ],
    },
    "Quant": {
        "label": "Quantitative Methods",
        "priority": "VERY HIGH",
        "weight": "5–10%",
        "hours": 35,
        "color": "#BA7517",
        "modules": [
            "Basics of multiple regression and assumptions",
            "Evaluating regression model fit, ANOVA, hypothesis testing",
            "Model misspecification — multicollinearity, heteroskedasticity, serial correlation",
            "Time-series analysis — ARMA, random walks, unit roots, cointegration",
            "Machine learning for investment analysis",
        ],
    },
    "Fixed_Income": {
        "label": "Fixed Income",
        "priority": "VERY HIGH",
        "weight": "10–15%",
        "hours": 55,
        "color": "#BA7517",
        "modules": [
            "Term structure and interest rate dynamics",
            "Arbitrage-free valuation — binomial trees, OAS",
            "Valuation of bonds with embedded options",
            "Credit analysis models — structural and reduced-form",
            "Credit default swaps",
        ],
    },
    "Equity": {
        "label": "Equity Valuation",
        "priority": "MAINTAIN",
        "weight": "10–15%",
        "hours": 60,
        "color": "#639922",
        "modules": [
            "Equity valuation applications and processes",
            "Industry and company analysis",
            "Discounted dividend valuation — DDM, H-model, multi-stage",
            "Free cash flow valuation — FCFF and FCFE",
            "Market-based valuation — P/E, P/B, EV/EBITDA",
            "Residual income valuation",
            "Private company valuation",
        ],
    },
    "Ethics": {
        "label": "Ethics & Professional Standards",
        "priority": "HIGH",
        "weight": "10–15%",
        "hours": 30,
        "color": "#27500A",
        "modules": [
            "Standards I–II — Professionalism, Capital Market Integrity",
            "Standards III–IV — Duties to Clients and Employers",
            "Standards V–VI — Investment Analysis, Conflicts of Interest",
            "Standard VII — Responsibilities as CFA Member/Candidate",
            "GIPS — fundamentals and composites",
        ],
    },
    "Derivatives": {
        "label": "Derivatives",
        "priority": "HIGH",
        "weight": "5–10%",
        "hours": 30,
        "color": "#185FA5",
        "modules": [
            "Forward commitments — forwards, futures, swaps (pricing and valuation)",
            "Contingent claims — BSM model, Greeks, binomial trees, interest rate options",
        ],
    },
    "PM": {
        "label": "Portfolio Management",
        "priority": "VERY HIGH",
        "weight": "10–15%",
        "hours": 40,
        "color": "#3C3489",
        "modules": [
            "Overview of asset allocation — strategic vs tactical frameworks",
            "Principles of asset allocation — MVO, Black-Litterman, liability-relative",
            "Asset allocation with real-world constraints",
            "Currency management and overlay strategies",
            "Options strategies for equity portfolios",
            "Derivatives in portfolio management — futures, swaps",
            "Risk management framework and budgeting",
            "Backtesting and simulation — look-ahead, survivorship, data-snooping biases",
            "Economics and investment markets — macro factor models",
            "Exchange-traded funds — creation/redemption, premium/discount",
        ],
    },
    "Economics": {
        "label": "Economics",
        "priority": "MEDIUM",
        "weight": "5–10%",
        "hours": 25,
        "color": "#BA7517",
        "modules": [
            "Currency exchange rates — CIRP, UIRP, PPP, Fisher, carry trades",
            "Economic growth and investment decision — Solow model, convergence",
        ],
    },
    "Corp_Issuers": {
        "label": "Corporate Issuers",
        "priority": "MEDIUM",
        "weight": "5–10%",
        "hours": 25,
        "color": "#639922",
        "modules": [
            "Dividends and share repurchases — signalling, irrelevance, residual model",
            "ESG factors in investment analysis",
            "Corporate governance and agency issues",
        ],
    },
    "Alts": {
        "label": "Alternative Investments",
        "priority": "MAINTAIN",
        "weight": "5–10%",
        "hours": 25,
        "color": "#639922",
        "modules": [
            "Private capital — PE/VC, J-curve, NAV, carried interest, IRR metrics",
            "Real estate — direct/indirect, NOI, cap rate, REIT valuation",
            "Infrastructure and natural resources",
            "Hedge funds — strategies and risk metrics",
        ],
    },
}

PRIORITY_ORDER = ["CRITICAL", "VERY HIGH", "HIGH", "MEDIUM", "MAINTAIN"]

PHASES = [
    {"name": "Foundation Sprint",      "start": date(2026,4,13),  "end": date(2026,4,30),  "hrs": 60,  "topics": ["Quant","FSA"]},
    {"name": "Maintenance Mode",       "start": date(2026,5,1),   "end": date(2026,5,14),  "hrs": 14,  "topics": ["FSA"]},
    {"name": "Power Window",           "start": date(2026,5,15),  "end": date(2026,5,31),  "hrs": 130, "topics": ["FSA","Fixed_Income","Equity"]},
    {"name": "Internship Grind I",     "start": date(2026,6,1),   "end": date(2026,6,30),  "hrs": 88,  "topics": ["Ethics","Derivatives","FSA"]},
    {"name": "Completing Curriculum",  "start": date(2026,7,1),   "end": date(2026,7,31),  "hrs": 88,  "topics": ["PM","Corp_Issuers","Economics"]},
    {"name": "Alts + Practice Pivot",  "start": date(2026,8,1),   "end": date(2026,8,31),  "hrs": 88,  "topics": ["Alts","Q-bank","Mock 1"]},
    {"name": "Mock & Revision Cycle",  "start": date(2026,9,1),   "end": date(2026,9,30),  "hrs": 66,  "topics": ["Q-bank","Error Log","Mock 2 & 3"]},
    {"name": "Final Consolidation",    "start": date(2026,10,1),  "end": date(2026,10,31), "hrs": 44,  "topics": ["Ethics","Q-bank","Mock 4"]},
    {"name": "Final Sprint",           "start": date(2026,11,1),  "end": date(2026,11,15), "hrs": 22,  "topics": ["Recall","Mock 5","Ethics","REST"]},
]

CONF_LABELS = {1: "Weak", 2: "Shaky", 3: "Moderate", 4: "Strong", 5: "Mastered"}
CONF_COLORS = {1: "#E24B4A", 2: "#BA7517", 3: "#378ADD", 4: "#639922", 5: "#27500A"}

# ─────────────────────────────────────────────────────────────────
# LAYER 2 — COMPUTATION ENGINE
# ─────────────────────────────────────────────────────────────────

def days_remaining():
    return max(1, (st.session_state.exam_date - date.today()).days)

def hours_remaining():
    return max(0, st.session_state.target_hours - st.session_state.hours_logged)

def required_daily_burn():
    return round(hours_remaining() / days_remaining(), 2)

def compute_streak():
    if st.session_state.daily_logs.empty or "date" not in st.session_state.daily_logs.columns:
        return 0
    df = st.session_state.daily_logs.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])
    if df.empty:
        return 0
    logged_days = set(df[df["hours"] > 0]["date"].tolist())
    streak = 0
    check = date.today()
    while check in logged_days:
        streak += 1
        check -= timedelta(days=1)
    if streak == 0:
        check = date.today() - timedelta(days=1)
        while check in logged_days:
            streak += 1
            check -= timedelta(days=1)
    return streak

def avg_hours_last_n(n=7):
    if st.session_state.daily_logs.empty or "date" not in st.session_state.daily_logs.columns:
        return 0.0
    df = st.session_state.daily_logs.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])
    cutoff = date.today() - timedelta(days=n)
    recent = df[df["date"] >= cutoff].copy()
    recent.loc[:, "hours"] = pd.to_numeric(recent["hours"], errors="coerce").fillna(0)
    return round(recent["hours"].sum() / n, 2)

def predict_finish_date():
    pace = avg_hours_last_n(7)
    if pace <= 0:
        return None
    days_needed = math.ceil(hours_remaining() / pace)
    return date.today() + timedelta(days=days_needed)

def on_track_status():
    pace = avg_hours_last_n(7)
    req  = required_daily_burn()
    if req == 0:
        return "Target reached!", "#27500A"
    ratio = pace / req
    if ratio >= 1.0:
        return f"On track ({pace} vs {req} hrs/day needed)", "#639922"
    elif ratio >= 0.75:
        return f"Slightly behind ({pace} vs {req} hrs/day needed)", "#BA7517"
    else:
        return f"Behind schedule ({pace} vs {req} hrs/day needed)", "#E24B4A"

def current_phase():
    today = date.today()
    for p in PHASES:
        if p["start"] <= today <= p["end"]:
            return p
    return None

def get_module_key(topic_key, module):
    return f"{topic_key}||{module}"

def is_module_done(topic_key, module):
    return st.session_state.module_states.get(get_module_key(topic_key, module), False)

def get_module_conf(topic_key, module):
    return st.session_state.conf_states.get(get_module_key(topic_key, module), 3)

def topic_progress(topic_key):
    mods = TOPICS[topic_key]["modules"]
    done = sum(1 for m in mods if is_module_done(topic_key, m))
    return done, len(mods)

def overall_progress():
    total = sum(len(t["modules"]) for t in TOPICS.values())
    done  = sum(sum(1 for m in t["modules"] if is_module_done(k, m)) for k, t in TOPICS.items())
    return done, total

def spaced_rep_queue():
    today = date.today()
    queue = []
    for tk, td in TOPICS.items():
        for mod in td["modules"]:
            if not is_module_done(tk, mod):
                continue
            conf = get_module_conf(tk, mod)
            key  = get_module_key(tk, mod)
            cdate_str = st.session_state.completion_dates.get(key)
            days_ago  = (today - datetime.strptime(cdate_str, "%Y-%m-%d").date()).days if cdate_str else 99
            if conf <= 2 or (conf == 3 and days_ago >= 14) or (conf == 4 and days_ago >= 30):
                queue.append({
                    "topic": td["label"], "module": mod, "conf": conf,
                    "days_ago": days_ago, "urgency": (3 - conf) * 10 + days_ago,
                })
    queue.sort(key=lambda x: -x["urgency"])
    return queue[:5]

def next_unread_modules(n=5):
    result = []
    for priority in PRIORITY_ORDER:
        for tk, td in TOPICS.items():
            if td["priority"] != priority:
                continue
            for mod in td["modules"]:
                if not is_module_done(tk, mod):
                    result.append({"topic_key": tk, "topic": td["label"], "module": mod, "priority": priority})
                    if len(result) >= n:
                        return result
    return result

def weakest_subjects_from_mocks():
    df    = st.session_state.mock_scores.copy()
    taken = df[df["overall"] > 0]
    if taken.empty:
        return []
    last     = taken.iloc[-1]
    subjects = ["FSA","Quant","Fixed_Income","Equity","Ethics","Derivatives","PM","Economics","Corp_Issuers","Alts"]
    scores   = {s: last.get(s, 0) for s in subjects}
    sorted_subs = sorted(scores.items(), key=lambda x: x[1])
    return [(s, sc) for s, sc in sorted_subs if sc > 0][:3]

def log_hours(hrs, topic_label="General"):
    st.session_state.hours_logged = round(st.session_state.hours_logged + hrs, 2)
    today_str = date.today().isoformat()
    dl   = st.session_state.daily_logs
    mask = pd.Series([False] * len(dl), index=dl.index)
    if not dl.empty and "date" in dl.columns:
        parsed_dates = pd.to_datetime(dl["date"], errors="coerce").dt.date
        mask = (parsed_dates == date.today())
    if not dl.empty and mask.any():
        st.session_state.daily_logs.loc[mask, "hours"] += hrs
    else:
        new_row = pd.DataFrame([{"date": today_str, "hours": hrs, "topic": topic_label}])
        st.session_state.daily_logs = pd.concat([st.session_state.daily_logs, new_row], ignore_index=True)
    persist()

# ─────────────────────────────────────────────────────────────────
# LAYER 3 — SIDEBAR
# ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📡 Ansh's L2 Dashboard")
    st.caption(f"Exam: Nov 15, 2026 · {days_remaining()} days left")

    streak       = compute_streak()
    streak_color = "#639922" if streak >= 3 else "#BA7517" if streak >= 1 else "#E24B4A"
    st.markdown(
        f'<div style="padding:10px 14px;border-radius:8px;background:{streak_color}22;border-left:3px solid {streak_color};margin-bottom:12px">'
        f'<span style="font-size:22px;font-weight:600;color:{streak_color}">{streak}</span>'
        f'<span style="font-size:13px;color:{streak_color}"> day streak</span>'
        f'<div style="font-size:11px;color:var(--color-text-secondary)">{"Keep it going!" if streak >= 1 else "Log today to start your streak"}</div>'
        f'</div>', unsafe_allow_html=True
    )

    pace         = avg_hours_last_n(7)
    req          = required_daily_burn()
    status_str, status_color = on_track_status()
    col1, col2   = st.columns(2)
    col1.metric("7-day pace", f"{pace} hrs/day")
    col2.metric("Need",       f"{req} hrs/day")
    st.markdown(
        f'<div style="padding:7px 12px;border-radius:6px;background:{status_color}22;font-size:12px;color:{status_color};font-weight:500">'
        f'{status_str}</div>', unsafe_allow_html=True
    )

    predicted = predict_finish_date()
    if predicted:
        days_diff = (st.session_state.exam_date - predicted).days
        pred_color = "#639922" if days_diff >= 0 else "#E24B4A"
        pred_msg   = f"Finish hours by {predicted.strftime('%b %d')} ({'+' if days_diff>=0 else ''}{days_diff} days vs exam)"
        st.markdown(f'<div style="font-size:12px;color:{pred_color};margin-top:6px">{pred_msg}</div>', unsafe_allow_html=True)

    st.divider()

    done_m, total_m = overall_progress()
    hrs_pct  = min(st.session_state.hours_logged / st.session_state.target_hours, 1.0)
    mod_pct  = done_m / total_m if total_m else 0
    st.progress(hrs_pct, text=f"Hours: {st.session_state.hours_logged:.1f} / {st.session_state.target_hours}")
    st.progress(mod_pct, text=f"Modules: {done_m} / {total_m}")
    st.divider()

    # ── Session Timer ──
    st.markdown("**⏱ Session Timer**")
    c1, c2 = st.columns(2)
    if c1.button("▶ Start", use_container_width=True):
        st.session_state.timer_start = datetime.now()
        st.rerun()
    if st.session_state.timer_start:
        elapsed = (datetime.now() - st.session_state.timer_start).total_seconds() / 3600
        st.caption(f"Running: {elapsed:.2f} hrs")
        if c2.button("⏹ Stop & Log", use_container_width=True):
            elapsed = round((datetime.now() - st.session_state.timer_start).total_seconds() / 3600, 2)
            log_hours(elapsed)
            st.session_state.timer_start = None
            st.success(f"Logged {elapsed} hrs")
            st.rerun()

    if st.button("⚡ Quick Log 1.5 hrs",           use_container_width=True): log_hours(1.5);  st.rerun()
    if st.button("⚡ Quick Log 1 Vignette (0.3 hrs)", use_container_width=True): log_hours(0.3); st.rerun()
    st.divider()

    nav = st.radio("Go to", [
        "🏠 Today's Command",
        "📚 Curriculum Tracker",
        "📊 Mock Analytics",
        "❌ Error Log",
        "📈 Hours & Velocity",
        "📅 Phase Calendar",
    ], label_visibility="collapsed")

# ─────────────────────────────────────────────────────────────────
# PAGE — TODAY'S COMMAND
# ─────────────────────────────────────────────────────────────────

if nav == "🏠 Today's Command":
    phase = current_phase()
    st.markdown("## Today's Command")
    if phase:
        st.info(f"**Current Phase: {phase['name']}** · Ends {phase['end'].strftime('%b %d')} · Target: {phase['hrs']} hrs this phase")

    left, right = st.columns([2, 1])

    with left:
        st.markdown("### What to do today")
        rep_queue  = spaced_rep_queue()
        next_mods  = next_unread_modules(5)
        weak_subs  = weakest_subjects_from_mocks()

        if rep_queue:
            st.markdown("**Spaced repetition — these need revisiting:**")
            for item in rep_queue:
                conf_label = CONF_LABELS[item["conf"]]
                color      = CONF_COLORS[item["conf"]]
                st.markdown(
                    f'<div style="padding:8px 12px;border-left:3px solid {color};background:{color}15;'
                    f'border-radius:0 6px 6px 0;margin-bottom:6px;font-size:13px">'
                    f'<b style="color:{color}">[{conf_label}]</b> {item["module"]} '
                    f'<span style="color:var(--color-text-secondary)">— {item["topic"]} · done {item["days_ago"]}d ago</span>'
                    f'</div>', unsafe_allow_html=True
                )

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

        if next_mods:
            st.markdown("**Next unread modules (priority order):**")
            for item in next_mods:
                color = TOPICS[item["topic_key"]]["color"]
                st.markdown(
                    f'<div style="padding:8px 12px;border-left:3px solid {color};background:{color}15;'
                    f'border-radius:0 6px 6px 0;margin-bottom:6px;font-size:13px">'
                    f'{item["module"]} '
                    f'<span style="color:var(--color-text-secondary)">— {item["topic"]}</span>'
                    f'</div>', unsafe_allow_html=True
                )

        st.divider()
        st.markdown("### Log a session")
        c1, c2, c3  = st.columns([2, 1, 1])
        log_topic   = c1.selectbox("Topic", [t["label"] for t in TOPICS.values()], label_visibility="collapsed")
        log_hrs     = c2.number_input("Hours", min_value=0.25, max_value=10.0, value=1.5, step=0.25, label_visibility="collapsed")
        if c3.button("Log", use_container_width=True, type="primary"):
            log_hours(log_hrs, log_topic)
            st.success(f"Logged {log_hrs} hrs on {log_topic}")
            st.rerun()

        st.divider()
        st.markdown("### My todo list")
        new_task = st.text_input("Add task", label_visibility="collapsed", placeholder="Add a task…")
        if st.button("Add task") and new_task.strip():
            st.session_state.todos.append({"task": new_task, "done": False})
            persist()
            st.rerun()

        to_remove = []
        for i, todo in enumerate(st.session_state.todos):
            c1, c2, c3 = st.columns([0.07, 0.83, 0.10])
            new_done = c1.checkbox("", todo["done"], key=f"chk_{i}")
            if new_done != todo["done"]:
                st.session_state.todos[i]["done"] = new_done
                persist()
            label = f"~~{todo['task']}~~" if new_done else todo["task"]
            c2.markdown(label)
            if c3.button("✕", key=f"del_{i}"):
                to_remove.append(i)
        for i in reversed(to_remove):
            st.session_state.todos.pop(i)
            persist()
            st.rerun()

        done_todos = [t for t in st.session_state.todos if t["done"]]
        if done_todos and st.button("Archive completed tasks"):
            new_rows = pd.DataFrame([{"date": date.today().isoformat(), "task": t["task"]} for t in done_todos])
            st.session_state.completed_tasks = pd.concat([st.session_state.completed_tasks, new_rows], ignore_index=True)
            st.session_state.todos = [t for t in st.session_state.todos if not t["done"]]
            persist()
            st.rerun()

    with right:
        st.markdown("### Topic completion")
        for tk, td in TOPICS.items():
            done_m, total_m = topic_progress(tk)
            pct   = int(done_m / total_m * 100) if total_m else 0
            color = td["color"]
            st.markdown(
                f'<div style="margin-bottom:8px">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">'
                f'<span style="color:var(--color-text-primary)">{td["label"]}</span>'
                f'<span style="color:{color};font-weight:500">{done_m}/{total_m}</span>'
                f'</div>'
                f'<div style="height:6px;background:var(--color-background-secondary);border-radius:3px;overflow:hidden">'
                f'<div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>'
                f'</div></div>', unsafe_allow_html=True
            )

        st.divider()
        st.markdown("### Phase overview")
        today = date.today()
        for p in PHASES:
            if today > p["end"]:
                badge, bc = "Done", "#27500A"
            elif p["start"] <= today <= p["end"]:
                badge, bc = "Now", "#185FA5"
            else:
                badge, bc = "Upcoming", "#888780"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:12px">'
                f'<span style="padding:2px 7px;border-radius:4px;background:{bc}22;color:{bc};font-weight:500;white-space:nowrap">{badge}</span>'
                f'<span style="color:var(--color-text-primary)">{p["name"]}</span>'
                f'<span style="color:var(--color-text-tertiary);margin-left:auto">{p["hrs"]}h</span>'
                f'</div>', unsafe_allow_html=True
            )

# ─────────────────────────────────────────────────────────────────
# PAGE — CURRICULUM TRACKER
# ─────────────────────────────────────────────────────────────────

elif nav == "📚 Curriculum Tracker":
    st.markdown("## Curriculum Tracker")
    st.caption("Tick a module when EOC questions are done AND you can explain the concept from memory.")

    for priority in PRIORITY_ORDER:
        priority_topics = [(tk, td) for tk, td in TOPICS.items() if td["priority"] == priority]
        if not priority_topics:
            continue
        for tk, td in priority_topics:
            done_m, total_m = topic_progress(tk)
            pct = int(done_m / total_m * 100)
            with st.expander(f"**{td['label']}** — {priority} · {done_m}/{total_m} modules · {pct}%", expanded=(pct < 100)):
                for mod in td["modules"]:
                    mk           = get_module_key(tk, mod)
                    col1, col2, col3 = st.columns([3.5, 1.5, 1])
                    current_done = st.session_state.module_states.get(mk, False)
                    new_done     = col1.checkbox(mod, value=current_done, key=f"chk_{mk}")
                    if new_done != current_done:
                        st.session_state.module_states[mk] = new_done
                        if new_done:
                            st.session_state.completion_dates[mk] = date.today().isoformat()
                        persist()
                        st.rerun()
                    if new_done:
                        current_conf = st.session_state.conf_states.get(mk, 3)
                        new_conf = col2.select_slider(
                            "Confidence", options=[1,2,3,4,5],
                            format_func=lambda x: CONF_LABELS[x],
                            value=current_conf,
                            key=f"conf_{mk}",
                            label_visibility="collapsed"
                        )
                        if new_conf != current_conf:
                            st.session_state.conf_states[mk] = new_conf
                            persist()
                        cdate = st.session_state.completion_dates.get(mk, "")
                        col3.caption(cdate)

# ─────────────────────────────────────────────────────────────────
# PAGE — MOCK ANALYTICS
# ─────────────────────────────────────────────────────────────────

elif nav == "📊 Mock Analytics":
    st.markdown("## Mock Exam Analytics")
    subject_cols = ["FSA","Quant","Fixed_Income","Equity","Ethics","Derivatives","PM","Economics","Corp_Issuers","Alts"]

    st.markdown("#### Enter / update mock scores")
    edited = st.data_editor(
        st.session_state.mock_scores,
        hide_index=True,
        use_container_width=True,
        column_config={
            "mock":    st.column_config.TextColumn("Mock", disabled=True),
            "date":    st.column_config.TextColumn("Date"),
            "target":  st.column_config.NumberColumn("Target %"),
            "overall": st.column_config.NumberColumn("Overall %"),
            **{s: st.column_config.NumberColumn(s) for s in subject_cols},
        }
    )
    if not edited.equals(st.session_state.mock_scores):
        st.session_state.mock_scores = edited
        persist()

    taken = edited[edited["overall"] > 0]
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Score trajectory vs target")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edited["mock"], y=edited["target"], mode="lines+markers",
                                 name="Target", line=dict(dash="dash", color="#888780"), marker=dict(size=6)))
        if not taken.empty:
            fig.add_trace(go.Scatter(x=taken["mock"], y=taken["overall"], mode="lines+markers",
                                     name="Your score", line=dict(color="#185FA5", width=3), marker=dict(size=9)))
        fig.add_hline(y=65, line_dash="dot", line_color="#639922",
                      annotation_text="Pass confidence line", annotation_position="bottom right")
        fig.update_layout(yaxis_range=[0,100], template="plotly_white",
                          height=320, margin=dict(t=10,b=10,l=10,r=10),
                          legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Subject weakness heatmap (latest mock)")
        if not taken.empty:
            last        = taken.iloc[-1]
            scores_dict = {s: last.get(s, 0) for s in subject_cols}
            scores_dict = {k: v for k, v in scores_dict.items() if v > 0}
            if scores_dict:
                df_sub = pd.DataFrame(list(scores_dict.items()), columns=["Subject","Score"]).sort_values("Score")
                colors = ["#E24B4A" if s < 50 else "#BA7517" if s < 65 else "#639922" for s in df_sub["Score"]]
                fig2   = go.Figure(go.Bar(x=df_sub["Score"], y=df_sub["Subject"], orientation="h", marker_color=colors))
                fig2.add_vline(x=65, line_dash="dot", line_color="#888780")
                fig2.update_layout(xaxis_range=[0,100], template="plotly_white",
                                   height=320, margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Enter subject scores in the table above.")
        else:
            st.info("No mocks logged yet.")

    if not taken.empty:
        st.markdown("#### Score progression by subject")
        subject_labels = {
            "FSA":"FSA","Quant":"Quant","Fixed_Income":"Fixed Income","Equity":"Equity",
            "Ethics":"Ethics","Derivatives":"Derivatives","PM":"Portfolio Mgmt",
            "Economics":"Economics","Corp_Issuers":"Corp. Issuers","Alts":"Alternatives"
        }
        fig3 = go.Figure()
        for s, label in subject_labels.items():
            valid = taken[taken[s] > 0]
            if not valid.empty:
                fig3.add_trace(go.Scatter(x=valid["mock"], y=valid[s], name=label,
                                          mode="lines+markers", marker=dict(size=7)))
        fig3.add_hline(y=65, line_dash="dot", line_color="#888780")
        fig3.update_layout(yaxis_range=[0,100], height=380, template="plotly_white",
                           margin=dict(t=10,b=10), legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────────────────────────
# PAGE — ERROR LOG
# ─────────────────────────────────────────────────────────────────

elif nav == "❌ Error Log":
    st.markdown("## Error Logging Engine")
    st.caption("Log every wrong answer. This becomes your revision Bible in September–October.")

    with st.form("error_form", clear_on_submit=True):
        c1, c2   = st.columns(2)
        err_topic = c1.selectbox("Topic", [td["label"] for td in TOPICS.values()])
        err_type  = c2.selectbox("Error type", ["Concept gap","Formula error","Vignette misread",
                                                 "IFRS/GAAP confusion","Time pressure","Calculation slip"])
        tags = st.multiselect("Tags", [
            "#Binomial_Tree","#IFRS_vs_GAAP","#Pension_Accounting","#BSM_Model",
            "#DDM_Formula","#Term_Structure","#Ethics_Standards","#Vignette_Misread",
            "#Time_Management","#Credit_Models","#FX_Parity","#PE_Valuation"
        ])
        concept   = st.text_area("Correct concept — write it in your own words", height=80)
        submitted = st.form_submit_button("Log Error", type="primary", use_container_width=True)
        if submitted and concept.strip():
            new_row = pd.DataFrame([{
                "date": date.today().isoformat(), "topic": err_topic,
                "error_type": err_type, "concept": concept, "tags": ", ".join(tags),
            }])
            st.session_state.error_log = pd.concat([st.session_state.error_log, new_row], ignore_index=True)
            persist()
            st.success("Error logged.")

    st.divider()
    df_err = st.session_state.error_log.copy()
    if not df_err.empty:
        col1, col2   = st.columns([2,1])
        filter_topic = col1.selectbox("Filter by topic", ["All"] + df_err["topic"].unique().tolist())
        filter_type  = col2.selectbox("Filter by type",  ["All"] + df_err["error_type"].unique().tolist())
        if filter_topic != "All": df_err = df_err[df_err["topic"]      == filter_topic]
        if filter_type  != "All": df_err = df_err[df_err["error_type"] == filter_type]
        st.dataframe(df_err.sort_values("date", ascending=False).reset_index(drop=True),
                     use_container_width=True, height=400)
        freq    = st.session_state.error_log.groupby("topic").size().reset_index(name="count").sort_values("count", ascending=True)
        fig_err = go.Figure(go.Bar(x=freq["count"], y=freq["topic"], orientation="h", marker_color="#E24B4A"))
        fig_err.update_layout(title="Error frequency by topic", template="plotly_white",
                              height=300, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig_err, use_container_width=True)
    else:
        st.info("No errors logged yet. Start logging from your Q-bank and mock sessions.")

# ─────────────────────────────────────────────────────────────────
# PAGE — HOURS & VELOCITY
# ─────────────────────────────────────────────────────────────────

elif nav == "📈 Hours & Velocity":
    st.markdown("## Hours & Velocity")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total logged",  f"{st.session_state.hours_logged:.1f} hrs")
    c2.metric("Target",        f"{st.session_state.target_hours} hrs")
    c3.metric("Remaining",     f"{hours_remaining():.1f} hrs")
    c4.metric("Required pace", f"{required_daily_burn()} hrs/day")

    st.divider()
    st.markdown("#### Log hours manually")
    c1, c2, c3     = st.columns([2,1,1])
    manual_topic   = c1.selectbox("Topic", [t["label"] for t in TOPICS.values()], key="manual_topic")
    manual_hrs     = c2.number_input("Hours", min_value=0.25, max_value=10.0, value=1.5, step=0.25, key="manual_hrs")
    if c3.button("Log", type="primary", use_container_width=True):
        log_hours(manual_hrs, manual_topic)
        st.success(f"Logged {manual_hrs} hrs")
        st.rerun()

    st.divider()
    df_dl = st.session_state.daily_logs.copy()
    if not df_dl.empty and "date" in df_dl.columns:
        df_dl["date"]  = pd.to_datetime(df_dl["date"], errors="coerce")
        df_dl          = df_dl.dropna(subset=["date"])
        df_dl["hours"] = pd.to_numeric(df_dl["hours"], errors="coerce").fillna(0)
        df_dl          = df_dl.sort_values("date")

        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(x=df_dl["date"], y=df_dl["hours"], marker_color="#185FA5", name="Daily hours"))
        fig_daily.add_hline(y=required_daily_burn(), line_dash="dash", line_color="#E24B4A",
                            annotation_text=f"Required {required_daily_burn()} hrs/day",
                            annotation_position="top right")
        fig_daily.update_layout(title="Daily study hours", template="plotly_white",
                                height=300, margin=dict(t=40,b=10))
        st.plotly_chart(fig_daily, use_container_width=True)

        cum = df_dl.groupby("date")["hours"].sum().reset_index()
        cum["cumulative"] = cum["hours"].cumsum()
        total_days  = (st.session_state.exam_date  - st.session_state.start_date).days
        total_hours = st.session_state.target_hours
        ideal_dates = [st.session_state.start_date + timedelta(days=i) for i in range(total_days+1)]
        ideal_hours = [total_hours * i / total_days for i in range(total_days+1)]

        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(x=ideal_dates, y=ideal_hours, mode="lines",
                                     name="Ideal trajectory", line=dict(dash="dash", color="#888780")))
        fig_cum.add_trace(go.Scatter(x=cum["date"], y=cum["cumulative"], mode="lines",
                                     name="Actual", line=dict(color="#639922", width=3)))
        fig_cum.update_layout(title="Cumulative hours vs ideal trajectory", yaxis_title="Hours",
                              template="plotly_white", height=320, margin=dict(t=40,b=10),
                              legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_cum, use_container_width=True)
    else:
        st.info("Start logging sessions to see your velocity charts.")

# ─────────────────────────────────────────────────────────────────
# PAGE — PHASE CALENDAR
# ─────────────────────────────────────────────────────────────────

elif nav == "📅 Phase Calendar":
    st.markdown("## Phase Calendar")
    today = date.today()
    for p in PHASES:
        if today > p["end"]:
            status, badge_color = "Completed", "#27500A"
        elif p["start"] <= today <= p["end"]:
            days_in    = (today - p["start"]).days + 1
            days_total = (p["end"] - p["start"]).days + 1
            status, badge_color = f"Active — day {days_in} of {days_total}", "#185FA5"
        else:
            days_to = (p["start"] - today).days
            status, badge_color = f"Starts in {days_to} days", "#888780"

        border = "2px solid #185FA5" if p["start"] <= today <= p["end"] else "0.5px solid #D3D1C7"
        st.markdown(
            f'<div style="border:{border};border-radius:10px;padding:14px 18px;margin-bottom:10px">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">'
            f'<span style="font-size:15px;font-weight:500;color:var(--color-text-primary)">{p["name"]}</span>'
            f'<span style="font-size:12px;font-weight:500;padding:3px 10px;border-radius:4px;background:{badge_color}22;color:{badge_color}">{status}</span>'
            f'</div>'
            f'<div style="font-size:13px;color:var(--color-text-secondary)">'
            f'{p["start"].strftime("%b %d")} – {p["end"].strftime("%b %d, %Y")} · '
            f'{(p["end"]-p["start"]).days+1} days · <b>{p["hrs"]} hrs</b> · '
            f'Topics: {", ".join(TOPICS.get(t,{}).get("label",t) for t in p["topics"])}'
            f'</div></div>', unsafe_allow_html=True
        )
