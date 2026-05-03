"""
Stack Underwriting & Matching Engine
-------------------------------------
Underwriting criteria (per Underwriting Policy v1.1):
  1. Minimum Vantage score: 700
  2. Monthly repayment / net available income < 10%
  3. Application info matches credit report (manual / API flag)
  4. No more than 5 late payments in last 6 months

Matching model:
  - Approved loan → fractionalised across available Stacker capital
  - Each Stacker funds a fraction proportional to their available cash
  - Repayments apportioned back pro-rata to each Stacker's fraction

Mercury Bank integration: placeholder hooks for when API is live.
Payment processor: placeholder hooks (Stripe / Dwolla / ACH).
TransUnion API: placeholder for when company structure is set up.
"""

from __future__ import annotations
import math
from datetime import datetime, date
from typing import Optional


# ══════════════════════════════════════════════════════════════
# UNDERWRITING ENGINE
# ══════════════════════════════════════════════════════════════

# Thresholds per policy
MIN_VANTAGE_SCORE   = 700
MAX_REPAYMENT_RATIO = 0.10   # 10% of net monthly income
MAX_LATE_PAYMENTS   = 5      # in last 6 months
ORIGINATION_FEE_PCT = 0.05   # 5%

# Rate schedule by grade
GRADE_RATES = {
    "A": 0.089,   # 8.9%
    "B": 0.122,   # 12.2%
    "C": 0.155,   # 15.5%
}

# Adverse action reason codes (FCRA compliant)
ADVERSE_REASONS = {
    "low_score":          "Credit score below minimum threshold (700 Vantage)",
    "high_dti":           "Monthly repayment exceeds 10% of net available income",
    "info_mismatch":      "Information provided does not sufficiently match credit report",
    "late_payments":      "More than 5 late payments on credit report in last 6 months",
    "insufficient_data":  "Insufficient credit history to make a determination",
}


def calculate_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    r = annual_rate / 12
    if r == 0:
        return principal / term_months
    return principal * r * (1 + r)**term_months / ((1 + r)**term_months - 1)


def assign_grade(vantage_score: int, dti_ratio: float, late_payments: int) -> str:
    """
    Grade A: score >= 750, DTI < 6%, late payments <= 1
    Grade B: score >= 700, DTI < 8%, late payments <= 3
    Grade C: score >= 700, DTI < 10%, late payments <= 5
    """
    if vantage_score >= 750 and dti_ratio < 0.06 and late_payments <= 1:
        return "A"
    if vantage_score >= 720 and dti_ratio < 0.08 and late_payments <= 3:
        return "B"
    return "C"


def underwrite(
    loan_amount:       float,
    term_months:       int,
    vantage_score:     int,
    monthly_net_income: float,
    late_payments_6mo: int,
    info_matches_report: bool = True,  # Set by staff / TransUnion API
) -> dict:
    """
    Run underwriting criteria against application.
    Returns decision dict with pass/fail per criterion,
    grade, rate, and any adverse action reasons.
    """
    reasons = []
    criteria = {}

    # ── Criterion 1: Vantage score ──────────────────────────
    criteria["score_pass"] = vantage_score >= MIN_VANTAGE_SCORE
    if not criteria["score_pass"]:
        reasons.append("low_score")

    # ── Criterion 2: Repayment ratio ────────────────────────
    # Determine rate to calculate repayment (use Grade C worst case)
    trial_rate    = GRADE_RATES["C"]
    monthly_pmt   = calculate_monthly_payment(loan_amount, trial_rate, term_months)
    dti_ratio     = monthly_pmt / monthly_net_income if monthly_net_income > 0 else 1.0
    criteria["dti_pass"] = dti_ratio < MAX_REPAYMENT_RATIO
    if not criteria["dti_pass"]:
        reasons.append("high_dti")

    # ── Criterion 3: Info matches report ────────────────────
    criteria["info_match_pass"] = info_matches_report
    if not criteria["info_match_pass"]:
        reasons.append("info_mismatch")

    # ── Criterion 4: Late payments ──────────────────────────
    criteria["late_payment_pass"] = late_payments_6mo <= MAX_LATE_PAYMENTS
    if not criteria["late_payment_pass"]:
        reasons.append("late_payments")

    # ── Decision ─────────────────────────────────────────────
    approved = all(criteria.values())

    if approved:
        grade        = assign_grade(vantage_score, dti_ratio, late_payments_6mo)
        annual_rate  = GRADE_RATES[grade]
        monthly_pmt  = calculate_monthly_payment(loan_amount, annual_rate, term_months)
        origination  = loan_amount * ORIGINATION_FEE_PCT
        disbursed    = loan_amount - origination
        total_repaid = monthly_pmt * term_months
        total_interest = total_repaid - loan_amount
    else:
        grade        = None
        annual_rate  = None
        monthly_pmt  = None
        origination  = None
        disbursed    = None
        total_repaid = None
        total_interest = None

    return {
        "approved":        approved,
        "grade":           grade,
        "annual_rate":     annual_rate,
        "monthly_payment": monthly_pmt,
        "origination_fee": origination,
        "amount_disbursed":disbursed,
        "total_repaid":    total_repaid,
        "total_interest":  total_interest,
        "dti_ratio":       dti_ratio,
        "criteria":        criteria,
        "adverse_reasons": [ADVERSE_REASONS[r] for r in reasons],
        "adverse_codes":   reasons,
        "underwritten_at": datetime.utcnow().isoformat(),
    }


def build_repayment_schedule(
    loan_id:      str,
    principal:    float,
    annual_rate:  float,
    term_months:  int,
    start_date:   date,
) -> list[dict]:
    """Build full amortization schedule for a loan."""
    r       = annual_rate / 12
    pmt     = calculate_monthly_payment(principal, annual_rate, term_months)
    balance = principal
    schedule = []

    for m in range(1, term_months + 1):
        interest_due  = balance * r
        principal_due = pmt - interest_due
        balance       = max(0, balance - principal_due)
        due_date      = date(
            start_date.year + (start_date.month + m - 1) // 12,
            (start_date.month + m - 1) % 12 + 1,
            min(start_date.day, 28)
        )
        schedule.append({
            "loan_id":       loan_id,
            "payment_number":m,
            "due_date":      due_date.isoformat(),
            "amount_due":    round(pmt, 2),
            "principal_due": round(principal_due, 2),
            "interest_due":  round(interest_due, 2),
            "balance_after": round(balance, 2),
            "status":        "scheduled",
        })

    return schedule


# ══════════════════════════════════════════════════════════════
# MATCHING ENGINE
# ══════════════════════════════════════════════════════════════

def match_loan_to_stackers(
    supabase,
    loan_id:      str,
    loan_amount:  float,
    loan_grade:   str,
) -> dict:
    """
    Fractionalise a loan across available Stacker capital.

    Algorithm:
    1. Fetch all Stacker portfolios with available_cash > 0
    2. Filter by risk profile compatibility with loan grade
    3. Calculate each Stacker's proportional contribution
    4. Create loan_match records
    5. Deduct from each Stacker's available_cash, add to deployed_capital
    6. Update loan total_funded and num_stackers
    7. If fully funded, mark loan as funded

    Returns: dict with match results
    """
    try:
        # Fetch available Stacker capital
        result = supabase.table("stacker_portfolios").select("*")\
            .gt("available_cash", 0).execute()
        portfolios = result.data or []

        if not portfolios:
            return {"success": False, "reason": "No Stacker capital available", "matches": []}

        # Filter compatible portfolios by grade preference
        grade_pct_field = {
            "A": "grade_a_pct",
            "B": "grade_b_pct",
            "C": "grade_c_pct",
        }.get(loan_grade, "grade_b_pct")

        # Weight each Stacker by their available cash × grade preference
        weighted = []
        for p in portfolios:
            available   = float(p.get("available_cash", 0))
            grade_pref  = float(p.get(grade_pct_field, 30)) / 100
            weight      = available * grade_pref
            if weight > 0:
                weighted.append({**p, "_weight": weight, "_available": available})

        if not weighted:
            return {"success": False, "reason": "No compatible Stacker capital", "matches": []}

        total_weight   = sum(p["_weight"] for p in weighted)
        total_available = sum(p["_available"] for p in weighted)
        amount_to_fund = min(loan_amount, total_available)
        fraction_scale = amount_to_fund / loan_amount

        matches = []
        total_matched = 0

        for p in weighted:
            fraction_pct    = p["_weight"] / total_weight
            fraction_amount = round(amount_to_fund * fraction_pct, 2)
            if fraction_amount <= 0:
                continue

            # Cap at what the Stacker actually has
            fraction_amount = min(fraction_amount, p["_available"])
            total_matched  += fraction_amount

            match_record = {
                "loan_id":        loan_id,
                "stacker_id":     p["user_id"],
                "portfolio_id":   p["id"],
                "fraction_amount":fraction_amount,
                "fraction_pct":   round(fraction_pct, 6),
                "status":         "active",
                "interest_earned":0,
                "principal_returned":0,
            }
            matches.append((match_record, p))

        # Write matches and update portfolios
        inserted_matches = []
        for match_record, portfolio in matches:
            # Insert match
            mr = supabase.table("loan_matches").insert(match_record).execute()
            if mr.data:
                inserted_matches.append(mr.data[0])

            # Update Stacker portfolio
            new_available = float(portfolio["available_cash"]) - match_record["fraction_amount"]
            new_deployed  = float(portfolio.get("deployed_capital", 0)) + match_record["fraction_amount"]
            new_count     = int(portfolio.get("num_active_loans", 0)) + 1
            supabase.table("stacker_portfolios").update({
                "available_cash":   max(0, round(new_available, 2)),
                "deployed_capital": round(new_deployed, 2),
                "num_active_loans": new_count,
                "updated_at":       datetime.utcnow().isoformat(),
            }).eq("id", portfolio["id"]).execute()

            # Record transaction
            supabase.table("transactions").insert({
                "user_id":    portfolio["user_id"],
                "loan_id":    loan_id,
                "type":       "investment",
                "amount":     match_record["fraction_amount"],
                "direction":  "out",
                "description":f"Capital deployed to loan {loan_id[:8]} (Grade {match_record.get('grade','?')})",
            }).execute()

        # Update loan record
        fully_funded = total_matched >= loan_amount * 0.99  # 99% threshold
        supabase.table("loan_applications").update({
            "total_funded":    round(total_matched, 2),
            "num_stackers":    len(inserted_matches),
            "status":          "funded" if fully_funded else "approved",
            "funded_at":       datetime.utcnow().isoformat() if fully_funded else None,
            "fully_funded_at": datetime.utcnow().isoformat() if fully_funded else None,
            "outstanding_balance": loan_amount,
        }).eq("id", loan_id).execute()

        return {
            "success":       True,
            "total_matched": total_matched,
            "fully_funded":  fully_funded,
            "num_stackers":  len(inserted_matches),
            "matches":       inserted_matches,
        }

    except Exception as e:
        return {"success": False, "reason": str(e), "matches": []}


# ══════════════════════════════════════════════════════════════
# REPAYMENT APPORTIONMENT ENGINE
# ══════════════════════════════════════════════════════════════

def apportion_repayment(
    supabase,
    loan_id:        str,
    payment_amount: float,
    payment_number: int,
) -> dict:
    """
    When a borrower makes a payment, split it back to all Stackers
    who funded that loan, pro-rata by their fraction_pct.

    Also deducts Stack's 2% management fee per repayment.
    Returns apportionment results.
    """
    MANAGEMENT_FEE_RATE = 0.02

    try:
        # Get all active matches for this loan
        matches_result = supabase.table("loan_matches").select("*")\
            .eq("loan_id", loan_id).eq("status", "active").execute()
        matches = matches_result.data or []

        if not matches:
            return {"success": False, "reason": "No active matches for this loan"}

        # Get loan details for interest/principal split
        loan_result = supabase.table("loan_applications").select("*")\
            .eq("id", loan_id).limit(1).execute()
        loan = loan_result.data[0] if loan_result.data else {}

        # Get schedule entry for this payment
        sched_result = supabase.table("repayment_schedule").select("*")\
            .eq("loan_id", loan_id)\
            .eq("payment_number", payment_number).limit(1).execute()
        schedule_entry = sched_result.data[0] if sched_result.data else {}

        interest_portion   = float(schedule_entry.get("interest_due", payment_amount * 0.15))
        principal_portion  = payment_amount - interest_portion

        # Deduct management fee from interest
        management_fee     = interest_portion * MANAGEMENT_FEE_RATE
        distributable      = payment_amount - management_fee

        apportionments = []
        total_distributed = 0

        for match in matches:
            fraction_pct    = float(match.get("fraction_pct", 0))
            stacker_amount  = round(distributable * fraction_pct, 2)
            stacker_interest= round(interest_portion * fraction_pct * (1 - MANAGEMENT_FEE_RATE), 2)
            stacker_principal = round(principal_portion * fraction_pct, 2)

            if stacker_amount <= 0:
                continue

            # Update match record
            new_interest  = float(match.get("interest_earned", 0)) + stacker_interest
            new_principal = float(match.get("principal_returned", 0)) + stacker_principal
            supabase.table("loan_matches").update({
                "interest_earned":    round(new_interest, 2),
                "principal_returned": round(new_principal, 2),
            }).eq("id", match["id"]).execute()

            # Credit Stacker's portfolio (reinvest principal, add interest to balance)
            portfolio_result = supabase.table("stacker_portfolios").select("*")\
                .eq("id", match["portfolio_id"]).limit(1).execute()
            if portfolio_result.data:
                port = portfolio_result.data[0]
                supabase.table("stacker_portfolios").update({
                    "available_cash":  round(float(port.get("available_cash",0)) + stacker_amount, 2),
                    "deployed_capital":round(max(0, float(port.get("deployed_capital",0)) - stacker_principal), 2),
                    "total_earned":    round(float(port.get("total_earned",0)) + stacker_interest, 2),
                    "current_balance": round(float(port.get("current_balance",0)) + stacker_interest, 2),
                    "updated_at":      datetime.utcnow().isoformat(),
                }).eq("id", match["portfolio_id"]).execute()

            # Record transaction for Stacker
            supabase.table("transactions").insert({
                "user_id":    match["stacker_id"],
                "loan_id":    loan_id,
                "match_id":   match["id"],
                "type":       "stacker_return",
                "amount":     stacker_amount,
                "direction":  "in",
                "description":f"Repayment #{payment_number} — ${stacker_principal:.2f} principal + ${stacker_interest:.2f} interest",
            }).execute()

            total_distributed += stacker_amount
            apportionments.append({
                "stacker_id":     match["stacker_id"],
                "amount":         stacker_amount,
                "principal":      stacker_principal,
                "interest":       stacker_interest,
                "fraction_pct":   fraction_pct,
            })

        # Record management fee transaction
        supabase.table("transactions").insert({
            "user_id":    loan.get("user_id", ""),
            "loan_id":    loan_id,
            "type":       "management_fee",
            "amount":     management_fee,
            "direction":  "in",
            "description":f"2% management fee on payment #{payment_number}",
        }).execute()

        # Update schedule entry as paid
        if sched_result.data:
            supabase.table("repayment_schedule").update({
                "status":      "paid",
                "paid_at":     datetime.utcnow().isoformat(),
                "amount_paid": payment_amount,
            }).eq("id", sched_result.data[0]["id"]).execute()

        # Update loan outstanding balance
        new_outstanding = max(0, float(loan.get("outstanding_balance", 0)) - principal_portion)
        payments_made   = int(loan.get("payments_made", 0)) + 1
        new_status      = "closed" if new_outstanding < 0.01 else "repaying"
        supabase.table("loan_applications").update({
            "outstanding_balance": round(new_outstanding, 2),
            "payments_made":       payments_made,
            "status":              new_status,
        }).eq("id", loan_id).execute()

        return {
            "success":          True,
            "payment_amount":   payment_amount,
            "management_fee":   management_fee,
            "total_distributed":total_distributed,
            "num_stackers":     len(apportionments),
            "apportionments":   apportionments,
            "new_outstanding":  new_outstanding,
            "loan_closed":      new_status == "closed",
        }

    except Exception as e:
        return {"success": False, "reason": str(e)}


# ══════════════════════════════════════════════════════════════
# MERCURY BANK INTEGRATION (PLACEHOLDER)
# ══════════════════════════════════════════════════════════════

class MercuryBank:
    """
    Placeholder Mercury Bank API integration.
    Mercury supports ACH transfers and real-time balance checking.

    When ready to connect:
    1. Sign up at mercury.com → get API key
    2. Add MERCURY_API_KEY to Streamlit secrets
    3. Uncomment the real API calls below
    4. Mercury API docs: https://docs.mercury.com/reference

    Required account structure:
    - Stack Operating Account (receives origination fees, management fees)
    - Stack Escrow Account (holds Stacker capital before deployment)
    - Stack Reserve Account (holds idle Stacker cash)
    """

    BASE_URL = "https://api.mercury.com/api/v1"

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.enabled = bool(api_key)

    def get_account_balance(self, account_id: str) -> dict:
        """Get current balance of a Mercury account."""
        if not self.enabled:
            return {"status": "placeholder", "balance": 0, "message": "Mercury API not yet connected"}
        # TODO: Uncomment when API key available
        # import requests
        # r = requests.get(f"{self.BASE_URL}/account/{account_id}",
        #     headers={"Authorization": f"Bearer {self.api_key}"})
        # return r.json()
        return {"status": "placeholder"}

    def initiate_ach_transfer(
        self,
        from_account: str,
        to_routing:   str,
        to_account:   str,
        amount:       float,
        description:  str,
    ) -> dict:
        """
        Initiate ACH transfer (Stacker deposit or loan disbursement).
        Mercury supports same-day ACH.
        """
        if not self.enabled:
            return {
                "status": "placeholder",
                "message": "Mercury API not connected. Configure MERCURY_API_KEY in secrets.",
                "amount": amount,
                "description": description,
            }
        # TODO: real call here
        return {"status": "placeholder"}

    def disburse_loan(self, loan_id: str, amount: float, routing: str, account: str) -> dict:
        """Disburse approved loan funds to borrower's bank account."""
        return self.initiate_ach_transfer(
            from_account="stack_escrow_account",
            to_routing=routing,
            to_account=account,
            amount=amount,
            description=f"Stack loan disbursement — Loan {loan_id[:8]}",
        )

    def receive_repayment(self, loan_id: str, amount: float) -> dict:
        """Record incoming repayment (triggered by payment processor webhook)."""
        return {
            "status":  "placeholder",
            "loan_id": loan_id,
            "amount":  amount,
            "message": "Payment processor webhook not yet configured",
        }


# ══════════════════════════════════════════════════════════════
# TRANSUNION API (PLACEHOLDER)
# ══════════════════════════════════════════════════════════════

class TransUnionAPI:
    """
    Placeholder TransUnion credit pull integration.

    When company structure is set up:
    1. Apply for TransUnion developer access at developer.transunion.com
    2. Complete permissible purpose verification (lending)
    3. Get API credentials → add to secrets
    4. Implement OAuth 2.0 flow
    5. Replace placeholder methods below with real calls

    Stack will use:
    - Soft pull at application (no score impact)
    - Hard pull only at final approval (FCRA compliant)
    - Vantage 4.0 score model
    """

    def __init__(self, api_key: str = None, environment: str = "sandbox"):
        self.api_key     = api_key
        self.environment = environment
        self.enabled     = bool(api_key)
        self.base_url    = "https://api.transunion.com" if environment == "production" else "https://sandbox.transunion.com"

    def soft_pull(self, first_name: str, last_name: str, dob: str,
                  ssn_last4: str, address: str, zip_code: str) -> dict:
        """Soft credit pull — no impact to applicant's score."""
        if not self.enabled:
            return {
                "status":          "placeholder",
                "message":         "TransUnion API not yet configured",
                "vantage_score":   None,
                "late_payments_6mo": None,
                "info_match":      None,
            }
        # TODO: real TransUnion API call
        return {"status": "placeholder"}

    def hard_pull(self, applicant_data: dict) -> dict:
        """Hard credit pull — performed only at final approval."""
        if not self.enabled:
            return {"status": "placeholder", "message": "TransUnion API not yet configured"}
        return {"status": "placeholder"}


# ══════════════════════════════════════════════════════════════
# ADVERSE ACTION NOTICE GENERATOR
# ══════════════════════════════════════════════════════════════

def generate_adverse_action_notice(
    applicant_name:  str,
    applicant_email: str,
    applicant_address: str,
    adverse_reasons: list[str],
    vantage_score:   Optional[int] = None,
    application_date: str = None,
) -> str:
    """
    Generate FCRA-compliant Adverse Action Notice text.
    Per Fair Credit Reporting Act requirements.
    """
    today = date.today().strftime("%B %d, %Y")
    reasons_text = "\n".join(f"  • {r}" for r in adverse_reasons)
    score_text = f"\nYour Vantage credit score: {vantage_score}\nScores range from 300 (low) to 850 (high).\n" if vantage_score else ""

    return f"""ADVERSE ACTION NOTICE
Date: {today}

{applicant_name}
{applicant_address}

Dear {applicant_name},

Thank you for applying for a personal loan with Stack Financial Technologies.
After careful consideration of your application, we regret to inform you that
we are unable to approve your loan application at this time.

REASONS FOR ADVERSE ACTION:

Your application was reviewed in accordance with our lending criteria.
The decision to not extend credit was based on the following reason(s):

{reasons_text}

CREDIT REPORT INFORMATION:
{score_text}
This decision was based in whole or in part on information obtained from:
TransUnion Consumer Solutions
P.O. Box 2000
Chester, PA 19016
1-800-916-8800

The credit reporting agency played no part in our decision and is unable to
provide specific reasons why adverse action was taken.

YOUR RIGHTS UNDER THE FAIR CREDIT REPORTING ACT:
• You have the right to obtain a free copy of your credit report from
  TransUnion within 60 days of receiving this notice.
• You have the right to dispute the accuracy or completeness of any
  information in your credit report.
• You have the right to add a consumer statement to your credit report.

EQUAL CREDIT OPPORTUNITY ACT NOTICE:
The Federal Equal Credit Opportunity Act prohibits creditors from
discriminating against credit applicants on the basis of race, color,
religion, national origin, sex, marital status, age, or because all or
part of the applicant's income derives from any public assistance program,
or because the applicant has in good faith exercised any right under the
Consumer Credit Protection Act.

The Federal agency administering compliance: Federal Trade Commission,
Consumer Response Center, 600 Pennsylvania Avenue NW, Washington, DC 20580.

We encourage you to apply again in the future once the concerns outlined
in this notice have been addressed. If you have any questions, please
contact us at support@stacklend.com or 844-306-3568.

Sincerely,
Stack Lending Team
Stack Financial Technologies Inc.
90 Vantis Drive Unit #3087
Aliso Viejo, CA 92656
support@stacklend.com | 844-306-3568
"""
