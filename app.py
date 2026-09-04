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
    page_title="KasuAI — குடும்ப நிதி & AI மேலாண்மை",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SIMPLE, BOLD & CLEAR MODERN CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
    
    .block-container {
        max-width: 1040px !important;
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    
    body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0f172a;
    }
    
    /* Top App Header Banner */
    .hero-banner {
        background: #0f172a;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 24px 28px;
        color: white;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .hero-subtitle {
        font-size: 14px;
        color: #bae6fd;
        margin-top: 4px;
        font-weight: 500;
    }
    
    /* Metric Cards: Bold, High Contrast & Clean */
    .stat-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 18px;
        border: 2px solid #f1f5f9;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        text-align: left;
        transition: all 0.2s ease-in-out;
    }
    .stat-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
    }
    .stat-label {
        font-size: 13px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stat-number {
        font-size: 28px;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 8px;
        letter-spacing: -0.8px;
    }
    .stat-sub {
        font-size: 13px;
        font-weight: 600;
        color: #475569;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Color Highlights */
    .c-expense { color: #dc2626 !important; }
    .c-budget { color: #0284c7 !important; }
    .c-savings { color: #059669 !important; }
    
    /* Progress Bar */
    .progress-track {
        background: #e2e8f0;
        border-radius: 8px;
        height: 8px;
        width: 100%;
        overflow: hidden;
        margin-top: 6px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }
    
    /* Transaction Row Cards */
    .tx-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 14px 18px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Section Headings */
    .section-title {
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 14px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Form Boxes */
    .form-box {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    
    /* AI Box */
    .ai-insight-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
        border: 2px solid #7dd3fc;
        border-radius: 16px;
        padding: 20px 24px;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    
    /* Loan Cards */
    .loan-card {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-left: 6px solid #0284c7;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 700;
        padding: 10px 18px;
        border-radius: 10px;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
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

# --- TOP BOLD APP BAR ---
st.markdown("""
<div class="hero-banner">
    <div>
        <div class="hero-title">🪙 KasuAI</div>
        <div class="hero-subtitle">குடும்ப நிதி, ஸ்மார்ட் SMS மூளை & சேமிப்பு மேலாண்மை</div>
    </div>
    <div style="text-align:right;">
        <span style="background:#22c55e; color:#0f172a; padding:5px 14px; border-radius:20px; font-weight:800; font-size:12px;">நேரலை (Live)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- USER SELECTOR & QUICK BAR ---
col_u1, col_u2 = st.columns([1.5, 1])
with col_u1:
    active_user = st.radio(
        "👤 தற்போதைய பயனர் யார்?", 
        ["👤 ராஜ்குமார் (கணவர்)", "👩 மனைவி (வீட்டுச் செலவு)"], 
        horizontal=True,
        label_visibility="collapsed"
    )

with col_u2:
    current_time_str = datetime.now().strftime("%d-%b-%Y | %I:%M %p")
    st.markdown(f"<div style='text-align:right; font-size:13px; font-weight:600; color:#64748b; padding-top:8px;'>📅 {current_time_str}</div>", unsafe_allow_html=True)

st.write("")

# --- GEMINI API KEY SETUP IN EXPANDER ---
gemini_api_key = os.getenv("GEMINI_API_KEY", "")
with st.sidebar:
    st.header("⚙️ KasuAI அமைப்புகள்")
    user_key = st.text_input("🔑 Google Gemini API Key (இலவசம்):", value=gemini_api_key, type="password", placeholder="AIzaSy...")
    if user_key:
        gemini_api_key = user_key
        st.success("🤖 KasuAI AI மூளை தயார்!")
    else:
        st.info("💡 இலவச Gemini API Key சேர்த்தால் அதிவேக AI புரிதல் செயல்படும்.")

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
    conn = get_db()
    all_df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    
    current_m = datetime.now().strftime("%Y-%m")
    available_months = ["இந்த மாதம் (நடப்பு மாதம்)"]
    if not all_df.empty:
        all_df['month_year'] = pd.to_datetime(all_df['date'], errors='coerce').dt.strftime('%Y-%m')
        unique_months = sorted([m for m in all_df['month_year'].dropna().unique() if str(m).startswith('202')], reverse=True)
        unique_months = [m for m in unique_months if m != current_m]
        available_months += unique_months
        
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        selected_view = st.selectbox("📅 கணக்கு மாதம்:", available_months)
    
    target_month = current_m if selected_view == "இந்த மாதம் (நடப்பு மாதம்)" else selected_view
    df = all_df[all_df['month_year'] == target_month] if not all_df.empty and 'month_year' in all_df else pd.DataFrame()
    
    total_spent = df['amount'].sum() if not df.empty else 0.0
    wife_spent = df[df['user'].str.contains('மனைவி', na=False)]['amount'].sum() if not df.empty else 0.0
    wife_remaining = max(0.0, 40000.0 - wife_spent)
    wife_pct = min(100.0, (wife_spent / 40000.0) * 100.0) if 40000.0 > 0 else 0.0
    savings_est = max(0.0, 65000.0 - total_spent)
    
    # 3 BOLD HERO METRICS
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">💳 மொத்த செலவு ({target_month})</div>
            <div class="stat-number c-expense">₹{total_spent:,.2f}</div>
            <div class="stat-sub">
                <span style="background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:6px; font-weight:700;">
                    {len(df)} பரிவர்த்தனைகள்
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        fill_color = "#0284c7" if wife_pct < 85 else "#ea580c" if wife_pct < 100 else "#dc2626"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">👩 மனைவி பட்ஜெட் (₹40,000)</div>
            <div class="stat-number c-budget">₹{wife_spent:,.2f}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {wife_pct}%; background: {fill_color};"></div>
            </div>
            <div class="stat-sub" style="margin-top:8px; justify-content:space-between;">
                <span>மீதம்: <b>₹{wife_remaining:,.2f}</b></span>
                <span style="font-size:11px; color:#64748b;">{wife_pct:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">💰 மாத சேமிப்பு நிலை</div>
            <div class="stat-number c-savings">₹{savings_est:,.2f}</div>
            <div class="stat-sub">
                <span style="background:#dcfce7; color:#166534; padding:2px 8px; border-radius:6px; font-weight:700;">
                    இலக்கு: ₹65,000
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # KASUAI SMART FINANCIAL ADVISOR BUTTON
    st.write("")
    if st.button("🤖 KasuAI தமிழ் நிதி ஆலோசகர் அறிக்கை (AI Financial Insights)", use_container_width=True):
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
        with st.spinner("🧠 KasuAI உங்கள் குடும்ப நிதியை அலசுகிறது..."):
            ai_advice = None
            if gemini_api_key:
                ai_advice_obj = call_gemini_ai(advice_prompt, gemini_api_key)
                if ai_advice_obj:
                    # Direct string or fallback
                    ai_advice = json.dumps(ai_advice_obj, ensure_ascii=False)
            if not ai_advice:
                # Built-in smart rule advice in Tamil
                ai_advice = f"""
                ### 🪙 KasuAI குடும்ப நிதி அறிக்கை ({target_month}):
                * **👍 சேமிப்பு நிலை:** இதுவரை மொத்த செலவு ₹{total_spent:,.2f}. மாத இலக்கு ₹65,000 சேமிப்பில் இன்னும் **₹{savings_est:,.2f}** சேமிக்க வாய்ப்புள்ளது.
                * **👩 மனைவி பட்ஜெட்:** ₹40,000 பட்ஜெட்டில் இதுவரை ₹{wife_spent:,.2f} ({wife_pct:.1f}%) செலவாகியுள்ளது. கையில் மீதம் **₹{wife_remaining:,.2f}** உள்ளது.
                * **💡 சிறு துளி பெருவெள்ளம்:** தினசரி சிறு சில்லறை செலவுகளைக் கண்காணிப்பது மாத இறுதியில் பெரிய சேமிப்பைத் தரும்!
                """
            st.markdown(f"""
            <div class="ai-insight-box">
                {ai_advice}
            </div>
            """, unsafe_allow_html=True)
            
    st.write("")
    
    if not df.empty:
        ch_col1, ch_col2 = st.columns([1, 1])
        summary = df.groupby("category")["amount"].sum().reset_index()
        
        with ch_col1:
            st.markdown('<div class="section-title">🍩 துறை வாரியான செலவுப் பகிர்வு</div>', unsafe_allow_html=True)
            fig = px.pie(
                summary, values="amount", names="category", hole=0.5,
                color_discrete_sequence=["#0284c7", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#64748b"]
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), 
                height=290,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with ch_col2:
            st.markdown('<div class="section-title">📊 செலவு அட்டவணை</div>', unsafe_allow_html=True)
            sum_disp = summary.rename(columns={"category": "பிரிவு", "amount": "தொகை (₹)"}).copy()
            sum_disp["தொகை (₹)"] = sum_disp["தொகை (₹)"].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(sum_disp, use_container_width=True, height=270, hide_index=True)
            
        st.markdown('<div class="section-title">📋 சமீபத்திய செலவுகள் (நீக்க/சரிபார்க்க)</div>', unsafe_allow_html=True)
        recent_df = df.sort_values(by="id", ascending=False)
        for _, r in recent_df.head(15).iterrows():
            d_col1, d_col2 = st.columns([5, 1])
            date_disp = str(r['date'])[:16] if pd.notna(r['date']) else ""
            notes_disp = f" — {str(r['notes'])[:35]}" if pd.notna(r['notes']) and r['notes'] else ""
            merchant_disp = f"[{r['merchant']}] " if pd.notna(r['merchant']) and r['merchant'] != r['category'] else ""
            
            with d_col1:
                st.markdown(f"""
                <div class="tx-card">
                    <div>
                        <span style="font-weight:700; font-size:15px; color:#0f172a;">{r['category']}</span>
                        <span style="color:#64748b; font-size:13px; margin-left:8px;">{merchant_disp}{notes_disp}</span>
                        <div style="font-size:12px; color:#94a3b8; margin-top:2px;">{date_disp} • {r['user']}</div>
                    </div>
                    <div style="font-size:17px; font-weight:800; color:#dc2626;">
                        ₹{r['amount']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with d_col2:
                if st.button("🗑️ நீக்கு", key=f"del_exp_{r['id']}"):
                    conn = get_db()
                    conn.execute("DELETE FROM expenses WHERE id = ?", (r['id'],))
                    conn.commit()
                    conn.close()
                    st.success("நீக்கப்பட்டது!")
                    st.rerun()
    else:
        st.markdown("""
        <div style="background:#ffffff; border:2px dashed #cbd5e1; border-radius:16px; padding:35px; text-align:center; color:#64748b; margin-top:10px;">
            <div style="font-size:32px; margin-bottom:8px;">📝</div>
            <div style="font-size:16px; font-weight:700; color:#0f172a;">இந்த மாதத்திற்கான செலவுகள் எதுவும் இன்னும் பதிவாகவில்லை</div>
            <div style="font-size:13px; margin-top:4px;">மேலே உள்ள '➕ புதிய செலவு' டேப் மூலம் புதிய செலவைச் சேர்க்கவும் அல்லது SMS-ஐ பேஸ்ட் செய்யவும்.</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== 2. ADD EXPENSE & SMS DECODER ====================
with tab_entry:
    st.markdown('<div class="section-title">⚡ விரைவுச் செலவுப் பதிவு & KasuAI SMS டிகோடர்</div>', unsafe_allow_html=True)
    
    # 1-CLICK QUICK CHIPS FOR COMMON DAILY EXPENSES
    st.markdown("<span style='font-size:13px; font-weight:700; color:#64748b;'>⚡ ஒரு க்ளிக் நேரடிச் செலவு (Quick Presets):</span>", unsafe_allow_html=True)
    q_c1, q_c2, q_c3, q_c4, q_c5 = st.columns(5)
    
    def add_quick_expense(cat, amt, note):
        conn = get_db()
        conn.execute("INSERT INTO expenses (date, user, category, amount, mode, merchant, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), active_user, cat, amt, "ரொக்கம் (Cash)", note, note))
        conn.commit()
        conn.close()
        st.success(f"✅ {note} ₹{amt} ({active_user}) கணக்கில் சேர்க்கப்பட்டது!")
        st.rerun()

    if q_c1.button("☕ டீ / ஸ்நாக்ஸ் ₹20"):
        add_quick_expense("டீ & சிற்றுண்டி", 20.0, "டீ / காபி")
    if q_c2.button("🥛 பால் பாக்கெட் ₹35"):
        add_quick_expense("மளிகை & உணவு", 35.0, "பால்")
    if q_c3.button("🥦 காய்கறி ₹150"):
        add_quick_expense("மளிகை & உணவு", 150.0, "காய்கறி")
    if q_c4.button("⛽ பெட்ரோல் ₹200"):
        add_quick_expense("வாகனம் & Fuel", 200.0, "பெட்ரோல்")
    if q_c5.button("🌾 மளிகை ₹500"):
        add_quick_expense("மளிகை & உணவு", 500.0, "மளிகைக் கடை")
        
    st.write("")
    
    col_in1, col_in2 = st.columns([1, 1])
    
    with col_in1:
        st.markdown("""
        <div class="form-box">
            <div style="font-size:16px; font-weight:800; color:#0f172a; margin-bottom:12px;">
                🧠 1. KasuAI SMS டிகோடர் (பேஸ்ட் செய்யவும்)
            </div>
        """, unsafe_allow_html=True)
        
        sms_txt = st.text_area(
            "SMS உரை:", 
            placeholder="வங்கி மெசேஜ், UPI டெபிட், OTP, அல்லது எச்சரிக்கை செய்தியை இங்கே பேஸ்ட் செய்யவும்...", 
            height=135,
            label_visibility="collapsed"
        )
        
        if st.button("🚀 KasuAI மூலம் படித்துப் பதிவு செய்", type="primary", use_container_width=True):
            if sms_txt.strip():
                with st.spinner("KasuAI SMS-ஐப் பகுப்பாய்வு செய்கிறது..."):
                    result = parse_sms_with_brain(sms_txt, gemini_api_key)
                    
                if result and result["is_expense"] and result["amount"] > 0:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO expenses (date, user, category, amount, mode, merchant, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), active_user, result["category"], result["amount"], "SMS / UPI", result["merchant"], sms_txt)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"💳 **{result['category']}** செலவு ₹{result['amount']:,.2f} ({result['merchant']}) கணக்கில் சேர்க்கப்பட்டது! [பகுப்பாய்வு: {result['source']}]")
                    st.rerun()
                else:
                    cat = result["category"] if result else "இதர அறிவிப்பு"
                    explanation = result["explanation"] if result else "தகவல் அறிவிப்பு"
                    conn = get_db()
                    conn.execute("INSERT INTO other_alerts (date, sender, category, explanation, raw_text) VALUES (?, ?, ?, ?, ?)",
                                 (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SMS", cat, explanation, sms_txt))
                    conn.commit()
                    conn.close()
                    st.info(f"🔔 **{cat}:** {explanation}")
                    st.rerun()
            else:
                st.warning("SMS உரையை உள்ளிடவும்!")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_in2:
        st.markdown("""
        <div class="form-box">
            <div style="font-size:16px; font-weight:800; color:#0f172a; margin-bottom:12px;">
                ✍️ 2. கைமுறைப் பதிவு (ரொக்கச் செலவு)
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("manual_entry_form"):
            man_amt = st.number_input("தொகை (₹):", min_value=1.0, value=50.0, step=10.0)
            man_cat = st.selectbox("பிரிவு:", ["மளிகை & உணவு", "டீ & சிற்றுண்டி", "வாகனம் & Fuel", "மின்சாரக் கட்டணம்", "கடன்கள் & EMI", "விவசாயச் செலவு", "மருத்துவம்", "இதர செலவுகள்"])
            man_mode = st.selectbox("செலுத்திய முறை:", ["ரொக்கம் (Cash)", "PhonePe / GPay", "வங்கி கணக்கு"])
            man_notes = st.text_input("குறிப்பு (எ.கா: காய்கறி, டீ, மளிகை):", "")
            
            if st.form_submit_button("➕ செலவைச் சேமிக்கவும்", type="primary", use_container_width=True):
                conn = get_db()
                conn.execute("INSERT INTO expenses (date, user, category, amount, mode, merchant, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), active_user, man_cat, man_amt, man_mode, man_notes or "நேரடிப் பதிவு", man_notes))
                conn.commit()
                conn.close()
                st.success(f"✅ ₹{man_amt:,.2f} ({man_cat}) பதிவானது!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== 3. LOANS & EMI ====================
with tab_loans:
    st.markdown('<div class="section-title">🏦 கடன் & தவணைகள் (Loans & EMI Tracker)</div>', unsafe_allow_html=True)
    conn = get_db()
    l_df = pd.read_sql_query("SELECT * FROM loans", conn)
    conn.close()
    
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
                    conn = get_db()
                    conn.execute("INSERT OR REPLACE INTO loans (loan_name, total_amount, monthly_emi, due_day, remaining_months) VALUES (?, ?, ?, ?, ?)",
                                 (l_name.strip(), l_total, l_emi, l_day, l_months))
                    conn.commit()
                    conn.close()
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
                        conn = get_db()
                        conn.execute("DELETE FROM loans WHERE id = ?", (l_row['id'],))
                        conn.commit()
                        conn.close()
                        st.success("கடன் நீக்கப்பட்டது!")
                        st.rerun()
        else:
            st.markdown("""
            <div style="background:#ffffff; border:2px dashed #cbd5e1; border-radius:14px; padding:30px; text-align:center; color:#64748b;">
                தற்போது கடன்கள் எதுவும் பதிவு செய்யப்படவில்லை.<br>புதிய கடனைச் சேர்க்க இடதுபுறப் படிவத்தைப் பயன்படுத்தவும்.
            </div>
            """, unsafe_allow_html=True)

# ==================== 4. HISTORY & TRENDS ====================
with tab_history:
    st.markdown('<div class="section-title">📜 கடந்த கால வரலாற்று வரைபடங்கள் & அறிக்கைகள்</div>', unsafe_allow_html=True)
    conn = get_db()
    h_df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    
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
                conn = get_db()
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
                    conn.executemany("INSERT INTO expenses (date, user, category, amount, mode, merchant, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", batch_records)
                    conn.commit()
                    st.success(f"🎉 {len(batch_records)} செலவுகள் வெற்றிகரமாக சேர்க்கப்பட்டன!")
                else:
                    st.warning("கோப்பில் செலவுப் பதிவுகள் எதுவும் கண்டறியப்படவில்லை.")
                conn.close()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")

# ==================== 6. OTHER ALERTS ====================
with tab_alerts:
    st.markdown('<div class="section-title">🔔 இதர எச்சரிக்கைகள் & தமிழ் விளக்கம்</div>', unsafe_allow_html=True)
    conn = get_db()
    alerts_df = pd.read_sql_query("SELECT id, date, category, explanation, raw_text FROM other_alerts ORDER BY id DESC", conn)
    conn.close()
    if not alerts_df.empty:
        for idx, row in alerts_df.iterrows():
            with st.expander(f"{row['category']} — {row['date']}"):
                st.write(f"💡 **விளக்கம்:** {row['explanation']}")
                st.code(row['raw_text'], language="text")
                if st.button("🗑️ நீக்கு", key=f"del_alert_{row['id']}"):
                    conn = get_db()
                    conn.execute("DELETE FROM other_alerts WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.success("எச்சரிக்கை நீக்கப்பட்டது!")
                    st.rerun()
    else:
        st.markdown("""
        <div style="background:#ffffff; border:2px dashed #cbd5e1; border-radius:14px; padding:30px; text-align:center; color:#64748b;">
            இதர எச்சரிக்கைகள் (OTP, Mandate, Stock tips) எதுவும் இல்லை.
        </div>
        """, unsafe_allow_html=True)
