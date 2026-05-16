import os
import io
import random
import sqlite3
import smtplib
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from email.mime.text import MIMEText

app = FastAPI(title="S.H.I.E.L.D. API Core")

@app.get("/")
def home():
    return {
        "status": "S.H.I.E.L.D. Backend Active",
        "version": "2.0.1",
        "endpoints": ["/api/submit-report", "/api/track", "/api/admin/all-reports"]
    }

# --- 1. FIXED CORS SETTINGS ---
# This allows your frontend (port 5500) to talk to the backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. CONFIGURATION ---
DB_FILE = "shield.db"
UPLOAD_DIR = "cleaned_evidence"
OTP_STORAGE = {}

# Email Config (Update these for real emails)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com" 
SENDER_PASSWORD = "your-app-password"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- 3. UPDATED DATABASE SCHEMA ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # We added device_type, location, has_suspect, etc.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            case_id TEXT PRIMARY KEY,
            category TEXT,
            narrative TEXT,
            device_type TEXT,
            location TEXT,
            has_suspect BOOLEAN,
            suspect_name TEXT,
            suspect_details TEXT,
            ai_triage TEXT,
            routing_advice TEXT,
            status TEXT DEFAULT 'Received'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 4. DATA MODELS (Must match index.html exactly) ---
class EmailRequest(BaseModel):
    email: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class CasePayload(BaseModel):
    category: str
    narrative: str
    device_type: str        # ADDED
    incident_location: str   # ADDED
    has_suspect: bool       # ADDED
    suspect_name: Optional[str] = "N/A"
    suspect_details: Optional[str] = "N/A"

class StatusUpdatePayload(BaseModel):
    new_status: str

# --- 5. LOGIC ---
def classify_incident(text: str):
    text = text.lower()
    cyber_keywords = ["phishing", "hacked", "password", "scam", "virus", "account", "login", "email"]
    physical_keywords = ["stolen", "theft", "broke", "window", "bag", "laptop", "physical", "hit"]
    
    cyber_score = sum(1 for word in cyber_keywords if word in text)
    physical_score = sum(1 for word in physical_keywords if word in text)

    if cyber_score > physical_score:
        return "CYBER", "High priority digital incident. Assigned to Cyber Forensics."
    elif physical_score > cyber_score:
        return "NON-CYBER", "Physical security matter. Routed to Campus Police."
    else:
        return "GENERAL", "Report received. Routed for manual review."

# --- 6. API ENDPOINTS ---

@app.post("/api/verify-email")
async def verify_email(payload: EmailRequest):
    otp = str(random.randint(100000, 999999))
    OTP_STORAGE[payload.email] = otp
    print(f"DEBUG: OTP for {payload.email} is {otp}")
    return {"message": "OTP Generated", "debug": otp}

@app.post("/api/check-otp")
async def check_otp(payload: OTPVerifyRequest):
    if OTP_STORAGE.get(payload.email) == payload.otp:
        return {"status": "verified"}
    raise HTTPException(status_code=400, detail="Invalid OTP")

@app.post("/api/submit-report")
async def submit_report(payload: CasePayload):
    try:
        category_type, routing_note = classify_incident(payload.narrative)
        case_id = f"SHIELD-{random.randint(100000, 999999)}"
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports (case_id, category, narrative, device_type, location, has_suspect, suspect_name, suspect_details, ai_triage, routing_advice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (case_id, payload.category, payload.narrative, payload.device_type, payload.incident_location, 
              payload.has_suspect, payload.suspect_name, payload.suspect_details, category_type, routing_note))
        conn.commit()
        conn.close()
        
        return {"success": True, "case_token_id": case_id, "triage_result": category_type, "routing_advice": routing_note}
    except Exception as e:
        print(f"CRITICAL BACKEND ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-evidence/{case_id}")
async def upload_evidence(case_id: str, file: UploadFile = File(...)):
    content = await file.read()
    image = Image.open(io.BytesIO(content))
    clean_image = Image.new(image.mode, image.size)
    clean_image.putdata(list(image.getdata()))
    file_path = os.path.join(UPLOAD_DIR, f"CLEAN_{case_id}_{file.filename}")
    clean_image.save(file_path)
    return {"status": "Cleaned", "path": file_path}

@app.get("/api/track/{case_token}")
async def track_case(case_token: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE case_id = ?", (case_token.upper(),))
    row = cursor.fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404)
    return dict(row)

@app.get("/api/admin/all-reports")
async def get_all_reports():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/admin/update-status/{case_id}")
async def update_status(case_id: str, payload: StatusUpdatePayload):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE reports SET status = ? WHERE case_id = ?", (payload.new_status, case_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.delete("/api/admin/delete-report/{case_id}")
async def delete_report(case_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE case_id = ?", (case_id,))
    conn.commit()
    conn.close()
    return {"success": True}