from fastapi import FastAPI, File, Form, Query, UploadFile, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Form
from fastapi.responses import PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
import ast
import uuid
from datetime import date, datetime, timedelta, timezone, time
import os
from dotenv import load_dotenv
import re
from sqlalchemy import create_engine, text
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
import requests
import json
import requests
import logging
from urllib.parse import quote
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, time as dtime
import pytz
from fastapi import Depends
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import uvicorn

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
print(DATABASE_URL)


with engine.connect() as conn:
   result = conn.execute(text("SELECT NOW()"))
   print("Connected to DB! Current time:", result.scalar())


app = FastAPI()



FRONTEND_URL = os.getenv("FRONTEND_URL")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # production frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)


class CustomMiddleware(BaseHTTPMiddleware):
   async def dispatch(self, request, call_next):
       response = await call_next(request)
       response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
       response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
       return response


app.add_middleware(CustomMiddleware)


class UserResponse(BaseModel):
   user_id: str
   email: str
   name: str
   phone_number: str
   owner_address: str




from sqlalchemy import text


def init_db():
   with engine.begin() as conn:

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
       conn.execute(text("""ALTER TABLE Reminders ADD COLUMN IF NOT EXISTS doctor_name TEXT NULL;"""))
       print("Added Reminders Table - Doctor Name Successfully")


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
       conn.execute(text("""
       CREATE TABLE IF NOT EXISTS AdminUsers (
        admin_id     BIGSERIAL PRIMARY KEY,
        admin_email  VARCHAR(255) UNIQUE NOT NULL,
        admin_name   TEXT,
        active       BOOLEAN NOT NULL DEFAULT TRUE,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        );

       
       """))
       print("Even Admin Table Added")
       conn.execute(text("""
       CREATE TABLE IF NOT EXISTS AllowedDoctors (
            doctor_id     BIGSERIAL PRIMARY KEY,
            doctor_email  VARCHAR(255) UNIQUE NOT NULL,
            active        BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
       );
       """))
       print("✅ AllowedDoctors table ensured")

       


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



class AdminLoginModel(BaseModel):
    email: EmailStr
    name: str = None

@app.post("/admin_login")
async def admin_login(data: AdminLoginModel):
    print("Received admin login request for email:", data.email)
    try:
        with engine.begin() as conn:
            # Check if admin already exists
            result = conn.execute(
                text("SELECT * FROM AdminUsers WHERE admin_email = :email"),
                {"email": data.email}
            ).mappings().fetchone()

            if result:
                print("Admin exists in DB:", result["admin_id"], result["admin_email"])
                return {
                    "status": True,
                    "message": "Login Successful",
                    "data": {
                        "admin_id": result["admin_id"],
                        "email": result["admin_email"],
                        "name": result["admin_name"],
                    },
                }

            else:
                # Restrict registration → only allow whitelisted emails
                ALLOWED_ADMINS = {"darshthakkar09@gmail.com", "your@ivanatech.com"}
                if data.email not in ALLOWED_ADMINS:
                    raise HTTPException(
                        status_code=403,
                        detail={"status": False, "message": "Unauthorized admin email"},
                    )

                print("Admin not found, registering new admin:", data.email)
                insert_result = conn.execute(
                    text("""
                        INSERT INTO AdminUsers (admin_email, admin_name)
                        VALUES (:email, :name)
                        RETURNING admin_id, admin_email, admin_name
                    """),
                    {"email": data.email, "name": data.name}
                ).mappings().fetchone()

                print("New admin registered with ID:", insert_result["admin_id"])
                return {
                    "status": True,
                    "message": "Admin Registered Successfully",
                    "data": {
                        "admin_id": insert_result["admin_id"],
                        "email": insert_result["admin_email"],
                        "name": insert_result["admin_name"],
                    },
                }

    except Exception as e:
        print("Error during admin login:", str(e))
        raise HTTPException(
            status_code=500,
            detail={"status": False, "message": f"Failed to process request: {str(e)}"},
        )


SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")  # 🔑 keep secret in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




class GoogleLoginModel(BaseModel):
   email: EmailStr
   name: str = None
   clinic_name: str = None

@app.post("/doctor_login")
async def doctor_login(data: GoogleLoginModel):
    print("Received login request for email:", data.email)
    try:
        with engine.begin() as conn:

            # ✅ Step 1: Check if email is in AllowedDoctors
            allowed = conn.execute(
                text("SELECT * FROM AllowedDoctors WHERE doctor_email = :email AND active = TRUE"),
                {"email": data.email}
            ).mappings().fetchone()

            if not allowed:
                print("❌ Doctor not in AllowedDoctors list:", data.email)
                raise HTTPException(
                    status_code=403,
                    detail={"status": False, "message": "You are not authorized to log in. Please contact admin."},
                )

            # ✅ Step 2: Check if doctor already exists
            result = conn.execute(
                text("SELECT * FROM Doctor WHERE doctor_email = :email"),
                {"email": data.email}
            ).mappings().fetchone()

            if result:
                print("Doctor exists in DB:", result["doctor_id"], result["doctor_email"])

                # 🔑 Create JWT
                access_token = create_access_token(
                    data={"sub": str(result["doctor_id"]), "email": result["doctor_email"], "role": "doctor"},
                    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                )

                return {
                    "status": True,
                    "message": "Login Successful",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "data": {
                        "doctor_id": result["doctor_id"],
                        "email": result["doctor_email"],
                        "name": result["doctor_name"],
                        "clinic_name": result["clinic_name"]
                    },
                }

            else:
                print("Doctor not found, registering new doctor:", data.email)

                insert_result = conn.execute(
                    text("""
                        INSERT INTO Doctor (doctor_email, doctor_name, clinic_name)
                        VALUES (:email, :name, :clinic_name)
                        RETURNING doctor_id, doctor_email, doctor_name, clinic_name
                    """),
                    {"email": data.email, "name": data.name, "clinic_name": data.clinic_name}
                ).mappings().fetchone()

                print("✅ New doctor registered with ID:", insert_result["doctor_id"])

                # 🔑 Create JWT for new doctor
                access_token = create_access_token(
                    data={"sub": str(insert_result["doctor_id"]), "email": insert_result["doctor_email"], "role": "doctor"},
                    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                )

                return {
                    "status": True,
                    "message": "Registration Successful",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "data": {
                        "doctor_id": insert_result["doctor_id"],
                        "email": insert_result["doctor_email"],
                        "name": insert_result["doctor_name"],
                        "clinic_name": insert_result["clinic_name"]
                    },
                }

    except HTTPException as e:
        raise e
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

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/doctor_upload")
async def doctor_upload_file(credentials: HTTPAuthorizationCredentials = Depends(security)):
    access_token = credentials.credentials  # This is the token sent from frontend
    print("📥 Received Access Token:", access_token)
    
    # For now just return it back to confirm
    return {"received_token": access_token}

def get_current_doctor(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    print(token)
    try:
        print("inside try")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("payload")
        return {
            "doctor_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/doctor_upload_file")
async def doctor_upload_file(
   request: Request,
   files: List[UploadFile] = File(...),
   user_id: str = Form(...),
   pet_parent_phone: str = Form(...),
   pet_name: str = Form(...),
   reminder: Optional[str] = Form(None),
   report_type: Optional[str] = Form(None),
   current_doctor: dict = Depends(get_current_doctor),
):
   print("📥 Received doctor_upload_file request")
   if str(current_doctor["doctor_id"]) != str(user_id):
    raise HTTPException(status_code=403, detail="Unauthorized to upload for this user")



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
      
           stored_path = f"{doctor_id}/{unique_name}"  # internal link
           saved_file_urls.append(stored_path)

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
               text("SELECT doctor_name, clinic_name, doctor_phone, whatsapp_access_token, whatsapp_number_id FROM Doctor WHERE doctor_id = :did"),
               {"did": doctor_id}
           ).mappings().fetchone()
           clinic_name = doctor_row["clinic_name"] if doctor_row else "Your Clinic"
           doctor_name =  doctor_row["doctor_name"] if doctor_row else "Doctor"
           doctor_phone_snapshot = doctor_row["doctor_phone"] if doctor_row else None
           whatsapp_token = doctor_row["whatsapp_access_token"] if doctor_row else None
           whatsapp_number_id = doctor_row["whatsapp_number_id"] if doctor_row else None


           # --- Function to insert reminder ---
           def insert_reminder(message: str, reminder_at: datetime):
               insert_sql = text("""
                   INSERT INTO Reminders
                   (doctor_id, report_id, pet_parent_phone, pet_name, clinic_name, doctor_phone,
                    message_template, channel, reminder_at, timezone, recurrence_type, recurrence_interval,
                    status, attempts, max_attempts, metadata, active, created_by, doctor_name)
                   VALUES
                   (:doctor_id, :report_id, :pet_parent_phone, :pet_name, :clinic_name, :doctor_phone,
                    :message_template, :channel, :reminder_at, :timezone, :recurrence_type, :recurrence_interval,
                    :status, :attempts, :max_attempts, :metadata, :active, :created_by, :doctor_name)
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
                   "created_by": doctor_id,
                   "doctor_name": doctor_name
               }
               return conn.execute(insert_sql, params).mappings().fetchone()

           # --- Immediate WhatsApp reminder ---
           try:
               first_file_url = json.loads(report_row["report_pdf_link"])[0]
               protected_link = f"https://www.purrytails.in/view_report/{report_row['report_id']}"
               # Insert into reminders table
               immediate_message = (
                   f"Hi, Thank you for visiting {clinic_name}. "
                   f"The record is uploaded for {pet_name}. Click the link below to access it:\n{first_file_url}"
               )
               immediate_time = datetime.utcnow().replace(tzinfo=timezone.utc)
               insert_reminder(immediate_message, immediate_time)


               # Send WhatsApp template
               template_name = "pet_report_update_notice"
               parameters = [
                   pet_name,    
                   protected_link,          # {{1}} pet name
                   reminder_date.strftime("%d %b '%y") if reminder_date else "Not set",
                   doctor_name,
                   doctor_phone_snapshot,
                   clinic_name # {{4}} reminder date
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



from itsdangerous import URLSafeTimedSerializer

# --- Signer for secure doctor links ---
SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
SIGNER = URLSafeTimedSerializer(SECRET_KEY)
TOKEN_EXPIRY_SEC = 3600  # 1 hour validity


def generate_doctor_link(report_id: int) -> str:
    token = SIGNER.dumps(report_id)
    return f"https://www.purrytails.in/view_report/{report_id}?token={token}"


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

        # --- Apply date filters ---
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

        # --- Search filters ---
        if search:
            base_sql += " AND (LOWER(COALESCE(pet_name,'')) LIKE :search OR COALESCE(pet_parent_phone,'') LIKE :search_raw)"
            params["search"] = f"%{search.lower()}%"
            params["search_raw"] = f"%{search}%"

        # --- Pagination & ordering ---
        base_sql += " ORDER BY created_at DESC NULLS LAST, report_id DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        with engine.begin() as conn:
            rows = conn.execute(text(base_sql), params).mappings().all()

        reports = []
        for r in rows:
            rec = dict(r)

            # Parse stored report links
            links = []
            raw = rec.get("report_pdf_link")
            if raw:
                try:
                    parsed = json.loads(raw)
                    links = parsed if isinstance(parsed, list) else [parsed]
                except Exception:
                    links = [raw]

            # Reminder
            rem = rec.get("reminder")
            reminder_iso = rem.isoformat() if isinstance(rem, (date, datetime)) else str(rem) if rem else None

            # created_at
            created = rec.get("created_at")
            created_iso = created.isoformat() if isinstance(created, (date, datetime)) else str(created) if created else None

            # --- Secure doctor link ---
            secure_link = generate_doctor_link(rec["report_id"])

            reports.append({
                "report_id": rec.get("report_id"),
                "doctor_id": rec.get("doctor_id"),
                "pet_name": rec.get("pet_name"),
                "pet_parent_phone": rec.get("pet_parent_phone"),
                "reminder": reminder_iso,
                "report_pdf_links": links,
                "report_type": rec.get("report_type") or "Unknown",
                "created_at": created_iso,
                "secure_doctor_link": secure_link  # 🔑 secure, signed URL
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


@app.get("/reminders_today")
async def get_tomorrows_reminders():
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        reminder_id,
                        pet_name,
                        doctor_name,
                        clinic_name,
                        reminder_at,
                        status,
                        active
                    FROM reminders
                    WHERE active = true
                      AND status = 'pending'
                      AND DATE(reminder_at AT TIME ZONE 'Asia/Kolkata') = CURRENT_DATE + INTERVAL '1 day'
                    ORDER BY reminder_at ASC
                """)
            ).mappings().all()

            reminders = [dict(row) for row in result]
            print("📌 Pending reminders for tomorrow:", reminders)

            return reminders

    except Exception as e:
        print("❌ Error fetching tomorrow's reminders:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch reminders")





# -------------------------------
# 2. Get all allowed doctors
# -------------------------------
@app.get("/allowed_doctors")
async def get_allowed_doctors():
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT doctor_id AS id, doctor_email AS email FROM AllowedDoctors WHERE active = TRUE ORDER BY doctor_id ASC")
            ).mappings().all()

            return [dict(row) for row in result]

    except Exception as e:
        print("Error fetching allowed doctors:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch doctors")



@app.post("/allowed_doctors")
async def add_allowed_doctor(data: dict):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO AllowedDoctors (doctor_email, active)
                    VALUES (:email, TRUE)
                    ON CONFLICT (doctor_email) DO UPDATE SET active = TRUE
                    RETURNING doctor_id AS id, doctor_email AS email
                """),
                {"email": email}
            ).mappings().fetchone()

            return dict(result)

    except Exception as e:
        print("Error adding allowed doctor:", str(e))
        raise HTTPException(status_code=500, detail="Failed to add doctor")


# -------------------------------
# 4. Delete allowed doctor
# -------------------------------
@app.delete("/allowed_doctors/{doctor_id}")
async def delete_allowed_doctor(doctor_id: int):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM AllowedDoctors WHERE doctor_id = :id RETURNING doctor_id"),
                {"id": doctor_id}
            ).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Doctor not found")

            return {"status": True, "message": "Doctor removed successfully"}

    except Exception as e:
        print("Error deleting allowed doctor:", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete doctor")

@app.post("/print_tomorrow_reminders")
async def print_tomorrow_reminders():
    tomorrow = date.today() + timedelta(days=1)
    print("Found Toms date")

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM reminders WHERE DATE(reminder_at) = :tomorrow"),
            {"tomorrow": tomorrow}
        ).mappings().all()  # ✅ ensures each row is a dict-like mapping

    print("📌 Tomorrow's reminders:")
    for row in result:
        print(dict(row))  # now this works

    return {"status": "Reminders printed successfully", "count": len(result)}

LOG = logging.getLogger(__name__)

def send_whatsapp(phone: str, template_name: str, lang: str, params: list, whatsapp_token: str, whatsapp_number_id: str) -> tuple:
    """
    Send a WhatsApp template message via Graph API v20.0 or v22.0.
    
    Returns:
        (ok: bool, status_code: int, response_text: str)
    """
    if not whatsapp_token or not whatsapp_number_id:
        LOG.warning("WhatsApp credentials missing for sending message to %s", phone)
        return False, 0, "Missing WhatsApp credentials"

    # Normalize phone number to include country code only
    to = phone.strip()
    if not to.startswith("+"):
        LOG.warning("Phone number should include country code: %s", phone)

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},  # must be string, not list
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(p)} for p in params]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }

    try:
        BASE_URL = f"https://graph.facebook.com/v22.0/{whatsapp_number_id}/messages"
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=15)
        LOG.info("WhatsApp payload sent to %s, status=%s", phone, resp.status_code)
        return resp.ok, resp.status_code, resp.text

    except Exception as e:
        LOG.exception("Exception sending WhatsApp template to %s", phone)
        return False, 0, str(e)


@app.post("/send_tomorrow_reminders")
async def send_tomorrow_reminders():
    session = Session(bind=engine)

    try:
        TZ = pytz.timezone("Asia/Kolkata")
        tomorrow = (datetime.now(TZ) + timedelta(days=1)).date()

        # Start/end of tomorrow in UTC
        start_k = TZ.localize(datetime.combine(tomorrow, dtime.min)).astimezone(pytz.UTC)
        end_k   = TZ.localize(datetime.combine(tomorrow, dtime.max)).astimezone(pytz.UTC)

        # Get all reminders for tomorrow
        rows = session.execute(
            text("""
                SELECT r.*, d.whatsapp_access_token, d.whatsapp_number_id
                FROM Reminders r
                JOIN Doctor d ON r.doctor_id = d.doctor_id
                WHERE r.active = true
                  AND r.status = 'pending'
                  AND r.reminder_at >= :s AND r.reminder_at <= :e
            """),
            {"s": start_k, "e": end_k}
        ).mappings().all()

        print(f"📌 Found {len(rows)} reminders for tomorrow")

        sent_count, failed_count = 0, 0
        for r in rows:
            try:
                phone = r["pet_parent_phone"]
                doctor_name = r["doctor_name"]
                doctor_phone = r["doctor_phone"]
                pet = (r["pet_name"] or "").strip()
                clinic = (r["clinic_name"] or "").strip()
                rem_dt = r["reminder_at"]
                date_str = rem_dt.astimezone(TZ).strftime("%d-%b-%Y")

                metadata = r["metadata"] or {}
                template_name = "followup_appointment_reminder"
                lang = "en"

                params = metadata.get("whatsapp_template_params")
                if not isinstance(params, list):
                    params = [pet, date_str, doctor_name, doctor_phone, clinic]

                whatsapp_token = r["whatsapp_access_token"]
                whatsapp_number_id = r["whatsapp_number_id"]

                ok, code, body = send_whatsapp(
                    phone, template_name, lang, params, whatsapp_token, whatsapp_number_id
                )

                if ok:
                    sent_count += 1
                    session.execute(
                        text("UPDATE Reminders SET status='sent', attempts=attempts+1, last_attempt_at=now(), updated_at=now() WHERE reminder_id=:id"),
                        {"id": r["reminder_id"]}
                    )
                else:
                    failed_count += 1
                    session.execute(
                        text("""
                            UPDATE Reminders
                            SET attempts = attempts+1,
                                last_attempt_at=now(),
                                status = CASE WHEN attempts+1 >= max_attempts THEN 'failed' ELSE 'pending' END,
                                updated_at=now()
                            WHERE reminder_id=:id
                        """),
                        {"id": r["reminder_id"]}
                    )
                session.commit()

            except Exception as e:
                print("⚠️ Error processing reminder:", r["reminder_id"], e)
                session.rollback()

        return {
            "status": "done",
            "sent": sent_count,
            "failed": failed_count,
            "total": len(rows)
        }

    except Exception as e:
        print("❌ Error fetching reminders:", str(e))
        raise HTTPException(status_code=500, detail="Failed to send reminders")
    finally:
        session.close()


UPLOAD_ROOT = "uploads"
REPORTS_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "reports")
os.makedirs(REPORTS_UPLOAD_DIR, exist_ok=True)


# Simulated vet check (replace with your actual auth/session logic)
def current_user_is_vet(vet: bool = False):
    return vet  # Replace with real auth/session check


# GET: Show password page
@app.get("/view_report/{report_id}", response_class=HTMLResponse)
async def view_report_form(report_id: int, vet: bool = False):
    if current_user_is_vet(vet):
        return await view_report_submit(report_id, password=None, vet=True)

    html_content = f"""
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          body {{ font-family: system-ui; background: #0b1320; color: #e9eef6; margin:0; padding:48px 16px; display:grid; place-items:center; }}
          .card {{ width: min(1000px, 96vw); background:#121a2b; border:1px solid #22314f; border-radius:14px; padding:24px; box-shadow:0 8px 24px rgba(0,0,0,.35); }}
          input[type=password] {{ background:#0f1625; color:#e9eef6; border:1px solid #314469; padding:10px 12px; border-radius:10px; width:160px; font-size:16px; }}
          button {{ background:#3b82f6; color:white; border:none; border-radius:10px; padding:10px 16px; cursor:pointer; }}
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

# POST: Verify password & show report
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
    html = """
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          :root {
            --maxWidth: min(1100px,96vw);
            --viewerHeight: 80vh;
            --cardBg: #f5f5f5; /* light neutral background for tiles */
            --textColor: #0b1320;
          }

          body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #e9eef6;
            color: var(--textColor);
            margin:0; padding:24px 12px 48px;
            display:flex; flex-direction:column; align-items:center; gap:20px;
          }

          h2 {
            font-size: 2rem;
            text-align: center;
            margin-bottom:16px;
            color: #0b1320;
          }

          .wrap {
            width: var(--maxWidth);
            display:grid;
            gap:24px;
          }

          .tile {
            background: var(--cardBg);
            border:1px solid #d1d5db;
            border-radius:12px;
            padding:16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
          }

          /* PDF styling */
          .pdfFrame {
            width: 100%;
            height: 80vh;
            border: none;
            border-radius: 8px;
          }

          /* Image styling */
          .imgEl {
            width: 100%;
            max-height: 80vh;
            object-fit: contain;
            border-radius: 8px;
          }

          .meta {
            display:flex;
            gap:12px;
            align-items:center;
            margin-top:12px;
          }

          .btn {
            display:inline-block;
            padding:8px 16px;
            border-radius:8px;
            text-decoration:none;
            font-weight:500;
            background:#3b82f6;
            color:white;
            border:1px solid #3b82f6;
            transition: all 0.2s ease;
          }

          .btn:hover {
            background:#2563eb;
            border-color:#2563eb;
          }

          @media(max-width:768px) {
            :root { --viewerHeight: 50vh; }
            h2 { font-size: 1.6rem; }
          }
        </style>
      </head>
      <body>
        <div class="wrap">
          <h2>Your Report(s)</h2>
    """

    # Serve files via /report_file/{file_name}
    for i, file_name in enumerate(links, start=1):
        secure_url = f"/report_file/{file_name}?password={password}"

        if file_name.lower().endswith(".pdf"):
            html += f"""
            <div class="tile">
              <iframe class="pdfFrame" src="{secure_url}" allowfullscreen></iframe>
              <div class="meta">
                <a class="btn" href="{secure_url}" target="_blank" rel="noopener">Open in new tab</a>
                <a class="btn" href="{secure_url}" download>Download PDF</a>
              </div>
            </div>
            """
        else:
            html += f"""
            <div class="tile">
              <img class="imgEl" src="{secure_url}" alt="Report image {i}" />
              <div class="meta">
                <a class="btn" href="{secure_url}" target="_blank" rel="noopener">Open full size</a>
                <a class="btn" href="{secure_url}" download>Download Image</a>
              </div>
            </div>
            """

    html += "</div></body></html>"
    return HTMLResponse(html)


# Serve actual report files
@app.get("/report_file/{file_name:path}")
async def serve_report_file(file_name: str, password: str = None):
    # Extract report_id from the first folder in the path
    report_id_part = int(file_name.split("/")[0])

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT report_pdf_link, share_password FROM Reports WHERE report_id = :rid"),
            {"rid": report_id_part}
        ).mappings().fetchone()

    if not row:
        return HTMLResponse("<h3>File not found.</h3>")

    if password != row["share_password"]:
        return HTMLResponse("<h3>Unauthorized access.</h3>")

    file_path = Path(REPORTS_UPLOAD_DIR) / file_name
    if not file_path.exists():
        return HTMLResponse(f"<h3>File not found on server: {file_path}</h3>")

    return FileResponse(file_path)





if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)

