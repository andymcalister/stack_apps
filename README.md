# Stack — Full Setup Guide

## File Structure

```
stack_apps/
├── stack_home.py           ← Main app (run this)
├── stack_borrower.py       ← Borrower calculator
├── stack_stacker.py        ← Stacker dashboard
├── requirements.txt
├── supabase_schema.sql     ← Run once in Supabase
├── .gitignore
└── .streamlit/
    └── secrets.toml        ← Your credentials (never commit this)
```

---

## Step 1 — Set up Supabase (free database)

1. Go to supabase.com → New Project → name it `stack`
2. Wait ~2 mins to provision
3. Go to SQL Editor → paste supabase_schema.sql → Run
4. Go to Settings → API → copy Project URL and anon key

## Step 2 — Add credentials

Edit `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://yourproject.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

## Step 3 — Install & run

```bash
pip install -r requirements.txt
streamlit run stack_home.py
```

## Step 4 — Deploy

Push to GitHub (secrets.toml is gitignored).
On share.streamlit.io: connect repo, set main file to stack_home.py, paste secrets in Advanced Settings.

## On MFA
Ask me to add free TOTP MFA (Google Authenticator) — takes about 20 mins to build.
