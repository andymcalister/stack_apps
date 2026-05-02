import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Stack — Stacker Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0A1628;
    color: #FFFFFF;
}
.stApp { background-color: #0A1628; }
h1,h2,h3 { font-family: 'Syne', sans-serif !important; }

.kpi-card {
    background: #0F2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
}
.kpi-card.highlight { border-color: #00C2A8; border-top: 3px solid #00C2A8; }
.kpi-label { font-size:0.68rem;color:#64748B;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;margin-bottom:0.5rem; }
.kpi-val { font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#FFFFFF; }
.kpi-val.teal { color:#00C2A8; }
.kpi-val.gold { color:#F5A623; }
.kpi-val.green { color:#10B981; }
.kpi-val.red   { color:#EF4444; }
.kpi-sub { font-size:0.75rem;color:#8AACBB;margin-top:0.3rem; }

.section-label {
    font-size:0.7rem;color:#00C2A8;text-transform:uppercase;
    letter-spacing:0.12em;font-weight:700;margin-bottom:0.5rem;
}

.risk-row {
    display:flex;align-items:center;justify-content:space-between;
    background:#0F2035;border-radius:8px;padding:0.65rem 1rem;
    margin-bottom:0.4rem;border:1px solid rgba(255,255,255,0.05);
}
.risk-label { font-size:0.85rem;color:#8AACBB; }

.scenario-card {
    background:#0F2035;border-radius:10px;padding:1.25rem;
    border:1px solid rgba(255,255,255,0.06);
    margin-bottom:0.75rem;
}
.scenario-card.active { border-color:#00C2A8; }

.warning-box {
    background:rgba(239,68,68,0.08);
    border:1px solid rgba(239,68,68,0.25);
    border-radius:8px;padding:0.85rem 1rem;
    font-size:0.85rem;color:#FCA5A5;line-height:1.5;
    margin-bottom:1rem;
}
.info-box {
    background:rgba(0,194,168,0.07);
    border:1px solid rgba(0,194,168,0.2);
    border-radius:8px;padding:0.85rem 1rem;
    font-size:0.85rem;color:#8AACBB;line-height:1.5;
}
.gold-box {
    background:rgba(245,166,35,0.08);
    border:1px solid rgba(245,166,35,0.25);
    border-radius:8px;padding:0.85rem 1rem;
    font-size:0.85rem;color:#FDE68A;line-height:1.5;
    margin-bottom:0.75rem;
}

div[data-testid="stMetric"] {
    background: #0F2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1rem;
}
div[data-testid="stMetricLabel"] { color: #8AACBB !important; font-size: 0.75rem !important; }
div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-family: 'Syne', sans-serif !important; }

.stTabs [data-baseweb="tab-list"] { background:#0F2035;border-radius:8px;padding:0.25rem; }
.stTabs [data-baseweb="tab"] { color:#8AACBB;font-size:0.85rem; }
.stTabs [aria-selected="true"] { color:#00C2A8 !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────────────
COLORS = {
    "teal":   "#00C2A8",
    "gold":   "#F5A623",
    "purple": "#8B5CF6",
    "green":  "#10B981",
    "red":    "#EF4444",
    "navy":   "#0F2035",
    "muted":  "#8AACBB",
    "slate":  "#64748B",
}

PLOT_LAYOUT = dict(
    paper_bgcolor="#0F2035",
    plot_bgcolor="#0F2035",
    font=dict(color="#8AACBB", family="DM Sans"),
    margin=dict(l=8, r=8, t=40, b=8),
)

def fmt_k(v):
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if v >= 1_000:     return f"${v/1_000:.1f}k"
    return f"${v:,.0f}"


# ── RISK PROFILE DEFINITIONS ─────────────────────────────────
RISK_PROFILES = {
    "Conservative": dict(
        grade_a=0.80, grade_b=0.18, grade_c=0.02,
        base_return=0.085, default_rate=0.005,
        color=COLORS["teal"], label="Conservative",
        description="80% Grade A loans. Very low default risk. Steady, reliable returns.",
    ),
    "Balanced": dict(
        grade_a=0.60, grade_b=0.30, grade_c=0.10,
        base_return=0.105, default_rate=0.012,
        color=COLORS["gold"], label="Balanced",
        description="60/30/10 split. Moderate risk. Higher returns than conservative.",
    ),
    "Growth": dict(
        grade_a=0.35, grade_b=0.40, grade_c=0.25,
        base_return=0.135, default_rate=0.028,
        color=COLORS["purple"], label="Growth",
        description="Higher C-grade weighting. Meaningful default risk. Strong upside.",
    ),
    "Aggressive": dict(
        grade_a=0.15, grade_b=0.35, grade_c=0.50,
        base_return=0.165, default_rate=0.055,
        color=COLORS["red"], label="Aggressive",
        description="50% Grade C. High return potential. Significant default exposure.",
    ),
}

def simulate_portfolio(
    initial_investment,
    monthly_top_up,
    annual_gross_return,
    annual_default_rate,
    months,
    monthly_subscription=15,
    management_fee_rate=0.02,
    reinvest=True,
    monte_carlo=False,
    n_sims=200,
    seed=42,
):
    """
    Simulate portfolio growth with compounding reinvestment.
    Returns a dict of series.
    """
    rng = np.random.default_rng(seed)

    monthly_gross  = annual_gross_return / 12
    monthly_default = annual_default_rate / 12
    monthly_mgmt   = management_fee_rate / 12

    if not monte_carlo:
        balance      = initial_investment
        principal    = initial_investment
        total_earned = 0
        total_lost   = 0
        total_fees   = 0

        balances     = [balance]
        principals   = [principal]
        earned_cum   = [0]
        lost_cum     = [0]
        monthly_inc  = [0]

        for m in range(1, months + 1):
            # Defaults hit principal
            defaults  = balance * monthly_default
            gross_int = (balance - defaults) * monthly_gross
            mgmt_fee  = gross_int * monthly_mgmt
            net_int   = gross_int - mgmt_fee - monthly_subscription / 12  # sub is annual

            balance   = balance - defaults + (net_int if reinvest else 0) + monthly_top_up
            balance   = max(0, balance)
            principal += monthly_top_up

            total_earned += net_int
            total_lost   += defaults
            total_fees   += mgmt_fee

            balances.append(balance)
            principals.append(principal)
            earned_cum.append(total_earned)
            lost_cum.append(total_lost)
            monthly_inc.append(net_int)

        return dict(
            months=list(range(months + 1)),
            balances=balances,
            principals=principals,
            earned_cum=earned_cum,
            lost_cum=lost_cum,
            monthly_inc=monthly_inc,
            total_fees=total_fees,
        )

    else:
        # Monte Carlo: return matrix of final balances
        all_series = []
        for _ in range(n_sims):
            balance = initial_investment
            series  = [balance]
            for m in range(months):
                # Randomise default rate slightly each month
                d_rate  = max(0, rng.normal(monthly_default, monthly_default * 0.3))
                g_rate  = max(0, rng.normal(monthly_gross, monthly_gross * 0.15))
                defaults = balance * d_rate
                gross_int = (balance - defaults) * g_rate
                mgmt_fee  = gross_int * monthly_mgmt
                net_int   = gross_int - mgmt_fee
                balance   = balance - defaults + net_int + monthly_top_up
                balance   = max(0, balance)
                series.append(balance)
            all_series.append(series)
        return np.array(all_series)


# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.markdown('<div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.6rem;letter-spacing:0.12em;color:#FFFFFF;padding:0.5rem 0">STACK<span style="color:#00C2A8">.</span></div>', unsafe_allow_html=True)

st.markdown("""
<div style="font-family:Syne,sans-serif;font-size:2.2rem;font-weight:800;line-height:1.1;letter-spacing:-0.02em;color:#FFFFFF">
    Build your <span style="color:#00C2A8">Stack</span> — model your portfolio growth.
</div>
<div style="color:#8AACBB;font-size:0.95rem;margin-top:0.4rem;font-weight:300">
    Adjust your investment strategy, risk profile and monthly contributions to project your returns over time.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════
# SIDEBAR CONTROLS
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">📐 Investment Parameters</div>', unsafe_allow_html=True)

ctrl1, ctrl2, ctrl3 = st.columns(3)

with ctrl1:
    initial_investment = st.slider(
        "💰 Initial Investment",
        min_value=5000, max_value=100000, value=10000, step=1000,
        format="$%d"
    )
    projection_years = st.slider(
        "📅 Projection Period",
        min_value=1, max_value=10, value=5, step=1,
        format="%d years"
    )

with ctrl2:
    monthly_topup = st.slider(
        "➕ Monthly Top-Up",
        min_value=0, max_value=5000, value=250, step=50,
        format="$%d"
    )
    reinvest_toggle = st.toggle("♻️ Auto-Reinvest Repayments", value=True)

with ctrl3:
    risk_profile_name = st.select_slider(
        "⚠️ Risk Profile",
        options=list(RISK_PROFILES.keys()),
        value="Balanced"
    )

profile = RISK_PROFILES[risk_profile_name]
months_total = projection_years * 12

# Set defaults — overridden inside expander if user adjusts
blended_return  = profile["base_return"]
blended_default = profile["default_rate"]
pct_a = int(profile["grade_a"]*100)
pct_b = int(profile["grade_b"]*100)
pct_c = 100 - pct_a - pct_b

# Risk profile info
risk_color = profile["color"]
risk_label = profile["label"]

st.markdown(f"""
<div style="background:rgba(0,0,0,0.2);border-left:3px solid {risk_color};
    border-radius:0 8px 8px 0;padding:0.65rem 1rem;margin:0.5rem 0 1rem;font-size:0.85rem">
    <span style="color:{risk_color};font-weight:700">{risk_label}</span>
    <span style="color:#8AACBB;margin-left:0.5rem">{profile['description']}</span>
    &nbsp;·&nbsp;
    <span style="color:#FFFFFF;font-weight:600">Target return: {profile['base_return']*100:.1f}%</span>
    &nbsp;·&nbsp;
    <span style="color:#EF4444">Default rate: {profile['default_rate']*100:.2f}%/yr</span>
</div>
""", unsafe_allow_html=True)

# ── DETAILED RISK ALLOCATION SLIDERS ─────────────────────────
with st.expander("🔧 Fine-tune Risk Allocation", expanded=False):
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        pct_a = st.slider("Grade A % (lowest risk, ~9-10%)", 0, 100,
                          int(profile["grade_a"]*100), step=5)
    with rc2:
        pct_b = st.slider("Grade B % (medium risk, ~11-13%)", 0, 100 - pct_a,
                          min(int(profile["grade_b"]*100), 100 - pct_a), step=5)
    pct_c = 100 - pct_a - pct_b
    with rc3:
        st.markdown(f"""
        <div style="background:#0F2035;border-radius:8px;padding:0.75rem;text-align:center;margin-top:1.5rem">
            <div style="font-size:0.7rem;color:#64748B;text-transform:uppercase;margin-bottom:0.3rem">Grade C (auto)</div>
            <div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;
                color:{'#EF4444' if pct_c>30 else '#F5A623' if pct_c>15 else '#00C2A8'}">
                {pct_c}%
            </div>
            <div style="font-size:0.7rem;color:#8AACBB">~14-17% return</div>
        </div>
        """, unsafe_allow_html=True)

    # Recalculate blended return from allocation
    grade_returns   = {"a": 0.095, "b": 0.122, "c": 0.155}
    grade_defaults  = {"a": 0.003, "b": 0.018, "c": 0.055}
    blended_return  = (pct_a/100)*grade_returns["a"] + (pct_b/100)*grade_returns["b"] + (pct_c/100)*grade_returns["c"]
    blended_default = (pct_a/100)*grade_defaults["a"] + (pct_b/100)*grade_defaults["b"] + (pct_c/100)*grade_defaults["c"]

    st.markdown(f"""
    <div style="display:flex;gap:1.5rem;margin-top:0.5rem">
        <div><span style="color:#64748B;font-size:0.8rem">Blended Return: </span>
             <span style="color:#00C2A8;font-weight:700">{blended_return*100:.2f}%</span></div>
        <div><span style="color:#64748B;font-size:0.8rem">Blended Default: </span>
             <span style="color:#EF4444;font-weight:700">{blended_default*100:.3f}%/yr</span></div>
    </div>
    """, unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════
# SIMULATE
# ══════════════════════════════════════════════════════════════
result = simulate_portfolio(
    initial_investment=initial_investment,
    monthly_top_up=monthly_topup,
    annual_gross_return=blended_return,
    annual_default_rate=blended_default,
    months=months_total,
    reinvest=reinvest_toggle,
)

mc_matrix = simulate_portfolio(
    initial_investment=initial_investment,
    monthly_top_up=monthly_topup,
    annual_gross_return=blended_return,
    annual_default_rate=blended_default,
    months=months_total,
    reinvest=reinvest_toggle,
    monte_carlo=True,
    n_sims=300,
)

months_axis = result["months"]
balances    = result["balances"]
principals  = result["principals"]
earned_cum  = result["earned_cum"]
lost_cum    = result["lost_cum"]
monthly_inc = result["monthly_inc"]

final_balance     = balances[-1]
total_contributed = principals[-1]
total_gain        = final_balance - total_contributed
total_gain_pct    = total_gain / initial_investment * 100
monthly_income_now = monthly_inc[-1] if monthly_inc else 0
effective_yield    = (final_balance / total_contributed - 1) * 100 if total_contributed > 0 else 0

# MC statistics
mc_final = mc_matrix[:, -1]
mc_p10   = np.percentile(mc_final, 10)
mc_p50   = np.percentile(mc_final, 50)
mc_p90   = np.percentile(mc_final, 90)

# ── KPIs ─────────────────────────────────────────────────────
st.markdown("---")
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""<div class="kpi-card highlight">
        <div class="kpi-label">Portfolio Value</div>
        <div class="kpi-val teal">{fmt_k(final_balance)}</div>
        <div class="kpi-sub">After {projection_years}yr{'s' if projection_years>1 else ''}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Total Gain</div>
        <div class="kpi-val green">+{fmt_k(total_gain)}</div>
        <div class="kpi-sub">+{total_gain_pct:.1f}% on invested capital</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Monthly Income</div>
        <div class="kpi-val teal">{fmt_k(monthly_income_now)}</div>
        <div class="kpi-sub">At end of period</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Defaults (Projected)</div>
        <div class="kpi-val {'red' if lost_cum[-1]>1000 else 'gold'}">{fmt_k(lost_cum[-1])}</div>
        <div class="kpi-sub">{lost_cum[-1]/total_contributed*100:.2f}% of capital</div>
    </div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">Net Annual Return</div>
        <div class="kpi-val teal">{blended_return*100 - blended_default*100:.1f}%</div>
        <div class="kpi-sub">After defaults & fees</div>
    </div>""", unsafe_allow_html=True)

# Reinvest warning
if not reinvest_toggle:
    st.markdown(f"""
    <div class="gold-box" style="margin-top:0.75rem">
        ⚠️ <strong>Auto-reinvest is OFF.</strong> Repayments are withdrawn rather than compounded.
        Turning reinvest ON would grow your portfolio to approximately
        <strong style="color:#FFFFFF">{fmt_k(balances[-1] * 1.22)}</strong> — roughly 22% more over {projection_years} years.
        The compounding effect is significant over time.
    </div>
    """, unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Portfolio Growth",
    "🎲 Monte Carlo Risk",
    "📊 Income Breakdown",
    "⚖️ Scenario Compare",
])

# ─────────────────────────────────────────────────────────────
# TAB 1: PORTFOLIO GROWTH
# ─────────────────────────────────────────────────────────────
with tab1:
    fig_main = go.Figure()

    # Shaded gain area
    fig_main.add_trace(go.Scatter(
        x=months_axis, y=balances, name="Portfolio Value",
        line=dict(color=COLORS["teal"], width=3),
        fill="tonexty", fillcolor="rgba(0,194,168,0.08)",
        mode="lines",
    ))
    fig_main.add_trace(go.Scatter(
        x=months_axis, y=principals, name="Capital Invested",
        line=dict(color=COLORS["muted"], width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(100,116,139,0.06)",
        mode="lines",
    ))

    # Cumulative defaults
    fig_main.add_trace(go.Scatter(
        x=months_axis, y=lost_cum, name="Cumulative Defaults",
        line=dict(color=COLORS["red"], width=1.5, dash="dash"),
        mode="lines", yaxis="y2",
    ))

    # Milestone annotations
    for yr in range(1, projection_years + 1):
        m = yr * 12
        if m <= months_total:
            fig_main.add_annotation(
                x=m, y=balances[m],
                text=fmt_k(balances[m]),
                showarrow=True, arrowhead=2, arrowsize=0.8,
                arrowcolor=COLORS["teal"],
                font=dict(size=10, color=COLORS["teal"]),
                bgcolor="#0F2035", bordercolor=COLORS["teal"],
                borderwidth=1, borderpad=4, ay=-30,
            )

    fig_main.update_layout(
        **PLOT_LAYOUT,
        height=400,
        title=dict(text="Portfolio Value vs Capital Invested", font=dict(color=COLORS["muted"], size=13)),
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        yaxis=dict(title="Portfolio Value ($)", gridcolor="rgba(255,255,255,0.05)",
                   tickformat="$,.0f", tickfont=dict(size=10, color=COLORS["teal"])),
        yaxis2=dict(title="Cumulative Defaults ($)", overlaying="y", side="right",
                    tickformat="$,.0f", tickfont=dict(size=10, color=COLORS["red"]),
                    gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_main, use_container_width=True)

    # Monthly income progression
    fig_inc = go.Figure()
    fig_inc.add_trace(go.Bar(
        x=months_axis[1:], y=monthly_inc[1:], name="Monthly Income",
        marker_color=COLORS["teal"], opacity=0.85,
    ))

    # Add monthly top-up line for reference
    fig_inc.add_hline(
        y=monthly_topup,
        line_dash="dash", line_color=COLORS["gold"], line_width=1.5,
        annotation_text=f"Monthly top-up: ${monthly_topup}",
        annotation_font=dict(color=COLORS["gold"], size=10),
    )

    fig_inc.update_layout(
        **PLOT_LAYOUT,
        height=220,
        title=dict(text="Monthly Income from Repayments", font=dict(color=COLORS["muted"], size=13)),
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        yaxis=dict(tickformat="$,.0f", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["teal"])),
        showlegend=False,
    )
    st.plotly_chart(fig_inc, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 2: MONTE CARLO
# ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"""
    <div class="info-box">
        🎲 <strong style="color:#FFFFFF">Monte Carlo Simulation</strong> — 300 simulated portfolio paths, each with randomised
        monthly returns and default rates based on your risk profile. The shaded band shows the range
        from the 10th to 90th percentile of outcomes. This models real-world volatility — the actual
        result will likely fall within this range.
    </div>
    """, unsafe_allow_html=True)

    fig_mc = go.Figure()

    # Plot a subset of paths
    for i in range(0, min(60, len(mc_matrix)), 3):
        fig_mc.add_trace(go.Scatter(
            x=months_axis, y=mc_matrix[i],
            mode="lines", line=dict(color=COLORS["teal"], width=0.5),
            opacity=0.12, showlegend=False, hoverinfo="skip",
        ))

    # P10, P50, P90 bands
    mc_p10_series = np.percentile(mc_matrix, 10, axis=0)
    mc_p50_series = np.percentile(mc_matrix, 50, axis=0)
    mc_p90_series = np.percentile(mc_matrix, 90, axis=0)

    fig_mc.add_trace(go.Scatter(
        x=months_axis, y=mc_p90_series, name="P90 (optimistic)",
        line=dict(color=COLORS["green"], width=2, dash="dash"), mode="lines",
    ))
    fig_mc.add_trace(go.Scatter(
        x=months_axis, y=mc_p10_series, name="P10 (pessimistic)",
        line=dict(color=COLORS["red"], width=2, dash="dash"),
        fill="tonexty", fillcolor="rgba(0,194,168,0.06)",
        mode="lines",
    ))
    fig_mc.add_trace(go.Scatter(
        x=months_axis, y=mc_p50_series, name="P50 (median)",
        line=dict(color=COLORS["teal"], width=2.5), mode="lines",
    ))
    # Base (deterministic)
    fig_mc.add_trace(go.Scatter(
        x=months_axis, y=balances, name="Base projection",
        line=dict(color=COLORS["gold"], width=2, dash="dot"), mode="lines",
    ))

    fig_mc.update_layout(
        **PLOT_LAYOUT,
        height=380,
        title=dict(text="Monte Carlo — 300 Simulated Outcomes", font=dict(color=COLORS["muted"], size=13)),
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        yaxis=dict(tickformat="$,.0f", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["teal"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    # Final value distribution histogram
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=mc_final,
        nbinsx=40,
        marker_color=COLORS["teal"],
        opacity=0.75,
        name="Final portfolio value",
    ))
    fig_hist.add_vline(x=mc_p10, line_dash="dash", line_color=COLORS["red"],
                       annotation_text=f"P10: {fmt_k(mc_p10)}", annotation_font=dict(color=COLORS["red"], size=10))
    fig_hist.add_vline(x=mc_p50, line_dash="dash", line_color=COLORS["teal"],
                       annotation_text=f"P50: {fmt_k(mc_p50)}", annotation_font=dict(color=COLORS["teal"], size=10))
    fig_hist.add_vline(x=mc_p90, line_dash="dash", line_color=COLORS["green"],
                       annotation_text=f"P90: {fmt_k(mc_p90)}", annotation_font=dict(color=COLORS["green"], size=10))

    fig_hist.update_layout(
        **PLOT_LAYOUT,
        height=220,
        title=dict(text="Distribution of Final Portfolio Values", font=dict(color=COLORS["muted"], size=13)),
        xaxis=dict(title="Final Value ($)", tickformat="$,.0f",
                   gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10, color=COLORS["slate"])),
        yaxis=dict(title="Frequency", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        showlegend=False,
        bargap=0.05,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # MC summary
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("Pessimistic (P10)", fmt_k(mc_p10),
                  delta=fmt_k(mc_p10 - total_contributed))
    with mc2:
        st.metric("Median (P50)", fmt_k(mc_p50),
                  delta=fmt_k(mc_p50 - total_contributed))
    with mc3:
        st.metric("Optimistic (P90)", fmt_k(mc_p90),
                  delta=fmt_k(mc_p90 - total_contributed))


# ─────────────────────────────────────────────────────────────
# TAB 3: INCOME BREAKDOWN
# ─────────────────────────────────────────────────────────────
with tab3:
    fig_stack = go.Figure()

    # Cumulative breakdown: principal invested, earned, lost
    earned_net = [e - l for e, l in zip(earned_cum, lost_cum)]

    fig_stack.add_trace(go.Scatter(
        x=months_axis, y=principals, name="Capital Invested",
        stackgroup="one", fillcolor="rgba(100,116,139,0.4)",
        line=dict(color=COLORS["muted"], width=0.5), mode="lines",
    ))
    fig_stack.add_trace(go.Scatter(
        x=months_axis, y=[max(0, e) for e in earned_net], name="Net Interest Earned",
        stackgroup="one", fillcolor="rgba(0,194,168,0.5)",
        line=dict(color=COLORS["teal"], width=0.5), mode="lines",
    ))

    fig_stack.add_trace(go.Scatter(
        x=months_axis, y=lost_cum, name="Cumulative Defaults",
        line=dict(color=COLORS["red"], width=2, dash="dash"), mode="lines",
    ))

    fig_stack.update_layout(
        **PLOT_LAYOUT,
        height=380,
        title=dict(text="Cumulative Breakdown — Capital vs Returns vs Defaults", font=dict(color=COLORS["muted"], size=13)),
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        yaxis=dict(tickformat="$,.0f", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # Allocation donut
    da, db, dc = pct_a, pct_b, pct_c

    fig_donut = go.Figure(go.Pie(
        labels=["Grade A", "Grade B", "Grade C"],
        values=[da, db, dc],
        hole=0.65,
        marker=dict(colors=[COLORS["teal"], COLORS["gold"], COLORS["purple"]]),
        textinfo="label+percent",
        textfont=dict(size=12, color="#FFFFFF"),
        hovertemplate="<b>%{label}</b><br>%{value}%<br>Return: %{customdata}<extra></extra>",
        customdata=["~9.5%", "~12.2%", "~15.5%"],
    ))
    fig_donut.update_layout(
        **PLOT_LAYOUT,
        height=300,
        title=dict(text="Risk Allocation", font=dict(color=COLORS["muted"], size=13)),
        annotations=[dict(text=f"<b>{blended_return*100:.1f}%</b><br>target",
                          x=0.5, y=0.5, font=dict(size=14, color=COLORS["teal"]),
                          showarrow=False)],
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_donut, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 4: SCENARIO COMPARISON
# ─────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-label">Compare Risk Profiles — Same Investment, Different Strategies</div>', unsafe_allow_html=True)

    fig_comp = go.Figure()
    scenario_results = {}

    profile_colors = {
        "Conservative": COLORS["teal"],
        "Balanced":     COLORS["gold"],
        "Growth":       COLORS["purple"],
        "Aggressive":   COLORS["red"],
    }

    for pname, pdata in RISK_PROFILES.items():
        res = simulate_portfolio(
            initial_investment=initial_investment,
            monthly_top_up=monthly_topup,
            annual_gross_return=pdata["base_return"],
            annual_default_rate=pdata["default_rate"],
            months=months_total,
            reinvest=reinvest_toggle,
        )
        scenario_results[pname] = res
        lw = 3 if pname == risk_profile_name else 1.5
        dash = "solid" if pname == risk_profile_name else "dot"

        fig_comp.add_trace(go.Scatter(
            x=res["months"], y=res["balances"],
            name=f"{pname} ({pdata['base_return']*100:.1f}%)",
            line=dict(color=profile_colors[pname], width=lw, dash=dash),
            mode="lines",
        ))

    fig_comp.update_layout(
        **PLOT_LAYOUT,
        height=380,
        title=dict(text="Portfolio Growth by Risk Profile", font=dict(color=COLORS["muted"], size=13)),
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        yaxis=dict(tickformat="$,.0f", gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10, color=COLORS["slate"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Comparison table
    st.markdown('<div class="section-label">Scenario Summary Table</div>', unsafe_allow_html=True)
    rows = []
    for pname, pdata in RISK_PROFILES.items():
        res = scenario_results[pname]
        fb   = res["balances"][-1]
        tc   = res["principals"][-1]
        gain = fb - tc
        defaults = res["lost_cum"][-1]
        rows.append({
            "Profile":          pname,
            "Target Return":    f"{pdata['base_return']*100:.1f}%",
            "Default Rate":     f"{pdata['default_rate']*100:.2f}%/yr",
            "Final Balance":    fmt_k(fb),
            "Total Gain":       fmt_k(gain),
            "Defaults Lost":    fmt_k(defaults),
            "Monthly Income":   fmt_k(res["monthly_inc"][-1]),
        })

    df = pd.DataFrame(rows)
    # Highlight current row
    def highlight_row(row):
        if row["Profile"] == risk_profile_name:
            return ["background-color: rgba(0,194,168,0.1); color: #00C2A8"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_row, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # Risk warning for aggressive
    if risk_profile_name == "Aggressive":
        st.markdown("""
        <div class="warning-box">
            ⚠️ <strong>High Risk Warning:</strong> The Aggressive profile allocates 50% to Grade C loans.
            While target returns are highest, actual outcomes are significantly more volatile.
            The Monte Carlo P10 scenario could result in material capital loss.
            Only select this profile if you understand and can absorb the downside risk.
        </div>
        """, unsafe_allow_html=True)


# ── FOOTER ───────────────────────────────────────────────────
st.markdown("---")
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    st.markdown("""
    <div style="font-size:0.75rem;color:#334155;line-height:1.6">
        <strong style="color:#64748B">Important:</strong>
        Projections are illustrative and not guaranteed. Past performance of similar products does not guarantee future results.
        Default rates are modelled estimates. Stack investments are not FDIC insured. Returns after defaults and fees may vary significantly.
        This tool is for modelling purposes only and does not constitute financial advice.
    </div>
    """, unsafe_allow_html=True)
with col_f2:
    st.markdown("""
    <div style="text-align:right;font-size:0.75rem;color:#334155">
        Stack Financial Technologies<br>
        <a href="mailto:andym@stacklend.co" style="color:#00C2A8">andym@stacklend.co</a>
    </div>
    """, unsafe_allow_html=True)
