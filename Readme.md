# CFA Level 2 Command Center 📈

A personal study dashboard for CFA Level 2 candidates to track curriculum progress, daily study hours, mock exam scores, and error logs. 

### Features
* **Spaced Repetition Engine**: Flags weak modules for review.
* **Velocity Tracking**: Calculates required daily burn rate vs. actual pace.
* **SQLite Backend**: Acid-compliant, fast, single-file database (`study.db`).
* **Error Log**: Centralized repository for tracking weaknesses.

### Installation & Execution
```bash
pip install -r requirements.txt
streamlit run cfa_dashboard.py

**`requirements.txt`**
```text
streamlit>=1.36.0
pandas>=2.0.0
plotly>=5.15.0