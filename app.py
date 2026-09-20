import streamlit as st
import sqlite3
import pandas as pd
import re
import json
import os
import requests
import xml.etree.ElementTree as ET
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="KasuAI — குடும்ப நிதி",
    page_icon="🪙",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CLEAN MOBILE-FIRST STYLING (No Tamil font issues) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. HIDE ALL STREAMLIT CHROME */
    #MainMenu, header, footer, 
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"],
    .stDeployButton,
    #manage-app-button,
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    .viewerBadge_container__1QSob,
    button[title="View app in Streamlit Community Cloud"],
    .css-15zrgzn, .css-vk3wp9 {
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 2. MOBILE CONTAINER */
    .block-container {
        max-width: 560px !important;
        padding-top: 0.25rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        margin: 0 auto !important;
    }

    html, body, [data-testid="stAppViewContainer"], section.main {
        overscroll-behavior-y: contain !important;
        overscroll-behavior: contain !important;
    }

    body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        -webkit-font-smoothing: antialiased;
    }

    /* 3. APP BAR */
    .mobile-app-bar {
        background: #ffffff;
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .brand-name {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
        line-height: 1;
    }
    .brand-tag {
        font-size: 11px;
        font-weight: 500;
        color: #64748b;
        margin-top: 2px;
    }
    .live-badge {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .live-dot {
        width: 7px;
        height: 7px;
        background: #22c55e;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(34, 197, 94, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    /* 4. IOS PILL TOGGLE */
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        background: #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 4px !important;
        gap: 4px !important;
        margin-bottom: 12px !important;
        width: 100% !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        flex: 1 !important;
        background: transparent !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 9px 4px !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"],
    div[data-testid="stRadio"] div[role="radiogroup"] svg,
    div[data-testid="stRadio"] div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div {
        display: none !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] p {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #475569 !important;
        margin: 0 !important;
        text-align: center !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        background: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {
        color: #0284c7 !important;
        font-weight: 800 !important;
    }

    /* 5. WALLET CARD */
    .wallet-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0369a1 100%);
        border-radius: 20px;
        padding: 18px 16px;
        color: #ffffff;
        margin-bottom: 12px;
        box-shadow: 0 10px 24px -4px rgba(15, 23, 42, 0.28);
        position: relative;
        overflow: hidden;
    }
    .wallet-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .wallet-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        color: #94a3b8;
    }
    .wallet-month-tag {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.15);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        color: #e0f2fe;
    }
    .wallet-amount {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 12px;
    }
    .wallet-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        background: rgba(15,23,42,0.45);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 12px;
    }
    .wallet-sub-title {
        font-size: 10px;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 2px;
    }
    .wallet-sub-val {
        font-size: 15px;
        font-weight: 800;
        color: #f8fafc;
    }
    .wallet-bar-track {
        background: rgba(255,255,255,0.15);
        border-radius: 6px;
        height: 5px;
        width: 100%;
        overflow: hidden;
        margin-top: 5px;
    }
    .wallet-bar-fill {
        height: 100%;
        border-radius: 6px;
    }

    /* 6. TABS */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        overflow-x: auto !important;
        scrollbar-width: none !important;
        -webkit-overflow-scrolling: touch !important;
        gap: 6px !important;
        padding: 2px 2px 6px 2px !important;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none !important; }
    .stTabs [data-baseweb="tab"] {
        background: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 7px 14px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #475569 !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: #0f172a !important;
        border-color: #0f172a !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(15,23,42,0.18) !important;
    }

    /* 7. BUTTONS */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 8px 12px !important;
        border: 1px solid #e2e8f0 !important;
        font-size: 13px !important;
        transition: transform 0.1s ease !important;
    }
    .stButton > button:active { transform: scale(0.97) !important; }

    /* 8. TRANSACTION CARDS */
    .tx-card {
        background: #ffffff;
        border: 1px solid #f1f5f9;
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .section-title {
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 8px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .form-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .loan-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0284c7;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    /* 9. CATEGORY BAR ROWS (replaces pie chart) */
    .cat-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .cat-icon { font-size: 18px; width: 28px; text-align: center; flex-shrink: 0; }
    .cat-label { font-size: 13px; font-weight: 600; color: #334155; flex: 1; min-width: 0; }
    .cat-bar-wrap { flex: 2; background: #f1f5f9; border-radius: 6px; height: 8px; overflow: hidden; min-width: 60px; }
    .cat-bar-fill { height: 100%; border-radius: 6px; }
    .cat-amount { font-size: 13px; font-weight: 800; color: #0f172a; min-width: 60px; text-align: right; flex-shrink: 0; }

    /* 10. DATE-WISE EXPENSE ACCORDION & ROWS */
    .day-item-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 9px 12px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        width: 100%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }

    /* 11. KILL ALL STREAMLIT WHITESPACE */

    /* A. Tab panel top padding — Streamlit default is 1rem, we kill it */
    [data-baseweb="tab-panel"] {
        padding-top: 0.3rem !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* B. Vertical block gap — tightest safe value */
    [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }

    /* C. Columns gap */
    [data-testid="stColumns"] {
        gap: 0.4rem !important;
    }
    [data-testid="column"] {
        gap: 0 !important;
        padding: 0 !important;
    }

    /* D. Form inputs — no bottom margin */
    [data-testid="stSelectbox"],
    [data-testid="stNumberInput"],
    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    [data-testid="stRadio"],
    [data-testid="stButton"] {
        margin-bottom: 0 !important;
    }

    /* E. Form container — no border/padding/bg */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }

    /* F. Paragraph margins */
    div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }

    /* G. Expander styling */
    [data-testid="stExpander"] {
        margin-bottom: 6px !important;
    }
    [data-testid="stExpander"] details {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        background: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stExpander"] details summary {
        padding: 10px 14px !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        color: #0f172a !important;
        background: #ffffff !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] details div[data-testid="stVerticalBlock"] {
        padding: 6px 12px 10px 12px !important;
    }

    /* H. Radio group bottom margin — tighter */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        margin-bottom: 6px !important;
    }

    /* I. Selectbox collapsed label height */
    [data-testid="stSelectbox"] > label[data-testid="stWidgetLabel"] {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stNumberInput"] > label[data-testid="stWidgetLabel"],
    [data-testid="stTextInput"] > label[data-testid="stWidgetLabel"],
    [data-testid="stTextArea"] > label[data-testid="stWidgetLabel"] {
        font-size: 12px !important;
        font-weight: 600 !important;
        margin-bottom: 2px !important;
        color: #475569 !important;
    }

    /* J. Caption / st.caption spacing */
    [data-testid="stCaptionContainer"] {
        margin-top: 0 !important;
        margin-bottom: 2px !important;
    }

    /* K. Success/info/warning alert padding */
    [data-testid="stAlert"] {
        padding: 8px 12px !important;
        margin: 4px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONFIG & SUPABASE HYBRID ENGINE ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jfplghpfxlbatmaeokmb.supabase.co").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_8NIaGgFZnmM_IkDnl8atYQ_MV9gtsTq").strip()

try:
    if hasattr(st, "secrets"):
        if "SUPABASE_URL" in st.secrets:
            SUPABASE_URL = str(st.secrets["SUPABASE_URL"]).strip().rstrip("/")
        if "SUPABASE_KEY" in st.secrets:
            SUPABASE_KEY = str(st.secrets["SUPABASE_KEY"]).strip()
except Exception:
    pass

DB_NAME = "rajpwa_finance.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            user TEXT,
            category TEXT,
            amount REAL,
            mode TEXT,
            merchant TEXT,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS other_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            sender TEXT,
            category TEXT,
            explanation TEXT,
            raw_text TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_name TEXT UNIQUE,
            total_amount REAL,
            monthly_emi REAL,
            due_day INTEGER,
            remaining_months INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# --- SUPABASE DATA ACCESS LAYER ---
@st.cache_data(ttl=60)
def db_get_expenses():
    """Fetches all expenses from Supabase Cloud REST API with SQLite fallback. Cached 60s for speed."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/expenses?select=*&order=date.desc"
            resp = requests.get(url, headers=get_supabase_headers(), timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                df = pd.DataFrame(data)
                if not df.empty and 'amount' in df:
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
                return df
        except Exception:
            pass
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    return df

def is_duplicate_expense(date_str, user, amount, notes):
    """Checks if an identical or near-simultaneous expense exists in Supabase or SQLite."""
    try:
        req_amount = float(amount)
    except Exception:
        return False

    # 1. Check Cloud Supabase
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/expenses?amount=eq.{req_amount}&order=id.desc&limit=5"
            resp = requests.get(url, headers=get_supabase_headers(), timeout=4)
            if resp.status_code == 200:
                rows = resp.json()
                for row in rows:
                    if str(row.get("user", "")).strip() != str(user).strip():
                        continue
                    # Exact notes match
                    if notes and row.get("notes") and str(row.get("notes")).strip() == str(notes).strip():
                        return True
                    # Within 10 minutes time window
                    row_date = str(row.get("date", ""))
                    try:
                        t1 = datetime.strptime(str(date_str)[:19], "%Y-%m-%d %H:%M:%S")
                        t2 = datetime.strptime(row_date[:19], "%Y-%m-%d %H:%M:%S")
                        if abs((t1 - t2).total_seconds()) < 600:
                            return True
                    except Exception:
                        pass
        except Exception:
            pass

    # 2. Check Local SQLite
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, notes FROM expenses WHERE user = ? AND amount = ? ORDER BY id DESC LIMIT 5", (str(user), req_amount))
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            if notes and row[2] and str(row[2]).strip() == str(notes).strip():
                return True
            try:
                t1 = datetime.strptime(str(date_str)[:19], "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(str(row[1])[:19], "%Y-%m-%d %H:%M:%S")
                if abs((t1 - t2).total_seconds()) < 600:
                    return True
            except Exception:
                pass
    except Exception:
        pass

    return False

def db_insert_expense(date, user, category, amount, mode, merchant, notes):
    """Inserts a new expense to Supabase Cloud and mirrors to local SQLite with deduplication."""
    if is_duplicate_expense(date, user, amount, notes):
        return True

    cloud_saved = False
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/expenses"
            payload = [{
                "date": str(date),
                "user": str(user),
                "category": str(category),
                "amount": float(amount),
                "mode": str(mode),
                "merchant": str(merchant),
                "notes": str(notes)
            }]
            resp = requests.post(url, headers=get_supabase_headers(), json=payload, timeout=5)
            if resp.status_code in (200, 201):
                cloud_saved = True
        except Exception:
            pass
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (date, user, category, amount, mode, merchant, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(date), str(user), str(category), float(amount), str(mode), str(merchant), str(notes))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return cloud_saved

def db_clean_duplicate_expenses():
    """Finds and eliminates duplicate expenses in Supabase and SQLite, retaining exactly one record."""
    deleted_count = 0
    df = db_get_expenses()
    if df.empty or len(df) <= 1:
        return 0

    df_sorted = df.sort_values(by="id", ascending=True).copy()
    seen = []
    ids_to_delete = []

    for _, row in df_sorted.iterrows():
        r_id = row['id']
        r_user = str(row['user']).strip()
        r_amt = float(row['amount'])
        r_date = str(row['date']).strip()
        r_notes = str(row.get('notes', '')).strip()

        is_dup = False
        for s_id, s_user, s_amt, s_date, s_notes in seen:
            if s_user == r_user and abs(s_amt - r_amt) < 0.01:
                # 1. Exact notes match
                if r_notes and s_notes and r_notes == s_notes:
                    is_dup = True
                    break
                # 2. Within 10 minutes time window
                try:
                    t1 = datetime.strptime(r_date[:19], "%Y-%m-%d %H:%M:%S")
                    t2 = datetime.strptime(s_date[:19], "%Y-%m-%d %H:%M:%S")
                    if abs((t1 - t2).total_seconds()) < 600:
                        is_dup = True
                        break
                except Exception:
                    pass

        if is_dup:
            ids_to_delete.append(r_id)
        else:
            seen.append((r_id, r_user, r_amt, r_date, r_notes))

    for dup_id in ids_to_delete:
        db_delete_expense(dup_id)
        deleted_count += 1

    return deleted_count

def db_delete_expense(expense_id):
    """Deletes an expense from Supabase Cloud and local SQLite."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/expenses?id=eq.{expense_id}"
            requests.delete(url, headers=get_supabase_headers(), timeout=5)
        except Exception:
            pass
    try:
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def db_get_loans():
    """Fetches all loans from Supabase Cloud with SQLite fallback."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/loans?select=*&order=id.asc"
            resp = requests.get(url, headers=get_supabase_headers(), timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    for col in ['total_amount', 'monthly_emi', 'due_day', 'remaining_months']:
                        if col in df:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                return df
        except Exception:
            pass
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM loans", conn)
    conn.close()
    return df

def db_save_loan(loan_name, total_amount, monthly_emi, due_day, remaining_months):
    """Saves or updates a loan in Supabase Cloud and local SQLite."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/loans?loan_name=eq.{requests.utils.quote(str(loan_name))}"
            check_resp = requests.get(url, headers=get_supabase_headers(), timeout=5)
            payload = {
                "loan_name": str(loan_name),
                "total_amount": float(total_amount),
                "monthly_emi": float(monthly_emi),
                "due_day": int(due_day),
                "remaining_months": int(remaining_months)
            }
            if check_resp.status_code == 200 and len(check_resp.json()) > 0:
                existing_id = check_resp.json()[0]['id']
                requests.patch(f"{SUPABASE_URL}/rest/v1/loans?id=eq.{existing_id}", headers=get_supabase_headers(), json=payload, timeout=5)
            else:
                requests.post(f"{SUPABASE_URL}/rest/v1/loans", headers=get_supabase_headers(), json=[payload], timeout=5)
        except Exception:
            pass
    try:
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO loans (loan_name, total_amount, monthly_emi, due_day, remaining_months) VALUES (?, ?, ?, ?, ?)",
            (str(loan_name), float(total_amount), float(monthly_emi), int(due_day), int(remaining_months))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def db_delete_loan(loan_id):
    """Deletes a loan from Supabase Cloud and local SQLite."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            requests.delete(f"{SUPABASE_URL}/rest/v1/loans?id=eq.{loan_id}", headers=get_supabase_headers(), timeout=5)
        except Exception:
            pass
    try:
        conn = get_db()
        conn.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def db_get_alerts():
    """Fetches other alerts from Supabase Cloud with SQLite fallback."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL}/rest/v1/other_alerts?select=*&order=id.desc"
            resp = requests.get(url, headers=get_supabase_headers(), timeout=5)
            if resp.status_code == 200:
                return pd.DataFrame(resp.json())
        except Exception:
            pass
    conn = get_db()
    df = pd.read_sql_query("SELECT id, date, category, explanation, raw_text FROM other_alerts ORDER BY id DESC", conn)
    conn.close()
    return df

def db_insert_alert(date, sender, category, explanation, raw_text):
    """Inserts alert into Supabase and SQLite."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            payload = [{
                "date": str(date),
                "sender": str(sender),
                "category": str(category),
                "explanation": str(explanation),
                "raw_text": str(raw_text)
            }]
            requests.post(f"{SUPABASE_URL}/rest/v1/other_alerts", headers=get_supabase_headers(), json=payload, timeout=5)
        except Exception:
            pass
    try:
        conn = get_db()
        conn.execute("INSERT INTO other_alerts (date, sender, category, explanation, raw_text) VALUES (?, ?, ?, ?, ?)",
                     (str(date), str(sender), str(category), str(explanation), str(raw_text)))
        conn.commit()
        conn.close()
    except Exception:
        pass

def db_delete_alert(alert_id):
    """Deletes alert from Supabase and SQLite."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            requests.delete(f"{SUPABASE_URL}/rest/v1/other_alerts?id=eq.{alert_id}", headers=get_supabase_headers(), timeout=5)
        except Exception:
            pass
    try:
        conn = get_db()
        conn.execute("DELETE FROM other_alerts WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def db_insert_batch_expenses(batch_records):
    """Batch inserts records into Supabase and SQLite with deduplication."""
    if not batch_records:
        return
    
    # Filter out duplicates against existing records
    filtered_records = []
    for r in batch_records:
        if not is_duplicate_expense(r[0], r[1], r[3], r[6]):
            filtered_records.append(r)
            
    if not filtered_records:
        return

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            payload = [
                {
                    "date": str(r[0]),
                    "user": str(r[1]),
                    "category": str(r[2]),
                    "amount": float(r[3]),
                    "mode": str(r[4]),
                    "merchant": str(r[5]),
                    "notes": str(r[6])
                }
                for r in filtered_records
            ]
            for i in range(0, len(payload), 100):
                requests.post(f"{SUPABASE_URL}/rest/v1/expenses", headers=get_supabase_headers(), json=payload[i:i+100], timeout=10)
        except Exception:
            pass
    try:
        conn = get_db()
        conn.executemany("INSERT INTO expenses (date, user, category, amount, mode, merchant, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", filtered_records)
        conn.commit()
        conn.close()
    except Exception:
        pass

# --- GEMINI AI & SMART PARSING ENGINE ---
def call_gemini_ai(prompt, api_key):
    """Calls Google Gemini API (100% Free Tier) via direct REST request."""
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code == 200:
            res_json = resp.json()
            raw_content = res_json['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_content)
    except Exception:
        pass
    return None

def parse_sms_with_brain(sms_txt, api_key=""):
    """
    KasuAI Hybrid Brain:
    Uses Google Gemini AI if API key is provided, otherwise falls back to smart regex rules.
    """
    if not sms_txt:
        return None
        
    # 1. Try Gemini AI Brain
    if api_key:
        prompt = f"""
        You are KasuAI, an expert Indian banking SMS decoder.
        Analyze this SMS text:
        \"\"\"{sms_txt}\"\"\"

        Return a JSON object with:
        - "is_expense": true if money is spent/debited/withdrawn, false if credit/OTP/mandate/alert
        - "amount": float (e.g. 250.0)
        - "category": one of ["மளிகை & உணவு", "டீ & சிற்றுண்டி", "வாகனம் & Fuel", "மின்சாரக் கட்டணம்", "கடன்கள் & EMI", "மருத்துவம்", "விவசாயச் செலவு", "இதர செலவுகள்"]
        - "merchant": name of store/payee/service (e.g. "Kannan Stores", "HPCL Petrol", "TANGEDCO", "GPay")
        - "explanation_ta": 1 brief sentence in simple Tamil explaining this transaction or alert.
        """
        ai_res = call_gemini_ai(prompt, api_key)
        if ai_res and "amount" in ai_res:
            return {
                "source": "KasuAI Brain (Gemini AI)",
                "is_expense": ai_res.get("is_expense", True),
                "amount": float(ai_res.get("amount", 0.0)),
                "category": ai_res.get("category", "இதர செலவுகள்"),
                "merchant": ai_res.get("merchant", "SMS"),
                "explanation": ai_res.get("explanation_ta", "")
            }

    # 2. Fast Rule Engine (Instant Fallback)
    txt_low = sms_txt.lower()
    amt = extract_amount_regex(sms_txt)
    is_debit = any(w in txt_low for w in ["debit", "debited", "spent", "paid", "recharge of", "withdrawn"])
    
    if is_debit and amt > 0:
        cat = "இதர செலவுகள்"
        if any(x in txt_low for x in ["petrol", "fuel", "diesel", "iocl", "hpcl", "bpcl", "fastag"]):
            cat = "வாகனம் & Fuel"
        elif any(x in txt_low for x in ["lntfin", "loan", "emi", "bajaj", "muthoot"]):
            cat = "கடன்கள் & EMI"
        elif any(x in txt_low for x in ["tangedco", "electricity"]):
            cat = "மின்சாரக் கட்டணம்"
        elif any(x in txt_low for x in ["tea", "bakery", "snack"]):
            cat = "டீ & சிற்றுண்டி"
        elif any(x in txt_low for x in ["mart", "grocery", "vegetable", "supermarket"]):
            cat = "மளிகை & உணவு"
        elif any(x in txt_low for x in ["med", "pharma", "hospital", "clinic", "doctor"]):
            cat = "மருத்துவம்"
            
        merchant = extract_merchant_regex(sms_txt, default=cat)
        return {
            "source": "KasuAI Rule Engine",
            "is_expense": True,
            "amount": amt,
            "category": cat,
            "merchant": merchant,
            "explanation": f"{cat} - ₹{amt:,.2f} செலவு செய்யப்பட்டது."
        }
    else:
        cat = "இதர அறிவிப்பு"
        explanation = "தகவல் அறிவிப்பு செய்தி (செலவு எதுவும் இல்லை)."
        if "otp" in txt_low or "one-time password" in txt_low:
            cat = "🔐 பாதுகாப்பு & OTP"
            explanation = "உள்நுழைவு அல்லது பணப் பரிவர்த்தனை OTP வந்துள்ளது."
        elif "mandate" in txt_low:
            cat = "🏦 வங்கி & UPI Mandate"
            explanation = "UPI ஆட்டோபே அல்லது வங்கி மேண்டேட் பதிவு செய்தி."
        elif any(x in txt_low for x in ["stcks", "buy now", "target", "stock", "nifty"]):
            cat = "📈 பங்குச் சந்தை டிப்ஸ்"
            explanation = "பங்கு வாங்குவதற்கான பரிந்துரை செய்தி."
            
        return {
            "source": "KasuAI Rule Engine",
            "is_expense": False,
            "amount": 0.0,
            "category": cat,
            "merchant": "SMS",
            "explanation": explanation
        }

def extract_amount_regex(text):
    if not text:
        return 0.0
    # 1. Split out balance suffix so we never accidentally grab available balance
    parts = re.split(r'(?:avl|avail|tot|net|rem)?\.?\s*bal(?:ance)?[:\s]', text, flags=re.IGNORECASE)
    txn_part = parts[0] if parts else text
    
    # 2. Priority: look for amount near debit/spent/paid/withdrawn
    m_action = re.search(r'(?:debited|spent|paid|withdrawn|transferred)\s+(?:by|for|with|of)?\s*(?:rs\.?|inr|\u20b9)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', txn_part, re.IGNORECASE)
    if m_action:
        try:
            val = float(m_action.group(1).replace(',', '').strip())
            if val > 0:
                return val
        except ValueError:
            pass
        
    # 3. Look for currency symbol in txn_part
    m_curr = re.search(r'(?:rs\.?|inr|\u20b9)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', txn_part, re.IGNORECASE)
    if m_curr:
        try:
            val = float(m_curr.group(1).replace(',', '').strip())
            if val > 0:
                return val
        except ValueError:
            pass
            
    return 0.0

def extract_merchant_regex(text, default="இதர"):
    if not text:
        return default
    m = re.search(r"(?:to|at|vpa)\s+([A-Za-z0-9\s&]+?)(?:\s+on|\s+ref|\s+upi|\s+a/c|\.|\n|$)", text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        if 2 < len(name) < 35:
            return name
    return default

# --- TOP APP BAR ---
st.markdown("""
<div class="mobile-app-bar">
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:24px; line-height:1;">🪙</span>
        <div>
            <div class="brand-name">KasuAI</div>
            <div class="brand-tag">Family Finance Tracker • Free</div>
        </div>
    </div>
    <div class="live-badge">
        <span class="live-dot"></span>
        <span>Cloud Live</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- USER SELECTOR ---
active_user = st.radio(
    "User:", 
    ["👤 Rajkumar (Husband)", "👩 Wife (Home Budget)"], 
    horizontal=True,
    label_visibility="collapsed"
)

# --- GEMINI API KEY SETUP IN SIDEBAR ---
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
with st.sidebar:
    st.markdown("### ⚙️ KasuAI Settings")
    
    st.markdown("""
    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:10px 12px; margin-bottom:10px;">
        <div style="font-size:11px; font-weight:700; color:#15803d;">☁️ CLOUD DATABASE</div>
        <div style="font-size:13px; font-weight:800; color:#0f172a; margin-top:2px;">Supabase PostgreSQL</div>
        <div style="font-size:11px; color:#16a34a; font-weight:600; margin-top:3px;">🟢 Real-Time Sync Active</div>
    </div>
    """, unsafe_allow_html=True)
    
    user_key = st.text_input("🔑 Gemini API Key (Free):", value=gemini_api_key, type="password", placeholder="AIzaSy...")
    if user_key:
        gemini_api_key = user_key
        st.success("🤖 AI Brain ready!")
    else:
        st.caption("Add a free Gemini API key for smart SMS parsing & financial tips.")

# --- CLEAN TABS WITH BOLD LABELS ---
tab_dash, tab_entry, tab_loans, tab_history, tab_upload, tab_alerts = st.tabs([
    "📊 மேலோட்டம்", 
    "➕ புதிய செலவு", 
    "🏦 கடன்கள் & EMI",
    "📜 வரலாறு",
    "📁 பதிவேற்றம்",
    "🔔 எச்சரிக்கைகள்"
])

# ==================== 1. DASHBOARD ====================
with tab_dash:
    all_df = db_get_expenses()
    
    current_m = datetime.now().strftime("%Y-%m")
    available_months = ["This Month (Current)"]
    if not all_df.empty:
        all_df['month_year'] = pd.to_datetime(all_df['date'], errors='coerce').dt.strftime('%Y-%m')
        unique_months = sorted([m for m in all_df['month_year'].dropna().unique() if str(m).startswith('202')], reverse=True)
        unique_months = [m for m in unique_months if m != current_m]
        available_months += unique_months
        
    m_col1, m_col2, m_col3 = st.columns([1.7, 1.0, 0.4])
    with m_col1:
        selected_view = st.selectbox("Month:", available_months, label_visibility="collapsed")
    with m_col2:
        st.markdown(f"<div style='text-align:right; font-size:11px; font-weight:700; color:#64748b; padding-top:6px;'>📅 {datetime.now().strftime('%d-%b')}</div>", unsafe_allow_html=True)
    with m_col3:
        if st.button("🔄", key="top_reload_btn", help="Refresh data"):
            st.cache_data.clear()
            st.rerun()
    
    target_month = current_m if selected_view == "This Month (Current)" else selected_view
    df = all_df[all_df['month_year'] == target_month] if not all_df.empty and 'month_year' in all_df else pd.DataFrame()
    
    total_spent = df['amount'].sum() if not df.empty else 0.0
    wife_spent = df[df['user'].str.contains('Wife|மனைவி', na=False)]['amount'].sum() if not df.empty else 0.0
    wife_remaining = max(0.0, 40000.0 - wife_spent)
    wife_pct = min(100.0, (wife_spent / 40000.0) * 100.0) if 40000.0 > 0 else 0.0
    savings_est = max(0.0, 65000.0 - total_spent)
    fill_color = "#38bdf8" if wife_pct < 85 else "#f97316" if wife_pct < 100 else "#ef4444"
    
    # WALLET CARD
    st.markdown(f"""
    <div class="wallet-card">
        <div class="wallet-header">
            <span class="wallet-label">💳 Total Family Spending</span>
            <span class="wallet-month-tag">{target_month}</span>
        </div>
        <div class="wallet-amount">₹{total_spent:,.0f}</div>
        <div class="wallet-grid">
            <div>
                <div class="wallet-sub-title">👩 Wife Budget (₹40,000)</div>
                <div class="wallet-sub-val">₹{wife_spent:,.0f}</div>
                <div class="wallet-bar-track">
                    <div class="wallet-bar-fill" style="width: {wife_pct:.1f}%; background: {fill_color};"></div>
                </div>
                <div style="font-size:10px; color:#cbd5e1; margin-top:4px;">Left: ₹{wife_remaining:,.0f} ({100-wife_pct:.0f}% free)</div>
            </div>
            <div>
                <div class="wallet-sub-title">💰 Savings Target (₹65K)</div>
                <div class="wallet-sub-val" style="color:#4ade80;">₹{savings_est:,.0f}</div>
                <div style="font-size:10px; color:#cbd5e1; margin-top:12px;">{len(df)} transactions</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    # AI ADVISOR BUTTON
    if st.button("🤖 KasuAI — Get Smart Financial Tips", use_container_width=True):
        summary_str = f"Target Month: {target_month}, Total Spent: ₹{total_spent}, Wife Spent: ₹{wife_spent}/₹40000, Projected Savings: ₹{savings_est}."
        if not df.empty:
            cat_breakdown = df.groupby("category")["amount"].sum().to_dict()
            summary_str += f" Category Breakdown: {cat_breakdown}"
            
        advice_prompt = f"""
        You are KasuAI, a warm, wise, encouraging family financial advisor speaking to Rajkumar and his wife in Tamil.
        Financial data for this month:
        {summary_str}
        Provide 3 clear, practical, motivating bullet points in simple, friendly Tamil on:
        1. Where they are saving well.
        2. Where to be cautious.
        3. A motivating quote/tip to achieve the ₹65,000 savings target.
        Return in clear markdown.
        """
        with st.spinner("🧠 Analyzing your finances..."):
            ai_advice = None
            if gemini_api_key:
                ai_advice_obj = call_gemini_ai(advice_prompt, gemini_api_key)
                if ai_advice_obj:
                    ai_advice = json.dumps(ai_advice_obj, ensure_ascii=False)
            if not ai_advice:
                ai_advice = f"""
**KasuAI Financial Report — {target_month}**

✅ **Savings on track:** Total spent ₹{total_spent:,.0f}. Potential savings towards ₹65K goal: **₹{savings_est:,.0f}**

👩 **Wife Budget:** ₹{wife_spent:,.0f} used of ₹40,000 ({wife_pct:.0f}%). Balance remaining: **₹{wife_remaining:,.0f}**

💡 **Tip:** Track even small daily expenses — they add up to big savings at month-end!
                """
            st.info(ai_advice)
            
    
    if not df.empty:
        summary = df.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
        max_amt = summary["amount"].max() if len(summary) > 0 else 1

        # Category icons map
        CAT_ICONS = {
            "மளிகை & உணவு": "🛒", "மளிகை": "🛒",
            "டீ & சிற்றுண்டி": "☕", "Tea": "☕",
            "வாகனம் & Fuel": "⛽", "Fuel": "⛽",
            "மின்சாரக் கட்டணம்": "⚡", "Electricity": "⚡",
            "கடன்கள் & EMI": "🏦", "EMI": "🏦",
            "மருத்துவம்": "🏥", "Medical": "🏥",
            "விவசாயச் செலவு": "🌾", "Farm": "🌾",
            "இதர செலவுகள்": "📦", "Other": "📦",
            "வங்கி அறிக்கை": "🏛️",
        }
        BAR_COLORS = ["#0284c7", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#64748b", "#db2777"]

        st.markdown('<div class="section-title">📊 Spending by Category</div>', unsafe_allow_html=True)
        cat_html = '<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:12px 16px; margin-bottom:12px;">'
        for idx, row in summary.iterrows():
            cat = str(row["category"])
            amt = float(row["amount"])
            pct = (amt / max_amt) * 100 if max_amt > 0 else 0
            icon = CAT_ICONS.get(cat, "📌")
            color = BAR_COLORS[list(summary.index).index(idx) % len(BAR_COLORS)]
            # Short English label for category
            short_label = (
                cat.replace("மளிகை & உணவு", "Grocery & Food")
                   .replace("டீ & சிற்றுண்டி", "Tea & Snacks")
                   .replace("வாகனம் & Fuel", "Vehicle & Fuel")
                   .replace("மின்சாரக் கட்டணம்", "Electricity")
                   .replace("கடன்கள் & EMI", "Loans & EMI")
                   .replace("மருத்துவம்", "Medical")
                   .replace("விவசாயச் செலவு", "Farm Expense")
                   .replace("இதர செலவுகள்", "Others")
                   .replace("வங்கி அறிக்கை", "Bank Statement")
            )
            cat_html += f"""
            <div class="cat-row">
                <div class="cat-icon">{icon}</div>
                <div class="cat-label">{short_label}</div>
                <div class="cat-bar-wrap"><div class="cat-bar-fill" style="width:{pct:.1f}%; background:{color};"></div></div>
                <div class="cat-amount">₹{amt:,.0f}</div>
            </div>"""
        cat_html += "</div>"
        st.markdown(cat_html, unsafe_allow_html=True)
            
        r_head_col1, r_head_col2 = st.columns([3.0, 2.2])
        with r_head_col1:
            st.markdown('<div class="section-title">📅 Daily Expenses</div>', unsafe_allow_html=True)
        with r_head_col2:
            if st.button("🧹 Remove Duplicates", key="clean_dup_dash", help="Remove duplicate entries recorded multiple times", use_container_width=True):
                del_count = db_clean_duplicate_expenses()
                st.cache_data.clear()
                if del_count > 0:
                    st.success(f"✅ {del_count} duplicates removed!")
                else:
                    st.info("✅ No duplicates found!")
                st.rerun()

        recent_df = df.copy()
        if not recent_df.empty:
            recent_df['dt'] = pd.to_datetime(recent_df['date'], errors='coerce')
            recent_df['date_only'] = recent_df['dt'].dt.strftime('%Y-%m-%d')
            today_str = datetime.now().strftime('%Y-%m-%d')
            yesterday_str = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            
            unique_dates = sorted(recent_df['date_only'].dropna().unique(), reverse=True)
            
            for idx, d_str in enumerate(unique_dates):
                day_df = recent_df[recent_df['date_only'] == d_str].sort_values(by="id", ascending=False)
                day_total = day_df['amount'].sum()
                day_count = len(day_df)
                
                try:
                    d_obj = datetime.strptime(d_str, "%Y-%m-%d")
                    date_formatted = d_obj.strftime("%d %b %Y (%a)")
                    day_short = d_obj.strftime("%d %b")
                except:
                    date_formatted = d_str
                    day_short = d_str
                
                count_lbl = f"{day_count} {'entry' if day_count == 1 else 'entries'}"
                if d_str == today_str:
                    header_label = f"📅 Today ({day_short})   •   ₹{day_total:,.0f}   ({count_lbl})"
                elif d_str == yesterday_str:
                    header_label = f"📅 Yesterday ({day_short})   •   ₹{day_total:,.0f}   ({count_lbl})"
                else:
                    header_label = f"📅 {date_formatted}   •   ₹{day_total:,.0f}   ({count_lbl})"
                
                with st.expander(header_label, expanded=(idx == 0)):
                    for _, r in day_df.iterrows():
                        merchant_raw = str(r['merchant']) if pd.notna(r['merchant']) else ""
                        notes_raw = str(r['notes']) if pd.notna(r['notes']) else ""
                        merchant_disp = merchant_raw if merchant_raw and merchant_raw != str(r['category']) else ""
                        notes_disp = notes_raw[:30] if notes_raw and notes_raw != merchant_raw else ""
                        
                        cat_name = str(r['category'])
                        cat_icon = CAT_ICONS.get(cat_name, "📌")
                        cat_display = (
                            cat_name
                            .replace("மளிகை & உணவு", "Grocery")
                            .replace("டீ & சிற்றுண்டி", "Tea/Snacks")
                            .replace("வாகனம் & Fuel", "Fuel")
                            .replace("மின்சாரக் கட்டணம்", "Electricity")
                            .replace("கடன்கள் & EMI", "Loan/EMI")
                            .replace("மருத்துவம்", "Medical")
                            .replace("விவசாயச் செலவு", "Farm")
                            .replace("இதர செலவுகள்", "Others")
                        )
                        user_short = "Raj" if "Raj" in str(r['user']) or "ராஜ்" in str(r['user']) else "Wife"
                        time_disp = str(r['date'])[11:16] if pd.notna(r['date']) and len(str(r['date'])) >= 16 else ""
                        time_str = f"{time_disp} · " if time_disp else ""
                        
                        t_col1, t_col2 = st.columns([4.4, 1.0])
                        with t_col1:
                            st.markdown(f"""
                            <div class="day-item-card">
                                <div style="font-size:18px; margin-right:8px; line-height:1;">{cat_icon}</div>
                                <div style="flex:1; min-width:0;">
                                    <div style="font-weight:700; font-size:13.5px; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{merchant_disp or cat_display}</div>
                                    <div style="font-size:11.5px; color:#64748b; margin-top:1px;">{cat_display} · {time_str}{user_short}</div>
                                </div>
                                <div style="font-size:15px; font-weight:800; color:#dc2626; white-space:nowrap; margin-left:8px;">
                                    ₹{r['amount']:,.0f}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with t_col2:
                            if st.button("🗑️", key=f"del_exp_{r['id']}", help="Delete this entry"):
                                db_delete_expense(r['id'])
                                st.cache_data.clear()
                                st.success("Deleted!")
                                st.rerun()
    else:
        st.markdown("""
        <div style="background:#ffffff; border:2px dashed #cbd5e1; border-radius:16px; padding:20px 16px; text-align:center; color:#64748b; margin-top:6px;">
            <div style="font-size:32px; margin-bottom:8px;">📝</div>
            <div style="font-size:15px; font-weight:700; color:#0f172a;">No expenses recorded this month</div>
            <div style="font-size:13px; margin-top:4px;">Tap the ➕ Add Expense tab to log your first entry.</div>
        </div>
        """, unsafe_allow_html=True)


# ==================== 2. ADD EXPENSE & SMS DECODER ====================
with tab_entry:
    st.markdown('<div class="section-title">⚡ Quick Add (1-Tap Presets)</div>', unsafe_allow_html=True)
    
    def add_quick_expense(cat, amt, note):
        db_insert_expense(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            active_user,
            cat,
            amt,
            "Cash",
            note,
            note
        )
        st.cache_data.clear()
        st.success(f"✅ {note} ₹{amt} added!")
        st.rerun()

    q_r1_c1, q_r1_c2, q_r1_c3 = st.columns(3)
    if q_r1_c1.button("☕ Tea ₹20", use_container_width=True):
        add_quick_expense("டீ & சிற்றுண்டி", 20.0, "Tea/Coffee")
    if q_r1_c2.button("🥛 Milk ₹35", use_container_width=True):
        add_quick_expense("மளிகை & உணவு", 35.0, "Milk")
    if q_r1_c3.button("🥦 Veggies ₹150", use_container_width=True):
        add_quick_expense("மளிகை & உணவு", 150.0, "Vegetables")
        
    q_r2_c1, q_r2_c2 = st.columns(2)
    if q_r2_c1.button("⛽ Petrol ₹200", use_container_width=True):
        add_quick_expense("வாகனம் & Fuel", 200.0, "Petrol")
    if q_r2_c2.button("🛒 Grocery ₹500", use_container_width=True):
        add_quick_expense("மளிகை & உணவு", 500.0, "Grocery Store")
        

    with st.expander("⚡ Paytm September Missing Expenses (1-Click Sync)", expanded=False):
        st.caption("Missing September Paytm payments not captured by SMS:")
        st.markdown("""
        * 🏨 **Hotel Annalakshmi Catering Services**: ₹345 *(Food)*
        * 🍞 **Krishna Bakery**: ₹170 *(Tea & Snacks)*
        * ⛽ **Nishanth Enterprises**: ₹800 *(Fuel)*
        * 🛒 **Maheshwari Maligai**: ₹70 *(Grocery)*
        """)
        if st.button("➕ Add All 4 Missing Paytm Expenses (Total: ₹1,385)", key="add_missing_paytm", use_container_width=True):
            missing_paytm_items = [
                ("2026-09-19 19:05:00", "👤 Rajkumar (Husband)", "மளிகை & உணவு", 345.0, "Paytm UPI", "Hotel Annalakshmi Catering Services", "Paytm: Paid ₹345 to Hotel Annalakshmi Catering Services"),
                ("2026-09-18 15:38:00", "👤 Rajkumar (Husband)", "டீ & சிற்றுண்டி", 170.0, "Paytm UPI", "Krishna Bakery", "Paytm: Paid ₹170 to Krishna Bakery"),
                ("2026-09-18 11:22:00", "👤 Rajkumar (Husband)", "வாகனம் & Fuel", 800.0, "Paytm UPI", "Nishanth Enterprises", "Paytm: Paid ₹800 to Nishanth Enterprises"),
                ("2026-09-17 10:15:00", "👤 Rajkumar (Husband)", "மளிகை & உணவு", 70.0, "Paytm UPI", "Maheshwari Maligai", "Paytm: Paid ₹70 to Maheshwari Maligai")
            ]
            added_count = 0
            for itm in missing_paytm_items:
                if db_insert_expense(itm[0], itm[1], itm[2], itm[3], itm[4], itm[5], itm[6]):
                    added_count += 1
            st.cache_data.clear()
            st.success(f"✅ {added_count} missing Paytm expenses added!")
            st.rerun()

    
    st.markdown("""
    <div class="form-box">
        <div style="font-size:15px; font-weight:800; color:#0f172a; margin-bottom:10px;">
            🧠 1. SMS Decoder — Paste Bank Message
        </div>
    """, unsafe_allow_html=True)
    
    sms_txt = st.text_area(
        "SMS Text:", 
        placeholder="Paste bank SMS, UPI debit, or payment notification here...", 
        height=100,
        label_visibility="collapsed"
    )
    
    if st.button("🚀 Decode SMS & Add Expense", type="primary", use_container_width=True):
        if sms_txt.strip():
            with st.spinner("🧠 KasuAI analyzing SMS..."):
                result = parse_sms_with_brain(sms_txt, gemini_api_key)
                
            if result and result["is_expense"] and result["amount"] > 0:
                db_insert_expense(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    active_user,
                    result["category"],
                    result["amount"],
                    "SMS / UPI",
                    result["merchant"],
                    sms_txt
                )
                st.cache_data.clear()
                st.success(f"💳 ₹{result['amount']:,.0f} expense added — {result['merchant']} [{result['source']}]")
                st.rerun()
            else:
                cat = result["category"] if result else "Info Alert"
                explanation = result["explanation"] if result else "Information message"
                db_insert_alert(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "SMS",
                    cat,
                    explanation,
                    sms_txt
                )
                st.info(f"🔔 **{cat}:** {explanation}")
                st.rerun()
        else:
            st.warning("Please paste an SMS message first!")
    st.markdown("</div>", unsafe_allow_html=True)


    st.markdown("""
    <div class="form-box">
        <div style="font-size:15px; font-weight:800; color:#0f172a; margin-bottom:10px;">
            ✍️ 2. Manual Entry (Cash / Any Expense)
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("manual_entry_form"):
        man_amt = st.number_input("Amount (₹):", min_value=1.0, value=50.0, step=10.0)
        man_cat = st.selectbox("Category:", ["மளிகை & உணவு", "டீ & சிற்றுண்டி", "வாகனம் & Fuel", "மின்சாரக் கட்டணம்", "கடன்கள் & EMI", "விவசாயச் செலவு", "மருத்துவம்", "இதர செலவுகள்"])
        man_mode = st.selectbox("Payment Mode:", ["Cash", "PhonePe / GPay", "Bank Transfer", "Paytm UPI"])
        man_notes = st.text_input("Note (e.g: Vegetables, Tea, Grocery):", "")
        
        if st.form_submit_button("➕ Save Expense", type="primary", use_container_width=True):
            db_insert_expense(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                active_user,
                man_cat,
                man_amt,
                man_mode,
                man_notes or "Manual Entry",
                man_notes
            )
            st.cache_data.clear()
            st.success(f"✅ ₹{man_amt:,.0f} ({man_cat}) saved!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ==================== 3. LOANS & EMI ====================
with tab_loans:
    st.markdown('<div class="section-title">🏦 கடன் & தவணைகள் (Loans & EMI Tracker)</div>', unsafe_allow_html=True)
    l_df = db_get_loans()
    
    col_l1, col_l2 = st.columns([1, 1])
    
    with col_l1:
        st.markdown("""
        <div class="form-box">
            <div style="font-size:16px; font-weight:800; color:#0f172a; margin-bottom:12px;">
                ➕ புதிய கடன் விவரம் சேர்க்க
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("add_loan_form"):
            l_name = st.text_input("கடன் பெயர் (எ.கா: L&T Loan, SBI நகைக்கடன், Jupiter EMI):")
            l_total = st.number_input("மொத்த அசல் / இருப்புத் தொகை (₹):", min_value=0.0, value=50000.0, step=5000.0)
            l_emi = st.number_input("மாதாந்திர தவணை / EMI (₹):", min_value=0.0, value=2500.0, step=500.0)
            l_day = st.number_input("மாத தவணை தேதி (1 முதல் 31):", min_value=1, max_value=31, value=5)
            l_months = st.number_input("மீதமுள்ள மாதங்கள்:", min_value=1, value=12)
            
            if st.form_submit_button("💾 கடனைப் பதிவு செய்", type="primary", use_container_width=True):
                if l_name.strip():
                    db_save_loan(l_name.strip(), l_total, l_emi, l_day, l_months)
                    st.success(f"✅ '{l_name}' சேர்க்கப்பட்டது!")
                    st.rerun()
                else:
                    st.error("கடன் பெயரை உள்ளிடவும்!")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_l2:
        st.markdown('<div style="font-size:16px; font-weight:800; color:#0f172a; margin-bottom:12px;">📋 தற்போதைய கடன்கள் பட்டியல்</div>', unsafe_allow_html=True)
        if not l_df.empty:
            total_emi = l_df['monthly_emi'].sum()
            total_debt = l_df['total_amount'].sum()
            
            st.markdown(f"""
            <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px; padding:12px 16px; margin-bottom:14px; display:flex; justify-content:space-between;">
                <div>மாத மொத்த EMI: <b style="color:#0284c7; font-size:16px;">₹{total_emi:,.2f}</b></div>
                <div>மொத்த அசல் இருப்பு: <b style="color:#0f172a; font-size:16px;">₹{total_debt:,.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
            for _, l_row in l_df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="loan-card">
                        <div style="font-size:16px; font-weight:800; color:#0f172a;">🏦 {l_row['loan_name']}</div>
                        <div style="margin-top:6px; font-size:14px; color:#334155;">
                            • மாதாந்திர EMI: <b style="color:#dc2626;">₹{l_row['monthly_emi']:,.2f}</b> (தவணை தேதி: <b>{l_row['due_day']}</b>)<br>
                            • அசல் இருப்பு: <b>₹{l_row['total_amount']:,.2f}</b> | மீதம்: <b>{l_row['remaining_months']} மாதங்கள்</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ இந்தக் கடனை நீக்கு", key=f"del_loan_{l_row['id']}"):
                        db_delete_loan(l_row['id'])
                        st.success("கடன் நீக்கப்பட்டது!")
                        st.rerun()
        else:
            st.markdown("""
            <div style="background:#ffffff; border:2px dashed #cbd5e1; border-radius:14px; padding:18px 16px; text-align:center; color:#64748b;">
                தற்போது கடன்கள் எதுவும் பதிவு செய்யப்படவில்லை.<br>புதிய கடனைச் சேர்க்க இடதுபுறப் படிவத்தைப் பயன்படுத்தவும்.
            </div>
            """, unsafe_allow_html=True)

# ==================== 4. HISTORY & TRENDS ====================
with tab_history:
    st.markdown('<div class="section-title">📜 கடந்த கால வரலாற்று வரைபடங்கள் & அறிக்கைகள்</div>', unsafe_allow_html=True)
    h_df = db_get_expenses()
    
    if not h_df.empty:
        h_df['month_year'] = pd.to_datetime(h_df['date'], errors='coerce').dt.strftime('%Y-%m')
        valid_history = h_df[h_df['month_year'].str.startswith('202', na=False)]
        
        if not valid_history.empty:
            monthly_trend = valid_history.groupby("month_year")["amount"].sum().reset_index()
            monthly_trend = monthly_trend.sort_values(by="month_year")
            
            bar_fig = px.bar(
                monthly_trend, x="month_year", y="amount",
                labels={"month_year": "மாதம் / வருடம்", "amount": "மொத்த செலவு (₹)"},
                color="amount", color_continuous_scale="Blues", text_auto=".2s"
            )
            bar_fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(bar_fig, use_container_width=True)
            
            st.markdown('<div class="section-title">📑 அனைத்து பரிவர்த்தனைகளின் பட்டியல்</div>', unsafe_allow_html=True)
            table_disp = valid_history[['date', 'user', 'category', 'amount', 'merchant', 'notes']].copy()
            table_disp['amount'] = table_disp['amount'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(table_disp.rename(columns={
                'date': 'தேதி & நேரம்', 'user': 'பயனர்', 'category': 'பிரிவு', 'amount': 'தொகை', 'merchant': 'சேவை/கடை', 'notes': 'முழு உரை'
            }), use_container_width=True, height=380, hide_index=True)
        else:
            st.info("வரலாற்றுத் தரவுகளுக்கான செல்லுபடியாகும் தேதிகள் கண்டறியப்படவில்லை.")
    else:
        st.info("டேட்டாபேஸில் இன்னும் பரிவர்த்தனைகள் எதுவும் இல்லை.")

# ==================== 5. UPLOAD OLD STATEMENTS ====================
with tab_upload:
    st.markdown('<div class="section-title">📁 பழைய SMS & வங்கி அறிக்கைகள் பதிவேற்றம்</div>', unsafe_allow_html=True)
    st.caption("Android SMS Backup & Restore (XML), JSON கோப்புகள் அல்லது SBI / வங்கி அறிக்கைகளை (CSV) இங்கே பதிவேற்றலாம்.")
    
    sms_file = st.file_uploader("📥 கோப்பைத் தேர்வு செய்யவும் (XML, JSON, CSV):", type=["xml", "json", "csv"], key="sms_upload")
    if sms_file is not None:
        if st.button("🚀 கோப்பைப் படித்து ஏற்றவும்", type="primary"):
            try:
                batch_records = []
                
                # 1. XML
                if sms_file.name.lower().endswith(".xml"):
                    tree = ET.parse(sms_file)
                    root = tree.getroot()
                    for sms in root.findall(".//sms"):
                        try:
                            body = sms.get("body", "")
                            if not body:
                                continue
                            date_ms = int(sms.get("date", "0"))
                            date_str = pd.to_datetime(date_ms, unit="ms").strftime("%Y-%m-%d %H:%M:%S")
                            address = sms.get("address", "SMS")
                            amt = extract_amount_regex(body)
                            txt_low = body.lower()
                            is_debit = any(w in txt_low for w in ["debit", "debited", "spent", "paid", "recharge of", "withdrawn"])
                            if is_debit and amt > 0:
                                cat = "இதர செலவுகள்"
                                if any(x in txt_low for x in ["petrol", "fuel", "diesel", "iocl", "hpcl", "bpcl", "fastag"]):
                                    cat = "வாகனம் & Fuel"
                                elif any(x in txt_low for x in ["lntfin", "loan", "emi"]):
                                    cat = "கடன்கள் & EMI"
                                elif any(x in txt_low for x in ["tangedco", "electricity"]):
                                    cat = "மின்சாரக் கட்டணம்"
                                elif any(x in txt_low for x in ["tea", "bakery", "snack"]):
                                    cat = "டீ & சிற்றுண்டி"
                                elif any(x in txt_low for x in ["mart", "grocery", "vegetable"]):
                                    cat = "மளிகை & உணவு"
                                batch_records.append((date_str, active_user, cat, amt, "Old SMS", address, body))
                        except Exception:
                            continue
                            
                # 2. JSON
                elif sms_file.name.lower().endswith(".json"):
                    data = json.load(sms_file)
                    items = data if isinstance(data, list) else data.get("messages", data.get("sms", []))
                    for item in items:
                        body = item.get("body") or item.get("text") or item.get("message") or ""
                        if not body:
                            continue
                        dt = item.get("date") or item.get("date_str") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        amt = extract_amount_regex(body)
                        txt_low = body.lower()
                        is_debit = any(w in txt_low for w in ["debit", "debited", "spent", "paid", "recharge of", "withdrawn"])
                        if is_debit and amt > 0:
                            cat = "இதர செலவுகள்"
                            if any(x in txt_low for x in ["petrol", "fuel", "diesel", "iocl", "hpcl", "bpcl"]):
                                cat = "வாகனம் & Fuel"
                            elif any(x in txt_low for x in ["lntfin", "loan", "emi"]):
                                cat = "கடன்கள் & EMI"
                            elif any(x in txt_low for x in ["tangedco", "electricity"]):
                                cat = "மின்சாரக் கட்டணம்"
                            elif any(x in txt_low for x in ["tea", "bakery", "snack"]):
                                cat = "டீ & சிற்றுண்டி"
                            elif any(x in txt_low for x in ["mart", "grocery"]):
                                cat = "மளிகை & உணவு"
                            batch_records.append((str(dt), active_user, cat, amt, "JSON SMS", item.get("address", "SMS"), body))
                            
                # 3. CSV
                elif sms_file.name.lower().endswith(".csv"):
                    csv_df = pd.read_csv(sms_file)
                    col_map = {col.lower().strip(): col for col in csv_df.columns}
                    date_col = next((col_map[c] for c in col_map if any(k in c for k in ["date", "txn date", "time"])), None)
                    desc_col = next((col_map[c] for c in col_map if any(k in c for k in ["desc", "narration", "particulars", "body", "message"])), None)
                    amt_col = next((col_map[c] for c in col_map if any(k in c for k in ["debit", "withdrawal", "amount"])), None)
                    
                    if desc_col:
                        for _, row in csv_df.iterrows():
                            body = str(row[desc_col])
                            dt = str(row[date_col]) if date_col and pd.notna(row[date_col]) else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            amt = 0.0
                            if amt_col and pd.notna(row[amt_col]):
                                try:
                                    amt = float(str(row[amt_col]).replace(",", "").strip())
                                except ValueError:
                                    amt = extract_amount_regex(body)
                            else:
                                amt = extract_amount_regex(body)
                            
                            if amt > 0:
                                cat = "வங்கி அறிக்கை"
                                txt_low = body.lower()
                                if any(x in txt_low for x in ["petrol", "fuel", "diesel", "iocl", "hpcl", "bpcl"]):
                                    cat = "வாகனம் & Fuel"
                                elif any(x in txt_low for x in ["lntfin", "loan", "emi"]):
                                    cat = "கடன்கள் & EMI"
                                elif any(x in txt_low for x in ["tangedco", "electricity"]):
                                    cat = "மின்சாரக் கட்டணம்"
                                elif any(x in txt_low for x in ["mart", "grocery"]):
                                    cat = "மளிகை & உணவு"
                                batch_records.append((dt, active_user, cat, amt, "Statement CSV", "Bank", body))
                
                if batch_records:
                    db_insert_batch_expenses(batch_records)
                    st.success(f"🎉 {len(batch_records)} செலவுகள் வெற்றிகரமாக சேர்க்கப்பட்டன!")
                else:
                    st.warning("கோப்பில் செலவுப் பதிவுகள் எதுவும் கண்டறியப்படவில்லை.")
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")

    st.markdown('<div class="section-title">📱 Paytm / UPI / SMS உரை மொத்தப் பதிவு</div>', unsafe_allow_html=True)
    st.caption("Paytm அல்லது UPI வரலாற்றை காப்பி செய்து இங்கே பேஸ்ட் செய்தால் தானாகப் பிரித்தெடுத்துப் பதிவு செய்யும்.")
    bulk_txt = st.text_area(
        "Paytm / SMS உரைகள் (வரிக்கு ஒன்றாக அல்லது பாராவாக):",
        placeholder="Paid ₹345 to Hotel Annalakshmi\nPaid ₹170 to Krishna Bakery\nPaid ₹800 to Nishanth Enterprises...",
        height=120,
        key="bulk_paytm_txt"
    )
    if st.button("🚀 மொத்தமாகப் பகுப்பாய்வு செய்து பதிவு செய்", key="btn_bulk_parse", use_container_width=True):
        if bulk_txt.strip():
            lines = [line.strip() for line in bulk_txt.strip().split("\n") if line.strip()]
            records = []
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for line in lines:
                amt = extract_amount_regex(line)
                if amt > 0:
                    merchant = "UPI / Paytm"
                    m_match = re.search(r'(?i)(?:to|at)\s+([A-Za-z0-9\s&.\'-]+?)(?:\s+successful|\s+from|\s+upi|\.|\n|$)', line)
                    if m_match:
                        cand = m_match.group(1).strip()
                        if len(cand) >= 3:
                            merchant = cand
                    cat = "இதர செலவுகள்"
                    line_low = line.lower()
                    if any(w in line_low for w in ["hotel", "restaurant", "catering", "cater", "bhavan", "mess", "maligai", "mart", "grocery", "milk", "vegetable"]):
                        cat = "மளிகை & உணவு"
                    elif any(w in line_low for w in ["tea", "coffee", "bakery", "snack", "sweets", "juice"]):
                        cat = "டீ & சிற்றுண்டி"
                    elif any(w in line_low for w in ["petrol", "fuel", "diesel", "iocl", "hpcl", "bpcl", "fastag", "traders"]):
                        cat = "வாகனம் & Fuel"
                    elif any(w in line_low for w in ["medical", "pharmacy", "clinic", "hospital"]):
                        cat = "மருத்துவம்"
                    elif any(w in line_low for w in ["loan", "emi"]):
                        cat = "கடன்கள் & EMI"
                    elif any(w in line_low for w in ["eb bill", "electricity"]):
                        cat = "மின்சாரக் கட்டணம்"
                    records.append((now_str, active_user, cat, amt, "Paytm / UPI Bulk", merchant, line))
            if records:
                db_insert_batch_expenses(records)
                st.success(f"🎉 {len(records)} செலவுகள் வெற்றிகரமாக சேர்க்கப்பட்டன!")
                st.rerun()
            else:
                st.warning("உரையில் செலவுத் தொகைகள் எதுவும் கண்டறியப்படவில்லை.")

# ==================== 6. OTHER ALERTS ====================
with tab_alerts:
    st.markdown('<div class="section-title">🔔 இதர எச்சரிக்கைகள் & தமிழ் விளக்கம்</div>', unsafe_allow_html=True)
    alerts_df = db_get_alerts()
    if not alerts_df.empty:
        for idx, row in alerts_df.iterrows():
            with st.expander(f"{row['category']} — {row['date']}"):
                st.write(f"💡 **விளக்கம்:** {row['explanation']}")
                st.code(row['raw_text'], language="text")
                if st.button("🗑️ நீக்கு", key=f"del_alert_{row['id']}"):
                    db_delete_alert(row['id'])
                    st.success("எச்சரிக்கை நீக்கப்பட்டது!")
                    st.rerun()
    else:
        st.markdown("""
        <div style="background:#ffffff; border:2px dashed #cbd5e1; border-radius:14px; padding:18px 16px; text-align:center; color:#64748b;">
            இதர எச்சரிக்கைகள் (OTP, Mandate, Stock tips) எதுவும் இல்லை.
        </div>
        """, unsafe_allow_html=True)
