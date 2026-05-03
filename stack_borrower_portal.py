"""
Stack Borrower Portal
Shows loan application status, funding progress, repayment schedule.
Embedded inside stack_home.py via exec() when user_type == borrower.
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date
import pandas as pd

supabase = st.session_state.get("_supabase")
user     = st.session_state.get("user", {})

C = dict(teal="#00C2A8", gold="#F5A623", red="#EF4444",
         green="#10B981", navy2="#0F2035", muted="#94A3B8")
PLOT = dict(paper_bgcolor="#0F2035", plot_bgcolor="#0F2035",
            font=dict(color=C["muted"], family="DM Sans"),
            margin=dict(l=8,r=8,t=36,b=8))

def fmt(v, prefix="$"):
    if v is None: return "—"
    return f"{prefix}{v:,.2f}"

# ── HEADER ───────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.5rem">
    <div style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;color:#FFFFFF">
        Welcome back, {user.get('first_name','')}.
    </div>
    <div style="color:#64748B;font-size:0.875rem;margin-top:0.25rem">
        Your Stack borrower account · {user.get('email','')}
    </div>
</div>
""", unsafe_allow_html=True)

# ── LOAD LOANS ───────────────────────────────────────────────
loans = []
if supabase and user.get("id"):
    try:
        r = supabase.table("loan_applications").select("*")\
            .eq("user_id", user["id"]).order("created_at", desc=True).execute()
        loans = r.data or []
    except: pass

if not loans:
    # No loan yet — show application CTA
    st.markdown("""
    <div style="background:rgba(0,194,168,0.04);border:1px solid rgba(0,194,168,0.2);
        border-radius:16px;padding:3rem;text-align:center;margin:2rem 0">
        <div style="font-size:3rem;margin-bottom:1rem">💳</div>
        <div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;
            margin-bottom:0.75rem;color:#FFFFFF">No Active Loans</div>
        <div style="color:#94A3B8;font-size:0.9rem;max-width:400px;margin:0 auto 1.5rem;line-height:1.7">
            You haven't applied for a Stack loan yet. Use our calculator to see your
            personalised rate, then apply in minutes.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("💳 Get My Rate →", key="borrower_apply_cta", use_container_width=False):
        st.session_state.page = "borrower"
        st.rerun()
else:
    # Show most recent loan
    loan = loans[0]
    status = loan.get("status", "pending")

    # Status pipeline
    stages = ["pending","approved","funded","repaying","closed"]
    stage_idx = stages.index(status) if status in stages else 0

    status_colors = {
        "pending":  C["gold"],
        "approved": C["teal"],
        "funded":   C["teal"],
        "repaying": C["green"],
        "closed":   C["muted"],
        "rejected": C["red"],
    }

    st.markdown(f"""
    <div style="background:rgba(15,32,53,0.8);border:1px solid rgba(0,194,168,0.2);
        border-radius:16px;padding:1.75rem;margin-bottom:1.5rem">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.25rem">
            <div>
                <div style="font-size:0.7rem;color:#475569;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:700;margin-bottom:0.3rem">Loan Amount</div>
                <div style="font-family:Syne,sans-serif;font-size:2.5rem;font-weight:800;
                    color:#FFFFFF">${float(loan.get('amount',0)):,.0f}</div>
                <div style="font-size:0.85rem;color:#64748B;margin-top:0.25rem">
                    {loan.get('term_months','—')} months · {float(loan.get('annual_rate',0))*100:.1f}% APR
                </div>
            </div>
            <div style="text-align:right">
                <span style="background:{status_colors.get(status,'#64748B')}22;
                    color:{status_colors.get(status,'#64748B')};
                    border:1px solid {status_colors.get(status,'#64748B')}44;
                    padding:0.4rem 1rem;border-radius:100px;
                    font-size:0.8rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.06em">{status}</span>
                <div style="font-size:0.75rem;color:#475569;margin-top:0.5rem">
                    Applied {loan.get('created_at','')[:10]}
                </div>
            </div>
        </div>

        <!-- Progress pipeline -->
        <div style="display:flex;align-items:center;gap:0;margin-top:0.5rem">
    """, unsafe_allow_html=True)

    # Pipeline stages
    stage_labels = ["Applied", "Approved", "Funded", "Repaying", "Paid Off"]
    cols = st.columns(len(stage_labels))
    for i, (col, label) in enumerate(zip(cols, stage_labels)):
        active  = i <= stage_idx
        current = i == stage_idx
        with col:
            color = C["teal"] if active else "#1E3A50"
            text  = "#FFFFFF" if current else (C["teal"] if active else "#334155")
            st.markdown(f"""
            <div style="text-align:center">
                <div style="width:32px;height:32px;border-radius:50%;
                    background:{color};border:2px solid {C['teal'] if active else '#1E3A50'};
                    display:flex;align-items:center;justify-content:center;
                    margin:0 auto 0.4rem;font-size:0.8rem;font-weight:700;color:#060E1A">
                    {'✓' if active and not current else str(i+1)}
                </div>
                <div style="font-size:0.72rem;color:{text};font-weight:{'700' if current else '400'}">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Funding progress bar
    if status in ["approved","funded","repaying"]:
        total_funded  = float(loan.get("total_funded", 0))
        loan_amount   = float(loan.get("amount", 1))
        funded_pct    = min(total_funded / loan_amount * 100, 100)
        num_stackers  = int(loan.get("num_stackers", 0))

        st.markdown(f"""
        <div style="background:rgba(15,32,53,0.7);border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;padding:1.25rem;margin-bottom:1rem">
            <div style="display:flex;justify-content:space-between;margin-bottom:0.75rem">
                <div style="font-size:0.85rem;font-weight:600;color:#E2EDF4">
                    Funding Progress
                </div>
                <div style="font-size:0.85rem;color:#00C2A8;font-weight:700">
                    {funded_pct:.0f}% funded · {num_stackers} Stackers
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.06);border-radius:100px;height:10px;overflow:hidden">
                <div style="width:{funded_pct:.1f}%;height:100%;
                    background:linear-gradient(90deg,#00C2A8,#00E5CC);
                    border-radius:100px;transition:width 0.5s ease"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:0.5rem">
                <div style="font-size:0.75rem;color:#475569">${total_funded:,.0f} raised</div>
                <div style="font-size:0.75rem;color:#475569">${loan_amount:,.0f} target</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Key loan details
    st.markdown("<br>", unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)
    monthly_payment = loan.get("monthly_payment", 0)
    total_repaid    = float(monthly_payment or 0) * int(loan.get("term_months", 0))
    total_interest  = total_repaid - float(loan.get("amount", 0))

    for col, label, val, color in [
        (d1, "Monthly Payment",  fmt(monthly_payment),      C["teal"]),
        (d2, "Interest Rate",    f'{float(loan.get("annual_rate",0))*100:.1f}% APR', "#FFFFFF"),
        (d3, "Total Interest",   fmt(total_interest),        C["gold"]),
        (d4, "Payments Made",    f'{int(loan.get("payments_made",0))} / {int(loan.get("term_months",0))}', C["muted"]),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:rgba(15,32,53,0.6);border-radius:12px;padding:1.1rem;
                border:1px solid rgba(255,255,255,0.06);text-align:center">
                <div style="font-size:0.68rem;color:#475569;text-transform:uppercase;
                    letter-spacing:0.08em;margin-bottom:0.4rem">{label}</div>
                <div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;color:{color}">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    # Repayment schedule
    if supabase and loan.get("id") and status in ["funded","repaying","closed"]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;margin-bottom:1rem;color:#E2EDF4">Repayment Schedule</div>', unsafe_allow_html=True)
        try:
            sched = supabase.table("repayment_schedule").select("*")\
                .eq("loan_id", loan["id"]).order("payment_number").execute()
            if sched.data:
                df_s = pd.DataFrame(sched.data)
                df_s["status_fmt"] = df_s["status"].apply(
                    lambda s: f"✅ {s.title()}" if s=="paid" else f"🟡 {s.title()}" if s=="scheduled" else f"🔴 {s.title()}"
                )
                st.dataframe(
                    df_s[["payment_number","due_date","amount_due","principal_due","interest_due","status_fmt"]]\
                        .rename(columns={"payment_number":"#","due_date":"Due Date",
                                         "amount_due":"Payment","principal_due":"Principal",
                                         "interest_due":"Interest","status_fmt":"Status"}),
                    use_container_width=True, hide_index=True
                )
        except: pass

    # Multiple loans
    if len(loans) > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"View all {len(loans)} loan applications"):
            for l in loans[1:]:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.75rem 1rem;
                    background:rgba(15,32,53,0.6);border-radius:8px;margin-bottom:0.4rem;
                    border:1px solid rgba(255,255,255,0.05)">
                    <span style="color:#94A3B8;font-size:0.85rem">${float(l.get('amount',0)):,.0f} · {l.get('term_months','?')}mo</span>
                    <span style="color:#64748B;font-size:0.8rem">{l.get('created_at','')[:10]}</span>
                    <span style="color:{status_colors.get(l.get('status',''),C['muted'])};font-size:0.8rem;font-weight:600">{l.get('status','').title()}</span>
                </div>
                """, unsafe_allow_html=True)
