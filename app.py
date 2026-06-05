import streamlit as st
import numpy as np
import pandas as pd

from database.db_connection import get_connection
from src.predit import make_prediction

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Loan Approval Predictor",
    page_icon="🏦",
    layout="centered",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #F1F5F9; }

/* Header */
.app-header { text-align: center; padding: 2rem 1rem 1rem; margin-bottom: 0.5rem; }
.app-header .icon { font-size: 2.8rem; }
.app-header h1 { font-size: 1.9rem; font-weight: 700; color: #1E293B; margin: 0.4rem 0 0.25rem; }
.app-header p  { font-size: 0.92rem; color: #64748B; margin: 0; }

/* Section cards */
.form-section {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.6rem 1.6rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.03);
    margin-bottom: 1rem;
}
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    margin: 0 0 1.1rem;
}

/* Credit score badge */
.score-badge {
    display: inline-block;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.4rem;
}
.badge-exc  { background:#D1FAE5; color:#065F46; }
.badge-good { background:#DBEAFE; color:#1E40AF; }
.badge-fair { background:#FEF9C3; color:#92400E; }
.badge-poor { background:#FEE2E2; color:#991B1B; }

/* Metric row */
.metric-row { display:flex; gap:0.75rem; margin: 0.8rem 0 1rem; }
.metric-box {
    flex:1; background:#F8FAFC;
    border:1px solid #E2E8F0;
    border-radius:12px; padding:0.85rem 0.5rem;
    text-align:center;
}
.metric-box .mlabel { font-size:0.68rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#94A3B8; }
.metric-box .mvalue { font-size:1.3rem; font-weight:700; color:#1E293B; margin:0.18rem 0; }
.metric-box .mhint  { font-size:0.7rem; font-weight:500; }
.ok  { color:#10B981; }
.bad { color:#EF4444; }

/* Results */
.result-approved {
    background:#ECFDF5; border:1.5px solid #6EE7B7;
    border-radius:14px; padding:1.8rem 1.5rem;
    text-align:center; margin-bottom:1rem;
}
.result-approved .ricon { font-size:2.4rem; }
.result-approved h2 { color:#065F46; font-size:1.55rem; font-weight:700; margin:0.4rem 0 0.25rem; }
.result-approved p  { color:#047857; margin:0; font-size:0.9rem; }

.result-rejected {
    background:#FEF2F2; border:1.5px solid #FCA5A5;
    border-radius:14px; padding:1.8rem 1.5rem;
    text-align:center; margin-bottom:1rem;
}
.result-rejected .ricon { font-size:2.4rem; }
.result-rejected h2 { color:#991B1B; font-size:1.55rem; font-weight:700; margin:0.4rem 0 0.25rem; }
.result-rejected p  { color:#B91C1C; margin:0; font-size:0.9rem; }

/* Decision breakdown */
.breakdown-card {
    background:#FFFFFF; border-radius:14px; padding:1.4rem;
    box-shadow:0 1px 3px rgba(0,0,0,0.06); margin-bottom:1rem;
}
.breakdown-card h4 { font-size:0.82rem; font-weight:600; color:#374151; margin:0 0 0.75rem; }
.reason-row {
    display:flex; align-items:flex-start; gap:0.55rem;
    font-size:0.86rem; color:#4B5563; padding:0.45rem 0;
    border-bottom:1px solid #F1F5F9; line-height:1.4;
}
.reason-row:last-child { border-bottom:none; }

/* Button */
div.stButton > button {
    width:100%; padding:0.82rem 1rem;
    font-size:0.98rem; font-weight:600;
    border-radius:12px !important;
    background: linear-gradient(135deg,#3B82F6,#6366F1) !important;
    color:white !important; border:none !important;
    letter-spacing:0.01em; transition:opacity 0.2s;
}
div.stButton > button:hover { opacity:0.86; }

/* Inputs */
.stNumberInput input, .stSelectbox select { border-radius:10px !important; }

#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="icon">🏦</div>
    <h1>Loan Approval Predictor</h1>
    <p>Fill in the applicant details below to receive an instant AI-powered decision</p>
</div>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — Financial Info
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="section-label">💰 Financial Information</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    annual_income = st.number_input(
        "Annual Income ($)", min_value=5_000, max_value=500_000,
        value=65_000, step=1_000,
        help="Combined yearly income of applicant and co-applicant."
    )
with c2:
    loan_amount = st.number_input(
        "Loan Amount ($)", min_value=5_000, max_value=1_000_000,
        value=120_000, step=5_000,
        help="Total loan amount being requested."
    )

existing_debt = st.number_input(
    "Existing Annual Debt ($)", min_value=0, max_value=300_000,
    value=15_000, step=1_000,
    help="Total yearly debt obligations — credit cards, car loans, student loans, etc."
)

st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SECTION 2 — Profile
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="section-label">📋 Applicant Profile</div>', unsafe_allow_html=True)

credit_score = st.slider("Credit Score (FICO)", 300, 850, 700, step=10)

# Dynamic rating badge
if credit_score >= 740:
    bcls, btxt = "badge-exc",  "⭐ Excellent  (740 – 850)"
elif credit_score >= 670:
    bcls, btxt = "badge-good", "👍 Good  (670 – 739)"
elif credit_score >= 580:
    bcls, btxt = "badge-fair", "⚠️ Fair  (580 – 669)"
else:
    bcls, btxt = "badge-poor", "🚨 Poor  (300 – 579)"

st.markdown(f'<span class="score-badge {bcls}">{btxt}</span>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

c3, c4 = st.columns(2)
with c3:
    employment = st.selectbox(
        "Employment Status",
        ["Employed", "Self-Employed", "Unemployed"],
        help="Current employment situation of the primary applicant."
    )
with c4:
    education = st.selectbox(
        "Education Level",
        ["Graduate", "Not Graduate"],
        help="Highest academic qualification achieved."
    )

st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# LIVE RISK METRICS (always visible)
# ═══════════════════════════════════════════════════════════════
dti   = (existing_debt / annual_income * 100) if annual_income > 0 else 0
lti   = (loan_amount / annual_income) if annual_income > 0 else 0
cover = min((annual_income / existing_debt) if existing_debt > 0 else 99, 99)

st.markdown(f"""
<div class="metric-row">
    <div class="metric-box">
        <div class="mlabel">Debt-to-Income</div>
        <div class="mvalue">{dti:.1f}%</div>
        <div class="mhint {'ok' if dti <= 40 else 'bad'}">
            {"✅ Safe" if dti <= 40 else "🚨 Too High"}
        </div>
    </div>
    <div class="metric-box">
        <div class="mlabel">Loan-to-Income</div>
        <div class="mvalue">{lti:.1f}x</div>
        <div class="mhint {'ok' if lti <= 5 else 'bad'}">
            {"✅ OK" if lti <= 5 else "⚠️ High"}
        </div>
    </div>
    <div class="metric-box">
        <div class="mlabel">Income Cover</div>
        <div class="mvalue">{cover:.1f}x</div>
        <div class="mhint ok">Annual multiples</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SUBMIT BUTTON
# ═══════════════════════════════════════════════════════════════
run = st.button("🔍  Check Loan Eligibility")

if run:
    emp_map = {"Employed": 0, "Self-Employed": 1, "Unemployed": 2}
    edu_map = {"Graduate": 1, "Not Graduate": 0}
    loan_id = f"APP-{np.random.randint(100_000, 999_999)}"

    input_vec = [
        float(annual_income),
        int(credit_score),
        float(loan_amount),
        int(emp_map[employment]),
        int(edu_map[education]),
        float(existing_debt),
    ]

    with st.spinner("Analyzing application…"):
        status, prob = make_prediction(input_vec, loan_id)

    st.session_state.result = {
        "status": status, "prob": prob,
        "credit_score": credit_score,
        "dti": dti, "lti": lti,
        "employment": employment,
    }

# ═══════════════════════════════════════════════════════════════
# RESULT DISPLAY
# ═══════════════════════════════════════════════════════════════
if st.session_state.result:
    r = st.session_state.result
    st.markdown("---")

    if r["status"] == "Approved":
        st.markdown(f"""
        <div class="result-approved">
            <div class="ricon">✅</div>
            <h2>Loan Approved</h2>
            <p>Approval confidence &nbsp;•&nbsp; <strong>{r['prob']*100:.1f}%</strong></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="result-rejected">
            <div class="ricon">❌</div>
            <h2>Loan Rejected</h2>
            <p>Risk level &nbsp;•&nbsp; <strong>{(1 - r['prob'])*100:.1f}%</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # ── Plain-English Reason Breakdown ────────────────────────────────────────
    reasons = []

    if r["credit_score"] >= 650:
        reasons.append(("✅", f"Credit score {r['credit_score']} meets the minimum requirement of 650"))
    else:
        reasons.append(("❌", f"Credit score {r['credit_score']} is below the required 650 threshold"))

    if r["dti"] <= 40:
        reasons.append(("✅", f"Debt-to-Income ({r['dti']:.1f}%) is within the safe limit of 40%"))
    else:
        reasons.append(("❌", f"Debt-to-Income ({r['dti']:.1f}%) exceeds the maximum allowed 40%"))

    if r["lti"] <= 5.0:
        reasons.append(("✅", f"Loan-to-Income ratio ({r['lti']:.1f}x) is within acceptable range"))
    else:
        reasons.append(("❌", f"Loan amount is {r['lti']:.1f}x annual income — exceeds the 5x cap"))

    if r["employment"] == "Unemployed":
        reasons.append(("❌", "Unemployed applicants carry high repayment risk"))
    else:
        reasons.append(("✅", f"Employment ({r['employment']}) supports repayment capacity"))

    rows_html = "".join(
        f'<div class="reason-row"><span>{icon}</span><span>{text}</span></div>'
        for icon, text in reasons
    )

    st.markdown(f"""
    <div class="breakdown-card">
        <h4>📋 Decision Breakdown</h4>
        {rows_html}
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# APPLICATION HISTORY (collapsible)
# ═══════════════════════════════════════════════════════════════
with st.expander("📜 Recent Application History"):
    try:
        conn, db_type = get_connection()
        query = """
            SELECT loan_id, credit_score, annual_income, loan_amount, approval_status
            FROM predictions
            ORDER BY id DESC
            LIMIT 8
        """
        df = pd.read_sql_query(query, conn.conn if db_type == "SQLite" else conn)
        conn.close()

        if not df.empty:
            df.columns = ["Application ID", "Credit Score", "Income", "Loan Amount", "Decision"]
            df["Income"]      = df["Income"].apply(lambda x: f"${x:,.0f}")
            df["Loan Amount"] = df["Loan Amount"].apply(lambda x: f"${x:,.0f}")

            def style_dec(val):
                color = "#059669" if val == "Approved" else "#DC2626"
                return f"color:{color}; font-weight:600;"

            st.dataframe(
                df.style.map(style_dec, subset=["Decision"]),
                width="stretch",
                hide_index=True,
            )
            st.caption(f"Database backend: {db_type}")
        else:
            st.info("No past applications found. Submit one above to get started.")
    except Exception as e:
        st.warning(f"Could not load history: {e}")
