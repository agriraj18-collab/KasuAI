import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from app import parse_sms_with_brain, db_insert_expense, db_insert_alert

app = Flask(__name__)

@app.route("/api/status", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "KasuAI Sync API",
        "database": "Supabase Cloud + Local Backup",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/sms", methods=["POST"])
def receive_sms():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
            
        sms_text = data.get("message") or data.get("text") or data.get("body", "")
        sender = data.get("sender", "SMS")
        user = data.get("user", "👤 ராஜ்குமார் (கணவர்)")
        dt = data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not sms_text.strip():
            return jsonify({"status": "error", "message": "Empty SMS body"}), 400
            
        gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        result = parse_sms_with_brain(sms_text, gemini_api_key)
        
        if result and result["is_expense"] and result["amount"] > 0:
            db_insert_expense(
                dt, user, result["category"], result["amount"], "Mobile SMS", result["merchant"], sms_text
            )
            return jsonify({
                "status": "success",
                "type": "expense",
                "category": result["category"],
                "amount": result["amount"],
                "merchant": result["merchant"],
                "explanation": result["explanation"],
                "source": result["source"]
            }), 200
        else:
            cat = result["category"] if result else "இதர அறிவிப்பு"
            explanation = result["explanation"] if result else "தகவல் அறிவிப்பு செய்தி"
            db_insert_alert(dt, sender, cat, explanation, sms_text)
            return jsonify({
                "status": "success",
                "type": "alert",
                "category": cat,
                "explanation": explanation
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 KasuAI Sync API running on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
