from fastapi import FastAPI, File, Form, Query, UploadFile, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
from fastapi import Form
from fastapi.responses import PlainTextResponse
import asyncpg
import datetime
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
import ast
import uuid
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from datetime import date, datetime, timedelta, timezone, time
import razorpay
import os
from dotenv import load_dotenv
import re
load_dotenv()
from pywebpush import webpush, WebPushException
import firebase_admin
from firebase_admin import messaging, credentials
from sqlalchemy import create_engine, text
import os
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
import requests
import json


import uvicorn




DATABASE_URL = os.getenv(
   "DATABASE_URL",
   "postgresql://darsh:Darsh123@localhost:5432/vetapp"
)


engine = create_engine(DATABASE_URL)
print(DATABASE_URL)


with engine.connect() as conn:
   result = conn.execute(text("SELECT NOW()"))
   print("Connected to DB! Current time:", result.scalar())






# WHATSAPP_PHONE_NUMBER_ID = "756800504184567"
# WHATSAPP_ACCESS_TOKEN = "EAAZAoZAtAUH6wBPGA9CHiBAhpd3uAxkw1hTobWORnvxiQ5ejrZAjMVprvgzzkzRgqavoRQsxrr1JxHAbiPnjhBU4STLvM1IqdhqCZBZCfnqkVRHnaQToYG2C0OiEaBJsJH5aAfUgtf4lPm62QX43kPn74nEEqcBO9LhLQPx25bkZAKd7p1z0ZBMDQHzSzirHG05emNnxSmRW1AE55VZAuA9t2GajJQXxx19EF96D"








app = FastAPI()


origins = [
   "http://localhost",
   "http://localhost:3000",
   "*",
]


app.add_middleware(
   CORSMiddleware,
   allow_origins=origins,
   allow_credentials=True,
   allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
   allow_headers=["*"],  # Allow all headers
)


app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))


class CustomMiddleware(BaseHTTPMiddleware):
   async def dispatch(self, request, call_next):
       response = await call_next(request)
       response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
       response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
       return response








app.add_middleware(CustomMiddleware)
import os






class UserResponse(BaseModel):
   user_id: str
   email: str
   name: str
   phone_number: str
   owner_address: str




from sqlalchemy import text


def init_db():
   with engine.begin() as conn:
       # --- Drop unused tables ---
       conn.execute(text("DROP TABLE IF EXISTS reminder_logs CASCADE;"))
       conn.execute(text("DROP TABLE IF EXISTS Bookings CASCADE;"))
       conn.execute(text("DROP TABLE IF EXISTS MessageEvents CASCADE;"))


       # -- Helper trigger function to maintain updated_at --
       conn.execute(text("""
       CREATE OR REPLACE FUNCTION set_updated_at_column()
       RETURNS TRIGGER AS $$
       BEGIN
           NEW.updated_at = now();
           RETURN NEW;
       END;
       $$ LANGUAGE plpgsql;
       """))


       # -- Doctor table --
       conn.execute(text("""
       CREATE TABLE IF NOT EXISTS Doctor (
           doctor_id SERIAL PRIMARY KEY,
           doctor_email VARCHAR(255) UNIQUE NOT NULL,
           doctor_phone VARCHAR(20),
           doctor_name VARCHAR(100),
           clinic_name VARCHAR(150),
           created_at TIMESTAMPTZ DEFAULT now(),
           updated_at TIMESTAMPTZ DEFAULT now()
       );
       """))


       conn.execute(text("""
       ALTER TABLE Doctor
       ADD COLUMN IF NOT EXISTS whatsapp_access_token TEXT,
       ADD COLUMN IF NOT EXISTS whatsapp_number_id TEXT;
       """))
       print("Successfull added the numberid and access token")




       # -- Reports table --
       conn.execute(text("""
       CREATE TABLE IF NOT EXISTS Reports (
           report_id SERIAL PRIMARY KEY,
           doctor_id INT NOT NULL,
           pet_name VARCHAR(100) NOT NULL,
           pet_parent_phone VARCHAR(20) NOT NULL,
           reminder DATE,
           report_pdf_link TEXT,
           report_type VARCHAR(50) DEFAULT 'Unknown',
           created_at TIMESTAMPTZ DEFAULT now(),
           updated_at TIMESTAMPTZ DEFAULT now(),
           FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE
       );
       """))
       conn.execute(text("""
           ALTER TABLE Reports
           ADD COLUMN IF NOT EXISTS share_password VARCHAR(4);
       """))
       conn.execute(text("""
           UPDATE Reports
           SET share_password = RIGHT(pet_parent_phone, 4)
       """))


       # -- Safe ALTERs (idempotent) --
       conn.execute(text("ALTER TABLE Reports ADD COLUMN IF NOT EXISTS report_type VARCHAR(50) DEFAULT 'Unknown';"))
       conn.execute(text("ALTER TABLE Reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();"))
       conn.execute(text("ALTER TABLE Reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();"))
       conn.execute(text("ALTER TABLE Doctor ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();"))
       conn.execute(text("ALTER TABLE Doctor ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();"))


       # -- Attach updated_at triggers --
       conn.execute(text("DROP TRIGGER IF EXISTS trg_doctor_updated_at ON Doctor;"))
       conn.execute(text("""
       CREATE TRIGGER trg_doctor_updated_at
         BEFORE UPDATE ON Doctor
         FOR EACH ROW
         EXECUTE FUNCTION set_updated_at_column();
       """))


       conn.execute(text("DROP TRIGGER IF EXISTS trg_reports_updated_at ON Reports;"))
       conn.execute(text("""
       CREATE TRIGGER trg_reports_updated_at
         BEFORE UPDATE ON Reports
         FOR EACH ROW
         EXECUTE FUNCTION set_updated_at_column();
       """))


       # -- Reminders table --
       conn.execute(text("""
       CREATE TABLE IF NOT EXISTS Reminders (
           reminder_id       BIGSERIAL PRIMARY KEY,
           doctor_id         BIGINT NOT NULL,
           report_id         BIGINT NULL,
           pet_parent_phone  VARCHAR(32) NOT NULL,
           pet_name          TEXT NULL,
           clinic_name       TEXT NULL,
           doctor_phone      VARCHAR(32) NULL,
           message_template  TEXT NOT NULL,
           channel           VARCHAR(20) NOT NULL DEFAULT 'sms',
           reminder_at       TIMESTAMPTZ NOT NULL,
           timezone          TEXT NOT NULL DEFAULT 'Asia/Kolkata',
           recurrence_type   VARCHAR(10) NOT NULL DEFAULT 'none',
           recurrence_interval INT NOT NULL DEFAULT 1,
           recurrence_weekdays INT[] NULL,
           status            VARCHAR(20) NOT NULL DEFAULT 'pending',
           attempts          SMALLINT NOT NULL DEFAULT 0,
           max_attempts      SMALLINT NOT NULL DEFAULT 3,
           last_attempt_at   TIMESTAMPTZ NULL,
           metadata          JSONB DEFAULT '{}'::jsonb,
           active            BOOLEAN NOT NULL DEFAULT TRUE,
           created_by        BIGINT NULL,
           created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
           updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
           CONSTRAINT fk_reminder_doctor FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id) ON DELETE CASCADE,
           CONSTRAINT fk_reminder_report FOREIGN KEY (report_id) REFERENCES Reports(report_id) ON DELETE SET NULL
       );
       """))


       # -- Indexes for Reminders --
       conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reminders_reminder_at_active ON Reminders (reminder_at) WHERE active = true;"))
       conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reminders_doctor_id ON Reminders (doctor_id);"))
       conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reminders_pet_parent_phone ON Reminders (pet_parent_phone);"))


       # -- Attach updated_at trigger to Reminders --
       conn.execute(text("DROP TRIGGER IF EXISTS trg_reminders_updated_at ON Reminders;"))
       conn.execute(text("""
       CREATE TRIGGER trg_reminders_updated_at
         BEFORE UPDATE ON Reminders
         FOR EACH ROW
         EXECUTE FUNCTION set_updated_at_column();
       """))


       # -- Phone constraint on Reports --
       conn.execute(text("""
       DO $$
       BEGIN
         IF NOT EXISTS (
           SELECT 1 FROM pg_constraint WHERE conname = 'chk_reports_pet_parent_phone_e164'
         ) THEN
           ALTER TABLE Reports
             ADD CONSTRAINT chk_reports_pet_parent_phone_e164 CHECK (pet_parent_phone ~ '^\\+\\d{6,15}$');
         END IF;
       EXCEPTION WHEN duplicate_object THEN
         NULL;
       END;
       $$;
       """))


   print("Database initialized. Removed reminder_logs, Bookings, MessageEvents.")




  






# Run DB init on FastAPI startup
@app.on_event("startup")
def startup_event():
   init_db()






@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
  
   return "Welcome to the Medocs Backend"




class CreateOrderRequest(BaseModel):
   user_id: str


class GoogleLoginModel(BaseModel):
   email: EmailStr
   name: str = None
   clinic_name: str = None






@app.post("/doctor_login")
async def doctor_login(data: GoogleLoginModel):
   print("Received login request for email:", data.email)
   try:
       with engine.begin() as conn:
           # Check if doctor already exists
           result = conn.execute(
               text("SELECT * FROM Doctor WHERE doctor_email = :email"),
               {"email": data.email}
           ).mappings().fetchone()  # <-- use .mappings() to get dict-like row


           if result:
               print("Doctor exists in DB:", result["doctor_id"], result["doctor_email"])
               # Doctor exists → log in
               return {
                   "status": True,
                   "message": "Login Successful",
                   "data": {
                       "doctor_id": result["doctor_id"],
                       "email": result["doctor_email"],
                       "name": result["doctor_name"],
                       "clinic_name": result["clinic_name"]
                   },
               }


           else:
               print("Doctor not found, registering new doctor:", data.email)
               # Doctor does not exist → insert with optional fields
               insert_result = conn.execute(
                   text("""
                       INSERT INTO Doctor (doctor_email, doctor_name, clinic_name)
                       VALUES (:email, :name, :clinic_name)
                       RETURNING doctor_id, doctor_email, doctor_name, clinic_name
                   """),
                   {"email": data.email, "name": data.name, "clinic_name": data.clinic_name}
               ).mappings().fetchone()  # <-- use .mappings() here too


               print("New doctor registered with ID:", insert_result["doctor_id"])
               return {
                   "status": True,
                   "message": "Registration Successful",
                   "data": {
                       "doctor_id": insert_result["doctor_id"],
                       "email": insert_result["doctor_email"],
                       "name": insert_result["doctor_name"],
                       "clinic_name": insert_result["clinic_name"]
                   },
               }


   except Exception as e:
       print("Error during doctor login:", str(e))
       raise HTTPException(
           status_code=500,
           detail={"status": False, "message": f"Failed to process request: {str(e)}"},
       )






class DoctorUpdateModel(BaseModel):
   doctor_email: EmailStr
   doctor_name: str | None = None
   doctor_phone: str | None = None
   clinic_name: str | None = None
   whatsapp_access_token : str | None = None
   whatsapp_number_id : str | None = None


  
def normalize_indian_phone(phone: str) -> str | None:
   if not phone:
       return None
   digits = ''.join(filter(str.isdigit, phone))


   # +91XXXXXXXXXX
   if len(digits) == 12 and digits.startswith("91"):
       n = digits[2:]
       return f"+91{n}" if n[0] in "6789" else None


   # 0XXXXXXXXXX
   if len(digits) == 11 and digits.startswith("0"):
       n = digits[1:]
       return f"+91{n}" if n[0] in "6789" else None


   # XXXXXXXXXX
   if len(digits) == 10 and digits[0] in "6789":
       return f"+91{digits}"


   return None


@app.post("/doctor_update")
async def doctor_update(data: DoctorUpdateModel):
   try:
       # Basic validation
       if not data or not data.doctor_email:
           raise HTTPException(status_code=400, detail={"status": False, "message": "doctor_email is required"})


       normalized_phone = None
       if getattr(data, "doctor_phone", None) is not None:
           normalized_phone = normalize_indian_phone(data.doctor_phone)
           print(f"Normalized phone: {normalized_phone}")
           if not normalized_phone:
               print("❌ Invalid phone number")
               raise HTTPException(
                   status_code=400,
                   detail={"status": False, "message": "Invalid doctor phone number"}
               )


       # Convert empty strings to None so they don't overwrite existing DB values
       def none_if_empty(s):
           if s is None: return None
           s2 = s.strip()
           return s2 if s2 != "" else None
      
       print("WhatsApp Acess Token", data.whatsapp_access_token)


       doctor_name_val = none_if_empty(data.doctor_name)
       clinic_name_val = none_if_empty(data.clinic_name)
       whatsapp_token_val = none_if_empty(data.whatsapp_access_token)
       whatsapp_id_val = none_if_empty(data.whatsapp_number_id)






       print("DEBUG doctor_update called with:", {
           "doctor_email": data.doctor_email,
           "doctor_name": doctor_name_val,
           "doctor_phone": normalized_phone,
           "clinic_name": clinic_name_val,
           "whatsapp_access_token": "***HIDDEN***" if whatsapp_token_val else None,
           "whatsapp_number_id": "***HIDDEN***" if whatsapp_id_val else None
       })


       with engine.begin() as conn:
           # Update Doctor with COALESCE to preserve old values if null
           result = conn.execute(
               text("""
                   UPDATE Doctor
                   SET doctor_name = COALESCE(:doctor_name, doctor_name),
                       doctor_phone = COALESCE(:doctor_phone, doctor_phone),
                       clinic_name = COALESCE(:clinic_name, clinic_name),
                       whatsapp_access_token = COALESCE(:whatsapp_access_token, whatsapp_access_token),
                       whatsapp_number_id = COALESCE(:whatsapp_number_id, whatsapp_number_id),
                       updated_at = now()
                   WHERE doctor_email = :doctor_email
                   RETURNING doctor_id, doctor_email, doctor_name, doctor_phone, clinic_name
               """),
               {
                   "doctor_email": data.doctor_email,
                   "doctor_name": doctor_name_val,
                   "doctor_phone": normalized_phone,
                   "clinic_name": clinic_name_val,
                   "whatsapp_access_token": whatsapp_token_val,
                   "whatsapp_number_id": whatsapp_id_val
               }
           ).mappings().fetchone()


           if not result:
               raise HTTPException(status_code=404, detail={"status": False, "message": "Doctor not found"})


           # Return safe response (don't leak token)
           resp_data = dict(result)
           return {
               "status": True,
               "message": "Profile updated successfully",
               "data": resp_data
           }


   except HTTPException:
       raise
   except Exception as e:
       print("ERROR in doctor_update:", str(e))
       raise HTTPException(status_code=500, detail={"status": False, "message": f"Update failed: {str(e)}"})








@app.get("/doctor_profile")
async def get_doctor_profile(email: str):
   with engine.begin() as conn:
       row = conn.execute(text("SELECT doctor_email, doctor_name, doctor_phone, clinic_name FROM Doctor WHERE doctor_email = :email"), {"email": email}).mappings().fetchone()
       if not row:
           raise HTTPException(status_code=404, detail="Doctor not found")
       return {"status": True, "data": dict(row)}


UPLOAD_ROOT = "uploads"
REPORTS_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "reports")
os.makedirs(REPORTS_UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")








def parse_duration_to_date(duration_str: str):
   """
   Accepts:
     - ISO date: "YYYY-MM-DD" => returns date object
     - Duration strings like "1 month", "2 months", "3 weeks", "10 days", "1 year"
   Returns date object (today + duration) or None if not parseable.
   """
   if not duration_str:
       return None


   s = duration_str.strip().lower()


   # If already an ISO date like 2025-08-20, try parse
   iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
   if iso_match:
       try:
           return date.fromisoformat(s)
       except Exception:
           return None


   # Match number + optional space + unit
   m = re.match(r"^(\d+)\s*(day|days|d|week|weeks|w|month|months|mo|year|years|y)s?$", s)
   if not m:
       return None


   num = int(m.group(1))
   unit = m.group(2)


   if unit in ("day", "days", "d"):
       return date.today() + relativedelta(days=num)
   if unit in ("week", "weeks", "w"):
       return date.today() + relativedelta(weeks=num)
   if unit in ("month", "months", "mo"):
       return date.today() + relativedelta(months=num)
   if unit in ("year", "years", "y"):
       return date.today() + relativedelta(years=num)


   return None






ALLOWED_REPORT_TYPES = {
   "prescription": "Prescription",
   "vaccination": "Vaccination",
   "blood work": "Blood Work",
   "bloodwork": "Blood Work",
}


def normalize_report_type(rt: Optional[str]) -> str:
   if not rt:
       return "Unknown"
   key = rt.strip().lower()
   return ALLOWED_REPORT_TYPES.get(key, "Unknown")
# constants: change if you want a different default send time
DEFAULT_REMINDER_HOUR = 22
DEFAULT_REMINDER_MINUTE = 45
DEFAULT_TIMEZONE = "Asia/Kolkata"




def send_whatsapp_template(
   phone_number: str,
   template_name: str,
   parameters: list | None = None,
   language_code: str = "en",  # <-- use "en", "en_GB", or exactly what the template has
   access_token: str = None,
   number_id: str = None
):
   if not access_token or not number_id:
       raise ValueError("Missing WhatsApp access_token or number_id")


   url = f"https://graph.facebook.com/v22.0/{number_id}/messages"
   headers = {
       "Authorization": f"Bearer {access_token}",
       "Content-Type": "application/json"
   }


   template_body = {
       "name": template_name,
       "language": {"code": language_code}
   }


   if parameters:
       template_body["components"] = [{
           "type": "body",
           "parameters": [{"type": "text", "text": str(p)} for p in parameters]
       }]


   payload = {
       "messaging_product": "whatsapp",
       "to": phone_number,
       "type": "template",
       "template": template_body
   }


   print("📤 Payload being sent:", json.dumps(payload, indent=2))
   try:
       resp = requests.post(url, headers=headers, json=payload, timeout=10)
       resp.raise_for_status()
       print(f"✅ Sent: {resp.json()}")
   except requests.HTTPError as e:
       print(f"❌ HTTPError: {e} - {e.response.text}")
   except Exception as e:
       print(f"❌ Error: {e}")


"""
phone_number = "918668861043"  # string, full international format, no '+'


send_whatsapp_template(
   phone_number=phone_number,
   template_name="appointment_followup",  # use the exact name that has 4 params
   parameters=[
       "Cooper",                         # {{1}} pet name
       "Happy Paws Clinic",              # {{2}} clinic name
       "http://localhost:8000/uploads/reports/1/20250818073619_0270800146dc41cab5b8c7c08b38bc4a.jpg",# {{3}} link
       "2025-09-11"                     # {{4}} date (any readable format)
   ],
   language_code="en"                    # must match the template’s language
)
"""




@app.post("/doctor_upload_file")
async def doctor_upload_file(
   request: Request,
   files: List[UploadFile] = File(...),
   user_id: str = Form(...),
   pet_parent_phone: str = Form(...),
   pet_name: str = Form(...),
   reminder: Optional[str] = Form(None),
   report_type: Optional[str] = Form(None),
):
   print("📥 Received doctor_upload_file request")


   # --- Normalize phone ---
   normalized_phone = normalize_indian_phone(pet_parent_phone)
   share_password = normalized_phone[-4:]


   if not normalized_phone:
       raise HTTPException(status_code=400, detail="Invalid pet parent phone number")


   # --- Doctor ID ---
   try:
       doctor_id = int(user_id)
   except ValueError:
       raise HTTPException(status_code=400, detail="Invalid doctor/user id")


   # --- Doctor folder ---
   doctor_folder = os.path.join(REPORTS_UPLOAD_DIR, str(doctor_id))
   os.makedirs(doctor_folder, exist_ok=True)


   saved_file_urls: List[str] = []


   try:
       # --- Save uploaded files ---
       for upload in files:
           ext = os.path.splitext(upload.filename or "file")[1]
           unique_name = f"{datetime.utcnow():%Y%m%d%H%M%S}_{uuid.uuid4().hex}{ext}"
           save_path = os.path.join(doctor_folder, unique_name)
           content = await upload.read()
           with open(save_path, "wb") as f:
               f.write(content)
      
           public_url = f"/uploads/reports/{doctor_id}/{unique_name}"  # internal link
           saved_file_urls.append(public_url)


       # --- Reminder processing ---
       reminder_date: Optional[date] = None
       if reminder:
           try:
               reminder_date = date.fromisoformat(reminder[:10])
           except Exception:
               reminder_date = parse_duration_to_date(reminder)
           if not reminder_date:
               raise HTTPException(
                   status_code=400,
                   detail="Invalid reminder format. Use YYYY-MM-DD or durations like '1 month', '2 weeks', '10 days'."
               )


       final_report_type = normalize_report_type(report_type)


       with engine.begin() as conn:
# --- Insert report ---
           insert_report_sql = text("""
               INSERT INTO Reports
               (doctor_id, pet_name, pet_parent_phone, reminder, report_pdf_link, report_type, share_password)
               VALUES (:doctor_id, :pet_name, :pet_parent_phone, :reminder, :report_pdf_link, :report_type, :share_password)
               RETURNING report_id, doctor_id, pet_name, pet_parent_phone, reminder, report_pdf_link, report_type, share_password, created_at
           """)
           report_row = conn.execute(insert_report_sql, {
               "doctor_id": doctor_id,
               "pet_name": pet_name,
               "pet_parent_phone": normalized_phone,
               "reminder": reminder_date,
               "report_pdf_link": json.dumps(saved_file_urls),
               "report_type": final_report_type,
               "share_password": share_password
           }).mappings().fetchone()




           if not report_row:
               raise HTTPException(status_code=500, detail="Failed to insert report record")


           # --- Fetch doctor info ---
           doctor_row = conn.execute(
               text("SELECT clinic_name, doctor_phone, whatsapp_access_token, whatsapp_number_id FROM Doctor WHERE doctor_id = :did"),
               {"did": doctor_id}
           ).mappings().fetchone()
           clinic_name = doctor_row["clinic_name"] if doctor_row else "Your Clinic"
           doctor_phone_snapshot = doctor_row["doctor_phone"] if doctor_row else None
           whatsapp_token = doctor_row["whatsapp_access_token"] if doctor_row else None
           whatsapp_number_id = doctor_row["whatsapp_number_id"] if doctor_row else None


           # --- Function to insert reminder ---
           def insert_reminder(message: str, reminder_at: datetime):
               insert_sql = text("""
                   INSERT INTO Reminders
                   (doctor_id, report_id, pet_parent_phone, pet_name, clinic_name, doctor_phone,
                    message_template, channel, reminder_at, timezone, recurrence_type, recurrence_interval,
                    status, attempts, max_attempts, metadata, active, created_by)
                   VALUES
                   (:doctor_id, :report_id, :pet_parent_phone, :pet_name, :clinic_name, :doctor_phone,
                    :message_template, :channel, :reminder_at, :timezone, :recurrence_type, :recurrence_interval,
                    :status, :attempts, :max_attempts, :metadata, :active, :created_by)
                   RETURNING reminder_id
               """)
               params = {
                   "doctor_id": doctor_id,
                   "report_id": report_row["report_id"],
                   "pet_parent_phone": normalized_phone,
                   "pet_name": pet_name,
                   "clinic_name": clinic_name,
                   "doctor_phone": doctor_phone_snapshot,
                   "message_template": message,
                   "channel": "whatsapp",
                   "reminder_at": reminder_at,
                   "timezone": DEFAULT_TIMEZONE,
                   "recurrence_type": "none",
                   "recurrence_interval": 1,
                   "status": "pending",
                   "attempts": 0,
                   "max_attempts": 3,
                   "metadata": json.dumps({}),
                   "active": True,
                   "created_by": doctor_id
               }
               return conn.execute(insert_sql, params).mappings().fetchone()


           # --- Immediate WhatsApp reminder ---
           try:
               first_file_url = json.loads(report_row["report_pdf_link"])[0]
               protected_link = f"https://401a8ca5585e.ngrok-free.app/view_report/{report_row['report_id']}"
               # Insert into reminders table
               immediate_message = (
                   f"Hi, Thank you for visiting {clinic_name}. "
                   f"The record is uploaded for {pet_name}. Click the link below to access it:\n{first_file_url}"
               )
               immediate_time = datetime.utcnow().replace(tzinfo=timezone.utc)
               insert_reminder(immediate_message, immediate_time)


               # Send WhatsApp template
               template_name = "appointment_followup"
               parameters = [
                   pet_name,              # {{1}} pet name
                   clinic_name,           # {{2}} clinic name
                   protected_link,        # {{3}} uploaded file link
                   reminder_date.strftime("%Y-%m-%d") if reminder_date else "Not set"  # {{4}} reminder date
               ]


               try:
                   send_whatsapp_template(
                       phone_number=normalized_phone.lstrip('+'),
                       template_name=template_name,
                       parameters=parameters,
                       language_code="en",
                       access_token=whatsapp_token,
                       number_id=whatsapp_number_id


                   )
               except Exception as e:
                   print(f"❌ Failed sending immediate WhatsApp: {e}")


           except Exception as e:
               print(f"❌ Failed to create immediate reminder: {e}")
               raise


           # --- Follow-up reminder ---
           if reminder_date:
               followup_dt = datetime.combine(
                   reminder_date,
                   time(hour=DEFAULT_REMINDER_HOUR, minute=DEFAULT_REMINDER_MINUTE)
               )
               followup_dt = followup_dt.replace(tzinfo=ZoneInfo(DEFAULT_TIMEZONE)).astimezone(timezone.utc)


               followup_message = (
                   f"Hi, this is a reminder for {pet_name}. "
                   f"A follow-up consultation was set up at {reminder_date.strftime('%d-%b-%Y')}. "
                   f"To book an appointment call {clinic_name}. "
                   f"- Thank you\n{clinic_name}"
               )
               insert_reminder(followup_message, followup_dt)


       # --- Return response ---
       return JSONResponse({
           "status": True,
           "message": "Report uploaded and reminders scheduled successfully",
           "data": {
               "report_id": report_row["report_id"],
               "doctor_id": report_row["doctor_id"],
               "pet_name": report_row["pet_name"],
               "pet_parent_phone": report_row["pet_parent_phone"],
               "report_pdf_links": json.loads(report_row["report_pdf_link"] or "[]"),
               "report_type": report_row["report_type"] or final_report_type,
               "shareable": True,
               "created_at": report_row["created_at"].isoformat()
           }
       })


   except HTTPException:
       raise
   except Exception as e:
       for url in saved_file_urls:
           local_path = os.path.join(doctor_folder, url.split("/")[-1])
           if os.path.exists(local_path):
               try:
                   os.remove(local_path)
               except:
                   pass
       raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")






def print_all_tables():
   """Prints all tables in the public schema and their rows in a structured way."""
   with engine.connect() as conn:
       # Fetch all table names in the public schema
       result = conn.execute(
           text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
       )
       tables = [row[0] for row in result]


       print("\n=== Printing all tables in 'public' schema ===\n")


       for table in tables:
           print(f"--- Table: {table} ---")
           try:
               rows = conn.execute(text(f"SELECT * FROM {table};")).fetchall()
               if rows:
                   for row in rows:
                       # row._mapping converts SQLAlchemy row to dict for readable print
                       print(dict(row._mapping))
               else:
                   print("   (empty)")
           except Exception as e:
               print(f"❌ Error reading table '{table}': {e}")


       print("\n=== End of tables ===\n")






print_all_tables()


@app.get("/doctor_reports/{doctor_id}")
async def get_doctor_reports(
   doctor_id: int,
   page: int = Query(1, ge=1),
   limit: int = Query(50, ge=1, le=500),
   search: str | None = Query(None, description="Search pet name or owner phone"),
   start_date: str | None = Query(None, description="YYYY-MM-DD"),
   end_date: str | None = Query(None, description="YYYY-MM-DD"),
):
   try:
       offset = (page - 1) * limit


       base_sql = """
           SELECT report_id, doctor_id, pet_name, pet_parent_phone,
                  reminder, report_pdf_link, report_type, created_at
           FROM Reports
           WHERE doctor_id = :doctor_id
       """
       params = {"doctor_id": doctor_id}


       # Date filters
       if start_date:
           try:
               date.fromisoformat(start_date)
           except Exception:
               raise HTTPException(status_code=400, detail="start_date must be YYYY-MM-DD")
           base_sql += " AND DATE(reminder) >= :start_date"
           params["start_date"] = start_date


       if end_date:
           try:
               date.fromisoformat(end_date)
           except Exception:
               raise HTTPException(status_code=400, detail="end_date must be YYYY-MM-DD")
           base_sql += " AND DATE(reminder) <= :end_date"
           params["end_date"] = end_date


       # Search filters
       if search:
           base_sql += " AND (LOWER(COALESCE(pet_name,'')) LIKE :search OR COALESCE(pet_parent_phone,'') LIKE :search_raw)"
           params["search"] = f"%{search.lower()}%"
           params["search_raw"] = f"%{search}%"


       # Ordering + pagination
       base_sql += " ORDER BY created_at DESC NULLS LAST, report_id DESC LIMIT :limit OFFSET :offset"
       params["limit"] = limit
       params["offset"] = offset


       with engine.begin() as conn:
           rows = conn.execute(text(base_sql), params).mappings().all()


       reports = []
       for r in rows:
           rec = dict(r)


           # parse report_pdf_link
           links = []
           raw = rec.get("report_pdf_link")
           if raw:
               if isinstance(raw, (list, tuple)):
                   links = list(raw)
               elif isinstance(raw, str):
                   try:
                       parsed = json.loads(raw)
                       if isinstance(parsed, list):
                           links = parsed
                       elif isinstance(parsed, str):
                           links = [parsed]
                       else:
                           links = []
                   except Exception:
                       links = [raw]


           # reminder
           rem = rec.get("reminder")
           if isinstance(rem, (date, datetime)):
               reminder_iso = rem.isoformat()
           else:
               reminder_iso = str(rem) if rem else None


           # created_at
           created = rec.get("created_at")
           if isinstance(created, (date, datetime)):
               created_iso = created.isoformat()
           else:
               created_iso = str(created) if created else None


           # doctor bypass link (no password needed)
           protected_link = f"https://401a8ca5585e.ngrok-free.app/view_report/{rec['report_id']}?vet=true"


           reports.append({
               "report_id": rec.get("report_id"),
               "doctor_id": rec.get("doctor_id"),
               "pet_name": rec.get("pet_name"),
               "pet_parent_phone": rec.get("pet_parent_phone"),
               "reminder": reminder_iso,
               "report_pdf_links": links,   # raw file(s)
               "report_type": rec.get("report_type") or "Unknown",
               "created_at": created_iso,
               "protected_link": protected_link  # 🔑 bypass password for doctor
           })


       return JSONResponse({
           "status": True,
           "reports": reports,
           "page": page,
           "limit": limit,
           "count": len(reports)
       })


   except HTTPException:
       raise
   except Exception as e:
       print("ERROR in get_doctor_reports:", str(e))
       raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")




@app.get("/view_report/{report_id}", response_class=HTMLResponse)
async def view_report_form(report_id: int):
   html_content = f"""
   <html>
   <head>
       <title>View Report</title>
       <style>
           body {{
               font-family: Arial, sans-serif;
               background-color: #f7f7f7;
               display: flex;
               justify-content: center;
               align-items: center;
               min-height: 100vh;
               margin: 0;
           }}
           .container {{
               background-color: #fff;
               padding: 30px;
               border-radius: 10px;
               box-shadow: 0 4px 10px rgba(0,0,0,0.1);
               width: 90%;
               max-width: 500px;
               text-align: center;
           }}
           input[type="password"] {{
               padding: 10px;
               width: 80%;
               margin-bottom: 20px;
               border-radius: 5px;
               border: 1px solid #ccc;
               font-size: 16px;
           }}
           button {{
               padding: 10px 20px;
               background-color: #007bff;
               color: #fff;
               border: none;
               border-radius: 5px;
               cursor: pointer;
               font-size: 16px;
           }}
           button:hover {{
               background-color: #0056b3;
           }}
           h2 {{
               color: #333;
           }}
       </style>
   </head>
   <body>
       <div class="container">
           <h2>Enter last 4 digits of your phone to view the report</h2>
           <form action="/view_report/{report_id}" method="post">
               <input type="password" name="password" maxlength="4" required>
               <br>
               <button type="submit">View Report</button>
           </form>
       </div>
   </body>
   </html>
   """
   return HTMLResponse(content=html_content)




# Simulated vet check (replace with your actual vet auth/session logic)
def current_user_is_vet(vet: bool = False):
   return vet  # Replace with your real auth


@app.get("/view_report/{report_id}", response_class=HTMLResponse)
async def view_report_form(report_id: int, vet: bool = False):
   if current_user_is_vet(vet):
       return await view_report_submit(report_id, password=None, vet=True)


   html_content = f"""
   <html>
     <head>
       <meta name="viewport" content="width=device-width, initial-scale=1" />
       <style>
         :root {{
           --maxWidth: min(1000px, 96vw);
           --viewerHeight: clamp(70vh, 85vh, 92vh);
         }}
         body {{
           font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
           background: #0b1320;
           color: #e9eef6;
           margin: 0;
           padding: 48px 16px;
           display: grid;
           place-items: start center;
           gap: 16px;
         }}
         .card {{
           width: var(--maxWidth);
           background: #121a2b;
           border: 1px solid #22314f;
           border-radius: 14px;
           box-shadow: 0 8px 24px rgba(0,0,0,.35);
           padding: 24px;
         }}
         h2 {{ margin: 0 0 16px; font-weight: 600; }}
         form {{
           display: flex; gap: 12px; justify-content: center; margin-top: 8px;
         }}
         input[type=password] {{
           background: #0f1625; color: #e9eef6; border: 1px solid #314469;
           padding: 10px 12px; border-radius: 10px; font-size: 16px; width: 160px;
         }}
         button {{
           background: #3b82f6; color: white; border: none; border-radius: 10px;
           padding: 10px 16px; font-size: 16px; cursor: pointer;
         }}
         button:hover {{ filter: brightness(1.05); }}
       </style>
     </head>
     <body>
       <div class="card">
         <h2>Enter last 4 digits of your phone to view the report</h2>
         <form action="/view_report/{report_id}" method="post">
           <input type="password" name="password" maxlength="4" required />
           <button type="submit">View Report</button>
         </form>
       </div>
     </body>
   </html>
   """
   return HTMLResponse(content=html_content)




@app.post("/view_report/{report_id}", response_class=HTMLResponse)
async def view_report_submit(report_id: int, password: str = Form(None), vet: bool = False):
   with engine.begin() as conn:
       row = conn.execute(
           text("SELECT report_pdf_link, share_password FROM Reports WHERE report_id = :rid"),
           {"rid": report_id}
       ).mappings().fetchone()


   if not row:
       return HTMLResponse("<h3>Report not found.</h3>")


   if not current_user_is_vet(vet) and password != row["share_password"]:
       return HTMLResponse(f"""
           <html><body style="font-family: Arial; padding: 32px; text-align:center;">
             <h3>Incorrect password. Try again.</h3>
             <a href="/view_report/{report_id}">Go back</a>
           </body></html>
       """)


   links = json.loads(row["report_pdf_link"] or "[]")


   # Helper: add viewer hints to PDFs so they fit width and hide toolbar (where supported)
   def pdf_view_url(u: str) -> str:
       frag = "#toolbar=0&navpanes=0&scrollbar=0&zoom=page-width"
       return u + (frag if "#" not in u else "&zoom=page-width")


   html = """
   <html>
     <head>
       <meta name="viewport" content="width=device-width, initial-scale=1" />
       <style>
         :root {
           --maxWidth: min(1100px, 96vw);
           --viewerHeight: clamp(70vh, 85vh, 92vh);
         }
         body {
           font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
           background: #0b1320;
           color: #e9eef6;
           margin: 0;
           padding: 24px 12px 48px;
           display: grid;
           place-items: start center;
           gap: 20px;
         }
         .wrap { width: var(--maxWidth); display: grid; gap: 20px; }
         .head { display:flex; align-items:center; justify-content:space-between; }
         .tile {
           background:#0f1625; border:1px solid #22314f; border-radius:14px;
           box-shadow: 0 8px 24px rgba(0,0,0,.35); padding:16px;
         }
         .pdfFrame, .imgEl {
           width: 100%; height: var(--viewerHeight); border: none; border-radius: 12px;
           background: #0a0f1c;
         }
         .imgEl { height: auto; max-height: var(--viewerHeight); object-fit: contain; }
         .meta { display:flex; gap:12px; align-items:center; margin-top:12px; }
         .btn {
           display:inline-block; padding:8px 12px; border-radius:10px; text-decoration:none;
           background:#22314f; color:#cfe1ff; border:1px solid #314469;
         }
         .btn:hover { filter: brightness(1.08); }
       </style>
     </head>
     <body>
       <div class="wrap">
         <div class="head">
           <h2 style="margin:0;">Your Report(s)</h2>
         </div>
   """


   for i, link in enumerate(links, start=1):
       if link.lower().endswith(".pdf"):
           view_url = pdf_view_url(link)
           html += f"""
             <div class="tile">
               <iframe class="pdfFrame" src="{view_url}" allow="fullscreen"></iframe>
               <div class="meta">
                 <a class="btn" href="{link}" target="_blank" rel="noopener">Open in new tab</a>
                 <a class="btn" href="{link}" download>Download PDF</a>
               </div>
             </div>
           """
       else:
           html += f"""
             <div class="tile">
               <img class="imgEl" src="{link}" alt="Report image {i}" />
               <div class="meta">
                 <a class="btn" href="{link}" target="_blank" rel="noopener">Open full size</a>
                 <a class="btn" href="{link}" download>Download Image</a>
               </div>
             </div>
           """


   html += """
       </div>
     </body>
   </html>
   """


   return HTMLResponse(html)




if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)

