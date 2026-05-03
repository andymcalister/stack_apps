"""
Stack Loan Application Form
Fields match underwriting policy requirements.
DEMO MODE: Form is visible but locked — no real data collected yet.
TransUnion API integration pending company structure setup.
"""
import streamlit as st
from datetime import date
from stack_engine import (
    underwrite, build_repayment_schedule, match_loan_to_stackers,
    generate_adverse_action_notice, GRADE_RATES, calculate_monthly_payment
)

supabase = st.session_state.get("_supabase")
user     = st.session_state.get("user", {})

DEMO_MODE = True  # Set False when ready to collect real data + TransUnion API live

C = dict(teal="#00C2A8", gold="#F5A623", red="#EF4444", green="#10B981")

# ── DEMO DATA (pre-fills form in demo mode) ──────────────────
DEMO = {
    "first_name":    "Andy",
    "last_name":     "McAlister",
    "dob":           "1985-06-15",
    "ssn_last4":     "1234",
    "email":         "andy@example.com",
    "phone":         "(555) 123-4567",
    "address":       "123 Main Street",
    "city":          "Tampa",
    "state":         "Florida",
    "zip":           "33601",
    "employer":      "Acme Corporation",
    "employment_status": "Full-time employed",
    "years_employed":    3,
    "gross_income":  95000,
    "other_income":  0,
    "monthly_rent":  1800,
    "loan_amount":   15000,
    "loan_purpose":  "Debt consolidation",
    "term_months":   36,
    "vantage_score": 742,
    "late_payments": 0,
    "existing_monthly_debt": 450,
}

# ── HEADER ───────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem">
    <div style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;color:#FFFFFF">
        Apply for a Stack Loan
    </div>
    <div style="color:#64748B;font-size:0.875rem;margin-top:0.25rem">
        Rates from 8.9% APR · $5,000–$25,000 · Florida residents only
    </div>
</div>
""", unsafe_allow_html=True)

# ── DEMO MODE BANNER ─────────────────────────────────────────
if DEMO_MODE:
    st.markdown("""
    <div style="background:rgba(245,166,35,0.1);border:1px solid rgba(245,166,35,0.4);
        border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1.5rem">
        <div style="display:flex;align-items:center;gap:0.75rem">
            <span style="font-size:1.5rem">🚧</span>
            <div>
                <div style="font-weight:700;color:#FDE68A;font-size:0.95rem;margin-bottom:0.25rem">
                    Application Portal — Preview Mode
                </div>
                <div style="font-size:0.85rem;color:#92400E;line-height:1.6">
                    This application form is displayed for preview purposes only.
                    <strong style="color:#FDE68A">No real data is being collected or stored.</strong>
                    Full applications will open once our TransUnion credit pull API is configured
                    and our Florida lending licence is active. You'll be notified by email the moment
                    applications open. The form below shows exactly what you'll need to complete.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── ELIGIBILITY CHECKER ──────────────────────────────────────
st.markdown("""
<div style="background:rgba(15,32,53,0.8);border:1px solid rgba(0,194,168,0.2);
    border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1.5rem">
    <div style="font-weight:700;color:#E2EDF4;margin-bottom:0.75rem;font-size:0.95rem">
        ✅ Quick Eligibility Check
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.84rem">
        <div style="color:#94A3B8">• Florida resident</div>
        <div style="color:#94A3B8">• At least 18 years old</div>
        <div style="color:#94A3B8">• Vantage score 700+</div>
        <div style="color:#94A3B8">• Valid SSN</div>
        <div style="color:#94A3B8">• Monthly repayment &lt;10% of net income</div>
        <div style="color:#94A3B8">• ≤5 late payments in last 6 months</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── FORM ─────────────────────────────────────────────────────
with st.form("loan_application", clear_on_submit=False):

    # SECTION 1: Personal Information
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;
        padding-bottom:0.6rem;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div style="width:28px;height:28px;background:rgba(0,194,168,0.12);border-radius:8px;
            display:flex;align-items:center;justify-content:center;font-size:0.85rem;
            font-weight:800;color:#00C2A8;font-family:Syne,sans-serif">1</div>
        <div style="font-weight:700;color:#E2EDF4">Personal Information</div>
    </div>
    """, unsafe_allow_html=True)

    p1, p2 = st.columns(2)
    with p1:
        first_name = st.text_input("First name *", value=DEMO["first_name"] if DEMO_MODE else "", disabled=DEMO_MODE)
        dob        = st.text_input("Date of birth (MM/DD/YYYY) *", value=DEMO["dob"] if DEMO_MODE else "", disabled=DEMO_MODE, help="Must be 18+")
        phone      = st.text_input("Phone number *", value=DEMO["phone"] if DEMO_MODE else "", disabled=DEMO_MODE)
    with p2:
        last_name  = st.text_input("Last name *", value=DEMO["last_name"] if DEMO_MODE else "", disabled=DEMO_MODE)
        ssn_last4  = st.text_input("Last 4 digits of SSN *", value=DEMO["ssn_last4"] if DEMO_MODE else "", max_chars=4, disabled=DEMO_MODE, help="Used for identity verification only")
        email_app  = st.text_input("Email address *", value=DEMO["email"] if DEMO_MODE else user.get("email",""), disabled=DEMO_MODE)

    # SECTION 2: Address
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;
        padding-bottom:0.6rem;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div style="width:28px;height:28px;background:rgba(0,194,168,0.12);border-radius:8px;
            display:flex;align-items:center;justify-content:center;font-size:0.85rem;
            font-weight:800;color:#00C2A8;font-family:Syne,sans-serif">2</div>
        <div style="font-weight:700;color:#E2EDF4">Florida Address</div>
    </div>
    """, unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        address = st.text_input("Street address *", value=DEMO["address"] if DEMO_MODE else "", disabled=DEMO_MODE)
        state   = st.selectbox("State *", ["Florida"], disabled=DEMO_MODE, help="Stack currently serves Florida residents only")
    with a2:
        city    = st.text_input("City *", value=DEMO["city"] if DEMO_MODE else "", disabled=DEMO_MODE)
        zip_code= st.text_input("ZIP code *", value=DEMO["zip"] if DEMO_MODE else "", max_chars=5, disabled=DEMO_MODE)

    # SECTION 3: Employment & Income
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;
        padding-bottom:0.6rem;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div style="width:28px;height:28px;background:rgba(0,194,168,0.12);border-radius:8px;
            display:flex;align-items:center;justify-content:center;font-size:0.85rem;
            font-weight:800;color:#00C2A8;font-family:Syne,sans-serif">3</div>
        <div style="font-weight:700;color:#E2EDF4">Employment & Income</div>
        <div style="font-size:0.75rem;color:#475569;margin-left:0.5rem">Used to calculate repayment-to-income ratio</div>
    </div>
    """, unsafe_allow_html=True)

    e1, e2 = st.columns(2)
    with e1:
        employment_status = st.selectbox("Employment status *",
            ["Full-time employed","Part-time employed","Self-employed","Contract / Freelance","Retired","Other"],
            disabled=DEMO_MODE,
            index=["Full-time employed","Part-time employed","Self-employed","Contract / Freelance","Retired","Other"].index(DEMO["employment_status"]) if DEMO_MODE else 0
        )
        employer        = st.text_input("Employer / Company name *", value=DEMO["employer"] if DEMO_MODE else "", disabled=DEMO_MODE)
        gross_income    = st.number_input("Annual gross income ($) *", min_value=0, value=DEMO["gross_income"] if DEMO_MODE else 0, disabled=DEMO_MODE, help="Before tax")
        monthly_rent    = st.number_input("Monthly rent / mortgage ($) *", min_value=0, value=DEMO["monthly_rent"] if DEMO_MODE else 0, disabled=DEMO_MODE)
    with e2:
        years_employed  = st.number_input("Years with current employer *", min_value=0.0, max_value=50.0, value=float(DEMO["years_employed"]) if DEMO_MODE else 0.0, step=0.5, disabled=DEMO_MODE)
        job_title       = st.text_input("Job title", value="Senior Account Executive" if DEMO_MODE else "", disabled=DEMO_MODE)
        other_income    = st.number_input("Other annual income ($)", min_value=0, value=DEMO["other_income"] if DEMO_MODE else 0, disabled=DEMO_MODE, help="e.g. rental income, investments")
        existing_debt   = st.number_input("Total existing monthly debt payments ($) *", min_value=0, value=DEMO["existing_monthly_debt"] if DEMO_MODE else 0, disabled=DEMO_MODE, help="Credit cards, auto loans, student loans, etc.")

    # SECTION 4: Loan Details
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;
        padding-bottom:0.6rem;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div style="width:28px;height:28px;background:rgba(0,194,168,0.12);border-radius:8px;
            display:flex;align-items:center;justify-content:center;font-size:0.85rem;
            font-weight:800;color:#00C2A8;font-family:Syne,sans-serif">4</div>
        <div style="font-weight:700;color:#E2EDF4">Loan Request</div>
    </div>
    """, unsafe_allow_html=True)

    l1, l2 = st.columns(2)
    with l1:
        loan_amount = st.number_input("Loan amount requested ($) *",
            min_value=5000, max_value=25000, value=DEMO["loan_amount"] if DEMO_MODE else 10000,
            step=500, disabled=DEMO_MODE)
        loan_purpose = st.selectbox("Loan purpose *",
            ["Debt consolidation","Home improvement","Medical expenses",
             "Auto repair","Wedding","Vacation","Moving expenses",
             "Business (personal use)","Other"],
            disabled=DEMO_MODE,
            index=0)
    with l2:
        term_months = st.selectbox("Preferred term *",
            [12, 24, 36, 48, 60],
            format_func=lambda x: f"{x} months ({x//12} year{'s' if x>12 else ''})",
            index=[12,24,36,48,60].index(DEMO["term_months"]) if DEMO_MODE else 2,
            disabled=DEMO_MODE)
        purpose_detail = st.text_area("Tell us more about your loan purpose",
            value="Looking to consolidate three credit cards at 24%+ APR into a single lower-rate payment." if DEMO_MODE else "",
            height=100, disabled=DEMO_MODE)

    # SECTION 5: Bank Account for Disbursement
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;
        padding-bottom:0.6rem;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div style="width:28px;height:28px;background:rgba(0,194,168,0.12);border-radius:8px;
            display:flex;align-items:center;justify-content:center;font-size:0.85rem;
            font-weight:800;color:#00C2A8;font-family:Syne,sans-serif">5</div>
        <div style="font-weight:700;color:#E2EDF4">Bank Account (for disbursement)</div>
        <div style="font-size:0.75rem;color:#475569;margin-left:0.5rem">Funds sent here via ACH within 5 business days</div>
    </div>
    """, unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        bank_name    = st.text_input("Bank name *", value="Chase Bank" if DEMO_MODE else "", disabled=DEMO_MODE)
        routing_no   = st.text_input("Routing number *", value="021000021" if DEMO_MODE else "", max_chars=9, disabled=DEMO_MODE)
    with b2:
        account_type = st.selectbox("Account type *", ["Checking","Savings"], disabled=DEMO_MODE)
        account_no   = st.text_input("Account number *", value="****4521" if DEMO_MODE else "", disabled=DEMO_MODE, help="Your account number is encrypted and stored securely")

    # SECTION 6: Declarations
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(15,32,53,0.6);border-radius:10px;padding:1.25rem;
        border:1px solid rgba(255,255,255,0.06);margin-bottom:1rem">
        <div style="font-size:0.8rem;color:#64748B;line-height:1.75">
            <strong style="color:#94A3B8">By submitting this application you confirm that:</strong><br>
            • All information provided is true, accurate and complete to the best of your knowledge<br>
            • You authorise Stack to obtain a soft credit pull from TransUnion for assessment purposes<br>
            • You understand a hard credit pull will be performed only if your application proceeds to final approval<br>
            • You have read and agree to Stack's Terms of Service and Privacy Policy<br>
            • Loan funds will be used only for personal, family, or household purposes as permitted under TILA<br>
            • You are a Florida resident aged 18 or over with a valid US Social Security Number
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1 = st.checkbox("I confirm all information is accurate and I authorise a credit pull", disabled=DEMO_MODE, value=DEMO_MODE)
    c2 = st.checkbox("I agree to Stack's Terms of Service, Privacy Policy and TILA Disclosure", disabled=DEMO_MODE, value=DEMO_MODE)
    c3 = st.checkbox("I confirm I am a Florida resident aged 18+ with a valid SSN", disabled=DEMO_MODE, value=DEMO_MODE)

    st.markdown("<br>", unsafe_allow_html=True)

    submitted = st.form_submit_button(
        "📋 Submit Application →" if not DEMO_MODE else "🚧 Applications Open Soon",
        use_container_width=True,
        disabled=DEMO_MODE,
    )

# ── FORM SUBMISSION (LIVE MODE ONLY) ─────────────────────────
if submitted and not DEMO_MODE:
    if not all([c1, c2, c3]):
        st.error("Please check all declaration boxes before submitting.")
    elif not supabase or not user.get("id"):
        st.error("Please log in to submit an application.")
    else:
        # Calculate net income for DTI
        gross_annual    = float(gross_income) + float(other_income)
        estimated_tax   = 0.22  # rough federal estimate
        net_monthly     = (gross_annual * (1 - estimated_tax)) / 12 - float(monthly_rent) - float(existing_debt)

        # Underwrite — TransUnion values are placeholder until API live
        uw = underwrite(
            loan_amount        = float(loan_amount),
            term_months        = int(term_months),
            vantage_score      = 700,   # Replace with TransUnion result
            monthly_net_income = max(1, net_monthly),
            late_payments_6mo  = 0,     # Replace with TransUnion result
            info_matches_report= True,  # Replace with TransUnion verification
        )

        if uw["approved"]:
            # Save approved application
            result = supabase.table("loan_applications").insert({
                "user_id":          user["id"],
                "amount":           float(loan_amount),
                "term_months":      int(term_months),
                "purpose":          loan_purpose,
                "annual_rate":      uw["annual_rate"],
                "monthly_payment":  uw["monthly_payment"],
                "grade":            uw["grade"],
                "status":           "approved",
                "outstanding_balance": float(loan_amount),
                "created_at":       __import__('datetime').datetime.utcnow().isoformat(),
            }).execute()

            if result.data:
                loan_id = result.data[0]["id"]

                # Build repayment schedule
                schedule = build_repayment_schedule(
                    loan_id     = loan_id,
                    principal   = float(loan_amount),
                    annual_rate = uw["annual_rate"],
                    term_months = int(term_months),
                    start_date  = __import__('datetime').date.today(),
                )
                supabase.table("repayment_schedule").insert(schedule).execute()

                # Trigger matching engine
                match_result = match_loan_to_stackers(
                    supabase   = supabase,
                    loan_id    = loan_id,
                    loan_amount= float(loan_amount),
                    loan_grade = uw["grade"],
                )

                st.success(f"✅ Application approved! Grade {uw['grade']} loan at {uw['annual_rate']*100:.1f}% APR.")
                st.balloons()

                if match_result["success"]:
                    st.info(f"Your loan is {match_result['total_matched']/float(loan_amount)*100:.0f}% funded across {match_result['num_stackers']} Stackers.")
        else:
            # Generate adverse action notice
            notice = generate_adverse_action_notice(
                applicant_name    = f"{first_name} {last_name}",
                applicant_email   = email_app,
                applicant_address = f"{address}, {city}, FL {zip_code}",
                adverse_reasons   = uw["adverse_reasons"],
                application_date  = str(date.today()),
            )
            st.error("We're unable to approve your application at this time.")
            with st.expander("View Adverse Action Notice"):
                st.text(notice)

# ── RATE PREVIEW (always visible) ────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="font-family:Syne,sans-serif;font-size:0.95rem;font-weight:700;
    margin-bottom:1rem;color:#E2EDF4">Rate Preview by Grade</div>
""", unsafe_allow_html=True)

rp1, rp2, rp3 = st.columns(3)
for col, grade, rate, desc, color in [
    (rp1, "A", 8.9,  "Excellent credit (750+)", C["teal"]),
    (rp2, "B", 12.2, "Good credit (720–749)",   C["gold"]),
    (rp3, "C", 15.5, "Fair credit (700–719)",   "#8B5CF6"),
]:
    demo_pmt = calculate_monthly_payment(15000, rate/100, 36)
    with col:
        st.markdown(f"""
        <div style="background:rgba(15,32,53,0.7);border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;padding:1.25rem;text-align:center;border-top:2px solid {color}">
            <div style="font-size:0.7rem;color:#475569;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:0.4rem">Grade {grade}</div>
            <div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:{color}">{rate}%</div>
            <div style="font-size:0.75rem;color:#64748B;margin-top:0.25rem">{desc}</div>
            <div style="font-size:0.8rem;color:#94A3B8;margin-top:0.6rem">
                ${demo_pmt:,.0f}/mo on $15k · 36mo
            </div>
        </div>
        """, unsafe_allow_html=True)
