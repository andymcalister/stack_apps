import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Stack — Borrow",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── THEME CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── ALL WIDGET LABELS BRIGHT WHITE ── */
label { color: #FFFFFF !important; opacity: 1 !important; }
label p { color: #FFFFFF !important; opacity: 1 !important; font-weight: 500 !important; }
div[data-testid="stWidgetLabel"] p { color: #FFFFFF !important; font-weight: 500 !important; }
div[data-testid="stWidgetLabel"] { color: #FFFFFF !important; }

/* ── SLIDER TRACK — TEAL NOT RED ── */
[data-testid="stSlider"] [role="slider"] { background-color: #00C2A8 !important; }
[data-testid="stSlider"] div[class*="TrackFill"] { background-color: #00C2A8 !important; }
input[type="range"]::-webkit-slider-thumb { background: #00C2A8 !important; }
input[type="range"]::-webkit-slider-runnable-track { background: #1E3A50 !important; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0A1628;
    color: #FFFFFF;
}
.stApp { background-color: #0A1628; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.metric-card {
    background: #0F2035;
    border: 1px solid rgba(0,194,168,0.2);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
}
.metric-card.primary { border-color: #00C2A8; border-top: 3px solid #00C2A8; }
.metric-label {
    font-size: 0.7rem; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.1em;
    font-weight: 600; margin-bottom: 0.4rem;
}
.metric-val {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem; font-weight: 800; color: #FFFFFF;
}
.metric-val.teal { color: #00C2A8; }
.metric-val.gold { color: #F5A623; }
.metric-val.red  { color: #EF4444; }
.metric-sub { font-size: 0.75rem; color: #8AACBB; margin-top: 0.3rem; }

.section-label {
    font-size: 0.7rem; color: #00C2A8;
    text-transform: uppercase; letter-spacing: 0.12em;
    font-weight: 700; margin-bottom: 0.5rem;
}

.score-badge {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 100px;
    font-size: 0.8rem; font-weight: 700;
}

.amortization-row {
    display: flex; justify-content: space-between;
    padding: 0.4rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.8rem;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem; font-weight: 800;
    line-height: 1.1; letter-spacing: -0.02em;
    color: #FFFFFF;
}
.hero-title span { color: #00C2A8; }
.hero-sub { color: #8AACBB; font-size: 1rem; margin-top: 0.5rem; font-weight: 300; }

.stSlider > div > div > div { background: #00C2A8 !important; }
.stSlider > div > div > div > div { background: #00C2A8 !important; }

/* Slider and widget labels */
div[data-testid="stWidgetLabel"] p { color: #FFFFFF !important; font-weight: 500 !important; }
div[data-testid="stSlider"] label,
div[data-testid="stSlider"] label p { color: #FFFFFF !important; font-weight: 500 !important; }
div[data-testid="stSelectSlider"] label,
div[data-testid="stSelectSlider"] label p { color: #FFFFFF !important; font-weight: 500 !important; }

div[data-testid="stMetric"] {
    background: #0F2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1rem;
}
div[data-testid="stMetricLabel"] { color: #8AACBB !important; font-size: 0.75rem !important; }
div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-family: 'Syne', sans-serif !important; }
div[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

.comparison-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.65rem 1rem;
    background: #0F2035;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    border: 1px solid rgba(255,255,255,0.05);
}
.comp-label { font-size: 0.85rem; color: #8AACBB; }
.comp-stack { font-size: 0.9rem; font-weight: 700; color: #00C2A8; }
.comp-other { font-size: 0.9rem; color: #EF4444; }

.info-box {
    background: rgba(0,194,168,0.07);
    border: 1px solid rgba(0,194,168,0.2);
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.85rem;
    color: #8AACBB;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


# ── RATE CALCULATION LOGIC ───────────────────────────────────
def credit_score_band(score):
    if score >= 750: return "Excellent", "#00C2A8", 0.0
    if score >= 700: return "Good",      "#10B981", 0.02
    if score >= 650: return "Fair",      "#F5A623", 0.045
    return "Poor", "#EF4444", 0.08

def calculate_rate(score, term_months):
    _, _, score_premium = credit_score_band(score)
    base_rate = 0.089          # 8.9% base
    term_premium = 0.005 if term_months > 36 else 0.0
    rate = base_rate + score_premium + term_premium
    # Cap at 16.9% — Stack's promise is always sub-market
    return min(rate, 0.169)

def monthly_payment(principal, annual_rate, term_months):
    r = annual_rate / 12
    if r == 0: return principal / term_months
    return principal * r * (1 + r)**term_months / ((1 + r)**term_months - 1)

def build_amortization(principal, annual_rate, term_months):
    r = annual_rate / 12
    pmt = monthly_payment(principal, annual_rate, term_months)
    balance = principal
    schedule = []
    total_interest = 0
    for m in range(1, term_months + 1):
        interest = balance * r
        principal_paid = pmt - interest
        balance = max(0, balance - principal_paid)
        total_interest += interest
        schedule.append({
            "month": m,
            "payment": pmt,
            "principal": principal_paid,
            "interest": interest,
            "balance": balance,
            "cumulative_interest": total_interest,
        })
    return schedule

def savings_vs_credit_card(principal, annual_rate, term_months):
    cc_rate = 0.25
    cc_payment = monthly_payment(principal, cc_rate, term_months)
    stack_payment = monthly_payment(principal, annual_rate, term_months)
    return (cc_payment - stack_payment) * term_months

def savings_vs_bank(principal, annual_rate, term_months):
    bank_rate = 0.18
    bank_payment = monthly_payment(principal, bank_rate, term_months)
    stack_payment = monthly_payment(principal, annual_rate, term_months)
    return (bank_payment - stack_payment) * term_months


# ── HEADER ───────────────────────────────────────────────────
col_logo, col_nav = st.columns([1, 3])
with col_logo:
    st.markdown('<div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.6rem;letter-spacing:0.12em;color:#FFFFFF;padding:0.5rem 0">STACK<span style="color:#00C2A8">.</span></div>', unsafe_allow_html=True)

st.markdown("---")

# Hero
st.markdown("""
<div class="hero-title">Get a loan that actually <span>works for you.</span></div>
<div class="hero-sub">Community-funded personal loans from $5,000 to $25,000. Rates well below credit cards. Move the sliders to see your numbers.</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── SLIDERS ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Configure Your Loan</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    loan_amount = st.slider(
        "💰 Loan Amount",
        min_value=5000, max_value=25000, value=12000, step=500,
        format="$%d"
    )
with col2:
    term_months = st.select_slider(
        "📅 Loan Term",
        options=[12, 24, 36, 48, 60],
        value=36,
        format_func=lambda x: f"{x} months ({x//12}yr)" if x >= 12 else f"{x}mo"
    )
with col3:
    credit_score = st.slider(
        "⭐ Credit Score",
        min_value=580, max_value=850, value=700, step=5
    )

# ── CALCULATIONS ─────────────────────────────────────────────
score_label, score_color, _ = credit_score_band(credit_score)
annual_rate = calculate_rate(credit_score, term_months)
monthly_pmt = monthly_payment(loan_amount, annual_rate, term_months)
total_repaid = monthly_pmt * term_months
total_interest = total_repaid - loan_amount
origination_fee = loan_amount * 0.05
effective_apr = annual_rate  # simplified
schedule = build_amortization(loan_amount, annual_rate, term_months)
cc_savings = savings_vs_credit_card(loan_amount, annual_rate, term_months)
bank_savings = savings_vs_bank(loan_amount, annual_rate, term_months)

# ── SCORE BADGE ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:1rem;margin:1rem 0 0.5rem">
    <span style="font-size:0.8rem;color:#64748B">Credit Rating:</span>
    <span style="background:{score_color}22;color:{score_color};padding:0.25rem 0.9rem;
        border-radius:100px;font-size:0.8rem;font-weight:700;border:1px solid {score_color}44">
        {score_label} · {credit_score}
    </span>
    <span style="font-size:0.8rem;color:#64748B">Your rate:</span>
    <span style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:#00C2A8">{annual_rate*100:.1f}% APR</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── KEY METRICS ───────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Monthly Payment", f"${monthly_pmt:,.2f}",
              delta=f"{annual_rate*100:.1f}% APR")
with m2:
    st.metric("Total Repaid", f"${total_repaid:,.0f}",
              delta=f"${total_interest:,.0f} total interest")
with m3:
    st.metric("vs. Credit Card", f"${cc_savings:,.0f} saved",
              delta=f"25% card vs {annual_rate*100:.1f}% Stack")
with m4:
    st.metric("Origination Fee", f"${origination_fee:,.0f}",
              delta="One-time, paid upfront")

st.markdown("<br>", unsafe_allow_html=True)

# ── CHARTS ───────────────────────────────────────────────────
chart_col, detail_col = st.columns([2, 1])

with chart_col:
    # Amortization chart — principal vs interest over time
    months = [s["month"] for s in schedule]
    principal_paid = [s["principal"] for s in schedule]
    interest_paid  = [s["interest"]  for s in schedule]
    balance        = [s["balance"]   for s in schedule]
    cum_interest   = [s["cumulative_interest"] for s in schedule]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Monthly Payment Breakdown", "Remaining Balance"),
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4]
    )

    # Stacked bar: principal + interest
    fig.add_trace(go.Bar(
        name="Principal", x=months, y=principal_paid,
        marker_color="#00C2A8", opacity=0.9,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        name="Interest", x=months, y=interest_paid,
        marker_color="#F5A623", opacity=0.9,
    ), row=1, col=1)

    # Balance line
    fig.add_trace(go.Scatter(
        name="Balance", x=months, y=balance,
        fill="tozeroy", fillcolor="rgba(0,194,168,0.07)",
        line=dict(color="#00C2A8", width=2.5),
        mode="lines",
    ), row=2, col=1)

    fig.update_layout(
        barmode="stack",
        paper_bgcolor="#0F2035",
        plot_bgcolor="#0F2035",
        font=dict(color="#8AACBB", family="DM Sans"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=0, r=0, t=40, b=0),
        height=380,
    )
    for axis in ["xaxis","yaxis","xaxis2","yaxis2"]:
        fig.update_layout(**{axis: dict(
            gridcolor="rgba(255,255,255,0.05)",
            zerolinecolor="rgba(255,255,255,0.08)",
            tickfont=dict(size=10, color="#64748B"),
        )})
    fig.update_annotations(font=dict(color="#8AACBB", size=12))

    st.plotly_chart(fig, use_container_width=True)

with detail_col:
    st.markdown('<div class="section-label">Loan Summary</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card primary">
        <div class="metric-label">Monthly Payment</div>
        <div class="metric-val teal">${monthly_pmt:,.2f}</div>
        <div class="metric-sub">For {term_months} months</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Interest Rate</div>
        <div class="metric-val">{annual_rate*100:.1f}%</div>
        <div class="metric-sub">Fixed APR · {score_label} credit</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Total Interest</div>
        <div class="metric-val gold">${total_interest:,.0f}</div>
        <div class="metric-sub">{total_interest/loan_amount*100:.1f}% of loan amount</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Origination Fee</div>
        <div class="metric-val">${origination_fee:,.0f}</div>
        <div class="metric-sub">5% · deducted at funding</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">You Receive</div>
        <div class="metric-val teal">${loan_amount - origination_fee:,.0f}</div>
        <div class="metric-sub">Net after origination fee</div>
    </div>
    """, unsafe_allow_html=True)

# ── COMPARISON ───────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">How Stack Compares</div>', unsafe_allow_html=True)

comp_col1, comp_col2 = st.columns(2)

with comp_col1:
    cc_monthly = monthly_payment(loan_amount, 0.25, term_months)
    bank_monthly = monthly_payment(loan_amount, 0.18, term_months)
    prosper_monthly = monthly_payment(loan_amount, 0.199, term_months)

    st.markdown(f"""
    <div style="margin-bottom:0.5rem;font-size:0.8rem;color:#64748B;font-weight:600">Monthly Payment Comparison</div>
    <div class="comparison-row">
        <span class="comp-label">Stack</span>
        <span class="comp-stack">${monthly_pmt:,.2f} / mo</span>
    </div>
    <div class="comparison-row">
        <span class="comp-label">Bank Loan (avg 18%)</span>
        <span class="comp-other">${bank_monthly:,.2f} / mo</span>
    </div>
    <div class="comparison-row">
        <span class="comp-label">Prosper (avg 19.9%)</span>
        <span class="comp-other">${prosper_monthly:,.2f} / mo</span>
    </div>
    <div class="comparison-row">
        <span class="comp-label">Credit Card (avg 25%)</span>
        <span class="comp-other">${cc_monthly:,.2f} / mo</span>
    </div>
    """, unsafe_allow_html=True)

with comp_col2:
    cc_total = cc_monthly * term_months
    bank_total = bank_monthly * term_months
    prosper_total = prosper_monthly * term_months
    stack_total = total_repaid

    fig2 = go.Figure(go.Bar(
        x=["Stack", "Bank Loan", "Prosper", "Credit Card"],
        y=[stack_total, bank_total, prosper_total, cc_total],
        marker_color=["#00C2A8", "#EF4444", "#EF4444", "#EF4444"],
        text=[f"${v:,.0f}" for v in [stack_total, bank_total, prosper_total, cc_total]],
        textposition="outside",
        textfont=dict(size=11, color="#FFFFFF"),
    ))
    fig2.update_layout(
        title=dict(text="Total Cost of Loan", font=dict(color="#8AACBB", size=12)),
        paper_bgcolor="#0F2035", plot_bgcolor="#0F2035",
        font=dict(color="#8AACBB", family="DM Sans"),
        margin=dict(l=0, r=0, t=40, b=0), height=220,
        showlegend=False,
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickformat="$,.0f",
                   tickfont=dict(size=10, color="#64748B")),
        xaxis=dict(tickfont=dict(size=11, color="#AABCC8")),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── RATE SENSITIVITY ─────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">Rate Sensitivity — How Your Score Affects Your Rate</div>', unsafe_allow_html=True)

score_range  = list(range(580, 855, 5))
rate_range   = [calculate_rate(s, term_months) * 100 for s in score_range]
pmt_range    = [monthly_payment(loan_amount, calculate_rate(s, term_months), term_months) for s in score_range]

fig3 = make_subplots(specs=[[{"secondary_y": True}]])
fig3.add_trace(go.Scatter(
    x=score_range, y=rate_range, name="APR %",
    line=dict(color="#F5A623", width=2.5), mode="lines",
), secondary_y=False)
fig3.add_trace(go.Scatter(
    x=score_range, y=pmt_range, name="Monthly Payment",
    line=dict(color="#00C2A8", width=2.5), mode="lines",
    fill="tozeroy", fillcolor="rgba(0,194,168,0.05)",
), secondary_y=True)

# Mark current score
fig3.add_vline(x=credit_score, line_dash="dash",
               line_color="rgba(255,255,255,0.3)", line_width=1.5)
fig3.add_annotation(x=credit_score, y=annual_rate*100,
                    text=f"  You: {annual_rate*100:.1f}%",
                    showarrow=False, font=dict(color="#FFFFFF", size=11),
                    xanchor="left", secondary_y=False, yref="y")

fig3.update_layout(
    paper_bgcolor="#0F2035", plot_bgcolor="#0F2035",
    font=dict(color="#8AACBB", family="DM Sans"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=0, r=0, t=30, b=0), height=220,
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Credit Score",
               tickfont=dict(size=10, color="#64748B")),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", ticksuffix="%",
               tickfont=dict(size=10, color="#F5A623")),
    yaxis2=dict(tickprefix="$", tickfont=dict(size=10, color="#00C2A8"),
                gridcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig3, use_container_width=True)

# ── INFO BOX ─────────────────────────────────────────────────
st.markdown(f"""
<div class="info-box">
    💡 <strong style="color:#FFFFFF">How Stack sets your rate:</strong>
    Your base rate starts at 8.9%. We add a small premium based on your credit score 
    ({score_label}: +{_*100:.1f}% for credit, using band logic), and a term premium for longer loans.
    Your rate is always capped at 16.9% — our promise to keep you below market.
    The 5% origination fee (${origination_fee:,.0f}) is deducted from the loan amount when funded — 
    you receive <strong style="color:#00C2A8">${loan_amount - origination_fee:,.0f}</strong>.
</div>
""".replace("{_*100:.1f}", f"{credit_score_band(credit_score)[2]*100:.1f}"), unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#334155;font-size:0.75rem;border-top:1px solid rgba(255,255,255,0.05);padding-top:1rem">
    Stack Financial Technologies · Rates are illustrative · Subject to credit approval · andym@stacklend.co
</div>
""", unsafe_allow_html=True)
