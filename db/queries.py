"""
Database Queries
"""
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta
from models.session import SpacedRepItem
from models.study_plan import TOPICS, PRIORITY_ORDER

DB_PATH = "study.db"

def _execute(query, params=(), fetch=False, commit=False):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(query, params)
            if commit:
                conn.commit()
            if fetch == "all":
                return c.fetchall()
            elif fetch == "one":
                return c.fetchone()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        return None

# --- Session & Hours ---
def log_hours(hrs: float, topic: str = "General"):
    today_str = date.today().isoformat()
    existing = _execute("SELECT hours FROM daily_logs WHERE date=?", (today_str,), fetch="one")
    if existing:
        _execute("UPDATE daily_logs SET hours = hours + ?, topic = ? WHERE date = ?", (hrs, topic, today_str), commit=True)
    else:
        _execute("INSERT INTO daily_logs (date, hours, topic) VALUES (?,?,?)", (today_str, hrs, topic), commit=True)

def get_hours_logged() -> float:
    res = _execute("SELECT SUM(hours) FROM daily_logs", fetch="one")
    return res[0] if res and res[0] else 0.0

def get_streak() -> int:
    df = pd.read_sql("SELECT date, hours FROM daily_logs WHERE hours > 0", sqlite3.connect(DB_PATH))
    if df.empty: return 0
    df["date"] = pd.to_datetime(df["date"]).dt.date
    logged_days = set(df["date"])
    
    streak = 0
    check = date.today()
    if check not in logged_days:
        check -= timedelta(days=1)
    
    while check in logged_days:
        streak += 1
        check -= timedelta(days=1)
    return streak

def get_pace(days: int) -> float:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    res = _execute("SELECT SUM(hours) FROM daily_logs WHERE date >= ?", (cutoff,), fetch="one")
    total = res[0] if res and res[0] else 0.0
    return round(total / days, 2)

def required_daily_burn() -> float:
    remaining = max(0, 490.0 - get_hours_logged())
    days_left = max(1, (date(2026, 11, 15) - date.today()).days)
    return round(remaining / days_left, 2)

# --- Timer ---
def start_timer():
    ts = datetime.now().isoformat()
    _execute("REPLACE INTO global_settings (key, value) VALUES ('timer_start', ?)", (ts,), commit=True)

def get_timer_start():
    res = _execute("SELECT value FROM global_settings WHERE key='timer_start'", fetch="one")
    return datetime.fromisoformat(res[0]) if res else None

def clear_timer():
    _execute("DELETE FROM global_settings WHERE key='timer_start'", commit=True)


# --- Modules ---
def update_module_state(topic_key: str, mod: str, is_done: bool):
    today = date.today().isoformat()
    _execute("""
        INSERT INTO module_states (topic_key, module, is_done, completion_date) 
        VALUES (?,?,?,?) ON CONFLICT(topic_key, module) 
        DO UPDATE SET is_done=excluded.is_done, completion_date=excluded.completion_date
    """, (topic_key, mod, 1 if is_done else 0, today), commit=True)

def update_module_conf(topic_key: str, mod: str, conf: int):
    _execute("""
        UPDATE module_states SET confidence=? WHERE topic_key=? AND module=?
    """, (conf, topic_key, mod), commit=True)

def get_spaced_rep_queue():
    rows = _execute("SELECT topic_key, module, confidence, completion_date FROM module_states WHERE is_done=1", fetch="all")
    if not rows: return []
    
    today = date.today()
    queue =[]
    for tk, mod, conf, cdate_str in rows:
        days_ago = (today - datetime.strptime(cdate_str, "%Y-%m-%d").date()).days if cdate_str else 99
        if conf <= 2 or (conf == 3 and days_ago >= 14) or (conf == 4 and days_ago >= 30):
            queue.append(SpacedRepItem(
                topic=TOPICS.get(tk, {}).get("label", tk),
                module=mod, conf=conf, days_ago=days_ago, urgency=(3 - conf) * 10 + days_ago
            ))
    queue.sort(key=lambda x: -x.urgency)
    return queue[:5]

def get_all_module_states():
    rows = _execute("SELECT topic_key, module, is_done FROM module_states", fetch="all")
    if not rows: return {}
    return {f"{r[0]}||{r[1]}": bool(r[2]) for r in rows}

def get_weakest_subjects():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM mock_scores WHERE overall > 0", conn)
    if df.empty: return []
    last = df.iloc[-1]
    subjects =["FSA","Quant","Fixed_Income","Equity","Ethics","Derivatives","PM","Economics","Corp_Issuers","Alts"]
    scores = {s: last[s] for s in subjects if s in last and last[s] > 0}
    sorted_subs = sorted(scores.items(), key=lambda x: x[1])
    return sorted_subs[:3]


# --- New Todo System Logic ---
def get_active_todos_df():
    """Returns active (undone) tasks as a Pandas DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, task, due_date, completed_date, done FROM todos WHERE done = 0", conn)
    
    # FIX: Convert SQLite string dates to Pandas date objects so Streamlit DateColumn works
    # errors='coerce' turns empty/invalid strings into NaT (Not a Time)
    df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.date
    df['completed_date'] = pd.to_datetime(df['completed_date'], errors='coerce').dt.date
    
    # Also ensure 'done' is explicitly boolean so the CheckboxColumn works perfectly
    df['done'] = df['done'].astype(bool)
    
    return df

def get_completed_todos_df():
    """Returns finished tasks for the log"""
    conn = sqlite3.connect(DB_PATH)
    # Added id, due_date, and done so we can edit it and send it back to the sync function
    df = pd.read_sql("SELECT id, task, due_date, completed_date, done FROM todos WHERE done = 1 ORDER BY completed_date DESC", conn)
    
    df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.date
    df['completed_date'] = pd.to_datetime(df['completed_date'], errors='coerce').dt.date
    df['done'] = df['done'].astype(bool)
    return df

def sync_todos_df(df_edited: pd.DataFrame):
    """Takes the edited DataFrame from Streamlit and syncs it securely to SQLite"""
    with sqlite3.connect(DB_PATH) as conn:
        for _, row in df_edited.iterrows():
            is_done = int(row['done'])
            comp_date = row['completed_date']
            due_date = row['due_date']
            
            # 1. Clean Pandas NaT (empty date) values
            if pd.isna(comp_date): comp_date = None
            if pd.isna(due_date): due_date = None
            
            # 2. Logic for checking/unchecking
            if not is_done:
                comp_date = None # <-- NEW: If unchecked, wipe the completed date
            elif is_done and not comp_date:
                comp_date = date.today().isoformat()
            
            # 3. Convert dates back to ISO strings
            if comp_date and not isinstance(comp_date, str):
                comp_date = comp_date.isoformat()
            if due_date and not isinstance(due_date, str):
                due_date = due_date.isoformat()
            
            conn.execute("""
                UPDATE todos SET 
                task=?, due_date=?, completed_date=?, done=?
                WHERE id=?
            """, (row['task'], due_date, comp_date, is_done, row['id']))
        conn.commit()
def add_todo(task: str, due: str = None):
    if due is None:
        due = date.today().isoformat()
    _execute("INSERT INTO todos (task, due_date, done) VALUES (?, ?, 0)", (task, due), commit=True)

def auto_populate_daily_todos():
    """Finds the next unread module and adds it to the Todo list for today if not already there"""
    today_str = date.today().isoformat()
    
    # 1. Check if we already auto-added something today
    last_added = _execute("SELECT value FROM global_settings WHERE key='last_auto_todo_date'", fetch="one")
    if last_added and last_added[0] == today_str:
        return # Already populated today

    # 2. Find next unread module
    states = get_all_module_states()
    next_mod = None
    for priority in PRIORITY_ORDER:
        for tk, td in TOPICS.items():
            if td["priority"] != priority: continue
            for mod in td["modules"]:
                if not states.get(f"{tk}||{mod}", False):
                    next_mod = f"Read Module: {mod} ({td['label']})"
                    break
            if next_mod: break
        if next_mod: break
    
    # 3. Add to list and record date
    if next_mod:
        # Prevent exact duplicates if it's already sitting undone
        existing = _execute("SELECT id FROM todos WHERE task=? AND done=0", (next_mod,), fetch="one")
        if not existing:
            add_todo(next_mod, today_str)
            _execute("REPLACE INTO global_settings (key, value) VALUES ('last_auto_todo_date', ?)", (today_str,), commit=True)