# Stack — Streamlit Apps

Two interactive Streamlit apps modelling Stack's borrower and investor products.

## Setup

```bash
pip install -r requirements.txt
```

## Run

**Borrower Calculator** (loan configurator with live amortization):
```bash
streamlit run stack_borrower.py
```

**Stacker Dashboard** (investor portfolio modeller with Monte Carlo):
```bash
streamlit run stack_stacker.py
```

---

## Borrower App Features
- Sliders: loan amount ($5k–$25k), term (12–60mo), credit score (580–850)
- Live rate calculation based on credit band
- Amortization chart (principal vs interest breakdown by month)
- Balance paydown curve
- Comparison vs credit card, bank loan, Prosper
- Rate sensitivity chart across all credit scores

## Stacker App Features
- Sliders: initial investment, monthly top-up, projection period (1–10yr)
- 4 risk profiles: Conservative / Balanced / Growth / Aggressive
- Fine-tune Grade A/B/C loan allocation manually
- Auto-reinvest toggle (shows compounding impact)
- Monte Carlo simulation: 300 paths, P10/P50/P90 bands + histogram
- Scenario comparison table across all risk profiles
- Cumulative breakdown: capital vs returns vs defaults

## Sharing
To share with others, deploy to Streamlit Community Cloud (free):
1. Push files to a GitHub repo
2. Go to share.streamlit.io
3. Connect repo → select app file → deploy
4. Share the URL
