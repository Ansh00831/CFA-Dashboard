from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Any

@dataclass
class Phase:
    name: str
    start: date
    end: date
    hrs: int
    topics: List[str]
    # New attribute to hold the detailed tasks and module mapping
    tasks: List[Dict[str, Any]] = field(default_factory=list)

TOPICS = {
    "FSA": {
        "label": "Financial Statement Analysis", "priority": "CRITICAL", "color": "#E24B4A", "modules":[
            "Intercorporate Investments — equity method vs consolidation",
            "Intercorporate Investments — business combinations, IFRS 3 vs GAAP",
            "Employee Compensation — pensions (IAS 19 vs US GAAP)",
            "Share-based compensation",
            "Multinational Operations — current rate vs temporal method",
            "Analysis of Financial Institutions",
        ],
    },
    "Quant": {
        "label": "Quantitative Methods", "priority": "VERY HIGH", "color": "#BA7517", "modules":[
            "Basics of multiple regression and assumptions",
            "Evaluating regression model fit, ANOVA, hypothesis testing",
            "Model misspecification — multicollinearity, heteroskedasticity, serial correlation",
            "Extensions of Multiple regression",
            "Time-series analysis — ARMA, random walks, unit roots, cointegration",
            "Machine learning for investment analysis",
            "Big Data Projects"
        ],
    },
    "Fixed_Income": {
        "label": "Fixed Income", "priority": "VERY HIGH", "color": "#BA7517", "modules":[
            "Term structure and interest rate dynamics",
            "Arbitrage-free valuation — binomial trees, OAS",
            "Valuation of bonds with embedded options",
            "Credit analysis models — structural and reduced-form",
            "Credit default swaps",
        ],
    },
    "Equity": {
        "label": "Equity Valuation", "priority": "MAINTAIN", "color": "#639922", "modules":[
            "Equity valuation applications and processes",
            "Discounted dividend valuation — DDM, H-model, multi-stage",
            "Free cash flow valuation — FCFF and FCFE",
            "Market-based valuation — P/E, P/B, EV/EBITDA",
            "Residual income valuation",
            "Private company valuation",
        ],
    },
    "Ethics": {
        "label": "Ethics & Professional Standards", "priority": "HIGH", "color": "#27500A", "modules":[
            "Code of Ethics and Standards of Professional Conduct",
            "Guidance for Standards I–VII",
            "Application of Code and Standards: Level II",
        ],
    },
    "Derivatives": {
        "label": "Derivatives", "priority": "HIGH", "color": "#185FA5", "modules":[
            "Forward commitments — forwards, futures, swaps (pricing and valuation)",
            "Contingent claims — BSM model, Greeks, binomial trees, interest rate options",
        ],
    },
    "PM": {
        "label": "Portfolio Management", "priority": "VERY HIGH", "color": "#3C3489", "modules":[
            "Economics and investment markets — macro factor models",
            "Analysis of Active Portfolio Management — performance attribution, appraisal ratios",
            "Exchange-Traded Funds - Mechanics and Application",
            "Using Multifactor Model",
            "Measuring and Managing Market Risk",
            "Backtesting and simulation — look-ahead, survivorship, data-snooping biases",
        ],
    },
    "Economics": {
        "label": "Economics", "priority": "MEDIUM", "color": "#BA7517", "modules":[
            "Currency exchange rates — CIRP, UIRP, PPP, Fisher, carry trades",
            "Economic growth and investment decision — Solow model, convergence",
        ],
    },
    "Corp_Issuers": {
        "label": "Corporate Issuers", "priority": "MEDIUM", "color": "#639922", "modules":[
            "Dividends and share repurchases — signalling, irrelevance, residual model",
            "ESG factors in investment analysis",
            "Cost of Capital: Advanced Topics",
            "Corporate Restructuring",
        ],
    },
    "Alts": {
        "label": "Alternative Investments", "priority": "MAINTAIN", "color": "#639922", "modules":[
            "Private capital — PE/VC, J-curve, NAV, carried interest, IRR metrics",
            "Real estate — direct/indirect, NOI, cap rate, REIT valuation",
            "Infrastructure and natural resources",
            "Hedge funds — strategies and risk metrics",
        ],
    },
}

PRIORITY_ORDER =["CRITICAL","VERY HIGH","HIGH","MEDIUM","MAINTAIN"]

PHASES =[
    Phase("Foundation Sprint", date(2026,4,13), date(2026,4,30), 60,["Quant","FSA"], tasks=[
        {"period": "Apr 13–17", "title": "Quant — Part 1", "desc": "Basics of multiple regression, ANOVA, hypothesis testing, multicollinearity.", "hrs": 18, "modules":[
            "Basics of multiple regression and assumptions",
            "Evaluating regression model fit, ANOVA, hypothesis testing",
            "Model misspecification — multicollinearity, heteroskedasticity, serial correlation"]},
        {"period": "Apr 18–23", "title": "Quant — Part 2", "desc": "Time-series analysis (ARMA, random walks) and machine learning.", "hrs": 18, "modules":[
            "Time-series analysis — ARMA, random walks, unit roots, cointegration",
            "Machine learning for investment analysis"]},
        {"period": "Apr 24–30", "title": "FSA — Intercorporate Investments", "desc": "Equity method vs consolidation, IFRS 3 vs GAAP. Hardest FSA chapter.", "hrs": 24, "modules":[
            "Intercorporate Investments — equity method vs consolidation",
            "Intercorporate Investments — business combinations, IFRS 3 vs GAAP"]}
    ]),
    Phase("Maintenance Mode", date(2026,5,1), date(2026,5,14), 14,["FSA"], tasks=[
        {"period": "May 1–14", "title": "End-semesters — Review Only", "desc": "No new material. 20 min flashcards, 40 min EOC revision. Recreate IFRS vs GAAP table from memory.", "hrs": 14, "modules": []}
    ]),
    Phase("Power Window", date(2026,5,15), date(2026,5,31), 130, ["FSA","Fixed_Income","Equity"], tasks=[
        {"period": "May 15–18", "title": "FSA — Complete", "desc": "Pensions, share-based compensation, multinational ops.", "hrs": 30, "modules":[
            "Employee Compensation — pensions (IAS 19 vs US GAAP)",
            "Share-based compensation",
            "Multinational Operations — current rate vs temporal method",
            "Analysis of Financial Institutions"]},
        {"period": "May 19–24", "title": "Fixed Income — Complete", "desc": "Term structure, binomial trees, credit models, CDS.", "hrs": 48, "modules":[
            "Term structure and interest rate dynamics",
            "Arbitrage-free valuation — binomial trees, OAS",
            "Valuation of bonds with embedded options",
            "Credit analysis models — structural and reduced-form",
            "Credit default swaps"]},
        {"period": "May 25–31", "title": "Equity Valuation — Complete", "desc": "DDM, FCF, residual income, private company valuation.", "hrs": 52, "modules":[
            "Equity valuation applications and processes", "Industry and company analysis", "Discounted dividend valuation — DDM, H-model, multi-stage", "Free cash flow valuation — FCFF and FCFE", "Market-based valuation — P/E, P/B, EV/EBITDA", "Residual income valuation", "Private company valuation"]}
    ]),
    Phase("Internship Grind I", date(2026,6,1), date(2026,6,30), 88, ["Ethics","Derivatives","FSA"], tasks=[
        {"period": "Week 1 (Jun 1–7)", "title": "Ethics & GIPS", "desc": "Read Standards with case studies. 15 scenario questions per evening.", "hrs": 22, "modules":[
            "Standards I–II — Professionalism, Capital Market Integrity", "Standards III–IV — Duties to Clients and Employers", "Standards V–VI — Investment Analysis, Conflicts of Interest", "Standard VII — Responsibilities as CFA Member/Candidate", "GIPS — fundamentals and composites"]},
        {"period": "Week 2 (Jun 8–14)", "title": "Derivatives — Forward commitments", "desc": "Pricing and valuation of forwards, futures, swaps. No-arbitrage pricing.", "hrs": 22, "modules":[
            "Forward commitments — forwards, futures, swaps (pricing and valuation)"]},
        {"period": "Week 3 (Jun 15–21)", "title": "Derivatives — Contingent claims", "desc": "Options valuation (BSM, Greeks), binomial model.", "hrs": 22, "modules":[
            "Contingent claims — BSM model, Greeks, binomial trees, interest rate options"]},
        {"period": "Week 4 (Jun 22–30)", "title": "FSA Second Pass", "desc": "Re-read intercorporate investments AND pensions (weakest spots).", "hrs": 22, "modules":[
            "Intercorporate Investments — equity method vs consolidation", "Intercorporate Investments — business combinations, IFRS 3 vs GAAP", "Employee Compensation — pensions (IAS 19 vs US GAAP)"]}
    ]),
    Phase("Completing Curriculum", date(2026,7,1), date(2026,7,31), 88, ["PM","Corp_Issuers","Economics"], tasks=[
        {"period": "Week 1 (Jul 1–7)", "title": "Portfolio Management — Part 1", "desc": "Asset allocation frameworks, MVO, liability-relative.", "hrs": 22, "modules":[
            "Overview of asset allocation — strategic vs tactical frameworks", "Principles of asset allocation — MVO, Black-Litterman, liability-relative", "Asset allocation with real-world constraints"]},
        {"period": "Week 2 (Jul 8–14)", "title": "Portfolio Management — Part 2", "desc": "ETFs, backtesting biases, macro factors.", "hrs": 22, "modules":[
            "Exchange-traded funds — creation/redemption, premium/discount", "Backtesting and simulation — look-ahead, survivorship, data-snooping biases", "Economics and investment markets — macro factor models"]},
        {"period": "Week 3 (Jul 15–21)", "title": "Corporate Issuers", "desc": "Dividends, ESG integration, corporate governance.", "hrs": 22, "modules":[
            "Dividends and share repurchases — signalling, irrelevance, residual model", "ESG factors in investment analysis", "Corporate governance and agency issues"]},
        {"period": "Week 4 (Jul 22–31)", "title": "Economics", "desc": "Currency exchange rates (parity conditions), economic growth.", "hrs": 22, "modules":[
            "Currency exchange rates — CIRP, UIRP, PPP, Fisher, carry trades", "Economic growth and investment decision — Solow model, convergence"]}
    ]),
    Phase("Alts + Practice Pivot", date(2026,8,1), date(2026,8,31), 88, ["Alts","Q-bank","Mock 1"], tasks=[
        {"period": "Week 1 (Aug 1–7)", "title": "Alternative Investments", "desc": "Private capital, real estate, infrastructure, hedge funds.", "hrs": 22, "modules":[
            "Private capital — PE/VC, J-curve, NAV, carried interest, IRR metrics", "Real estate — direct/indirect, NOI, cap rate, REIT valuation", "Infrastructure and natural resources", "Hedge funds — strategies and risk metrics"]},
        {"period": "Week 2 (Aug 8–14)", "title": "Q-bank Launch — FSA & Quant", "desc": "Target 50 questions/day. Every wrong answer mapped to Error Log.", "hrs": 22, "modules":[]},
        {"period": "Week 3 (Aug 15–21)", "title": "Q-bank — Ethics, Deriv, PM, Equity", "desc": "Rotate focus. 18 minutes max per 6-question item set.", "hrs": 22, "modules":[]},
        {"period": "Week 4 (Aug 22–31)", "title": "Mock Exam 1 + Deep Review", "desc": "First full mock under strict timed conditions. Baseline scoring.", "hrs": 22, "modules":[]}
    ]),
    Phase("Mock & Revision Cycle", date(2026,9,1), date(2026,9,30), 66, ["Q-bank","Error Log","Mock 2 & 3"], tasks=[
        {"period": "Week 1 (Sep 1–7)", "title": "Error Log Revision — FSA & Quant", "desc": "Rework calculations from Mock 1 errors.", "hrs": 16, "modules": []},
        {"period": "Week 2 (Sep 8–14)", "title": "Mock Exam 2 + Fixed Income", "desc": "Deep dive into Fixed Income post-mock (binomial trees, CDS).", "hrs": 16, "modules":[]},
        {"period": "Week 3 (Sep 15–21)", "title": "Q-bank — Lighter Topics", "desc": "Target Economics, Corp Issuers, Alts. 60 Qs/day.", "hrs": 18, "modules":[]},
        {"period": "Week 4 (Sep 22–30)", "title": "Mock Exam 3 + Master Formula Sheet", "desc": "Build one A4 page per topic handwritten from memory.", "hrs": 16, "modules":[]}
    ]),
    Phase("Final Consolidation", date(2026,10,1), date(2026,10,31), 44,["Ethics","Q-bank","Mock 4"], tasks=[
        {"period": "Week 1 (Oct 1–7)", "title": "Mock Exam 4 + Comprehensive Review", "desc": "Aim for 70%+. Targeted Q-bank on worst two topics.", "hrs": 12, "modules": []},
        {"period": "Week 2 (Oct 8–14)", "title": "Ethics Deep Dive", "desc": "Re-read all 6 Standards. 50 scenario questions.", "hrs": 10, "modules":[]},
        {"period": "Week 3 (Oct 15–21)", "title": "Targeted Weakness Drilling", "desc": "60 targeted Q-bank questions/day on your bottom 2 topics.", "hrs": 12, "modules":[]},
        {"period": "Week 4 (Oct 22–31)", "title": "Consolidation & Hard Stop", "desc": "Light Q-bank. October 31 is a hard stop on new material.", "hrs": 10, "modules":[]}
    ]),
    Phase("Final Sprint", date(2026,11,1), date(2026,11,15), 22, ["Recall","Mock 5","Ethics","REST"], tasks=[
        {"period": "Nov 1–5", "title": "Active Recall Only", "desc": "Handwritten notes, formulas from memory. No textbooks.", "hrs": 10, "modules": []},
        {"period": "Nov 6–8", "title": "Final Mock Exam 5", "desc": "Nov 8: Last full mock. Review errors same evening only.", "hrs": 8, "modules":[]},
        {"period": "Nov 9–12", "title": "Ethics Only — Final Read", "desc": "Read Standards one final time. Protect your sleep.", "hrs": 4, "modules":[]},
        {"period": "Nov 13–14", "title": "Complete Rest", "desc": "No study. Sleep 8 hours. Prepare passport and calculator.", "hrs": 0, "modules":[]}
    ]),
]
