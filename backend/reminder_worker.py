"""
reminders_worker.py

Standalone scheduler worker for Purry Tails — Option 2 (run separately from your FastAPI app).

- Runs daily at 08:30 (Asia/Kolkata)
- Picks Reminders scheduled for "tomorrow" (computed in REMINDER_TZ)
- Sends WhatsApp template messages via Meta Graph API v20.0
- Uses Postgres row-locking (FOR UPDATE SKIP LOCKED) to avoid duplicates when multiple workers run
- Respects attempts / max_attempts and updates status to 'sent' or 'failed'

USAGE (dev):
    REMINDER_TZ=Asia/Kolkata \
    DATABASE_URL=postgresql://user:pass@host:5432/dbname \
    WHATSAPP_PHONE_NUMBER_ID=756800504184567 \
    WHATSAPP_ACCESS_TOKEN=EAA...your_token... \
    python reminders_worker.py

In production, run this as a separate process (systemd, docker-compose, k8s Job, etc.).

Note: Do NOT hardcode production tokens. Use env vars or a secret manager.
"""

import os
import logging
from datetime import datetime, timedelta, time as dtime
import time
import pytz
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ---------- Logging ----------
LOG = logging.getLogger("reminders_worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------- Config (from env) ----------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://darsh:Darsh123@localhost:5432/vetapp")

#WH_PHONE_ID = "756800504184567"
#WH_TOKEN = "EAAZAoZAtAUH6wBPGA9CHiBAhpd3uAxkw1hTobWORnvxiQ5ejrZAjMVprvgzzkzRgqavoRQsxrr1JxHAbiPnjhBU4STLvM1IqdhqCZBZCfnqkVRHnaQToYG2C0OiEaBJsJH5aAfUgtf4lPm62QX43kPn74nEEqcBO9LhLQPx25bkZAKd7p1z0ZBMDQHzSzirHG05emNnxSmRW1AE55VZAuA9t2GajJQXxx19EF96D"
#BASE_URL = f"https://graph.facebook.com/v20.0/{WH_PHONE_ID}/messages"
TZ_NAME = os.getenv("REMINDER_TZ", "Asia/Kolkata")
TZ = pytz.timezone(TZ_NAME)

if not DATABASE_URL:
    LOG.error("DATABASE_URL is not set. Exiting.")
    raise SystemExit(1)


# ---------- DB ----------
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

# ---------- Helpers ----------

def _normalize(phone: str) -> str:
    if not phone:
        return ""
    return "".join(ch for ch in phone if ch.isdigit())


def send_whatsapp_template(phone: str, template_name: str, lang: str, params: list, whatsapp_token: str, whatsapp_number_id: str) -> tuple:
    """Send a WhatsApp template message via Graph API v20.0.
    Returns: (ok: bool, status_code: int, text: str)
    """
    to = _normalize(phone)
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
            "components": [
                {"type": "body", "parameters": [{"type": "text", "text": p} for p in params]}
            ]
        }
    }
    headers = {"Authorization": f"Bearer {whatsapp_token}", "Content-Type": "application/json"}
    try:
        BASE_URL = f"https://graph.facebook.com/v20.0/{whatsapp_number_id}/messages"
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=15)
        LOG.debug("WhatsApp response: %s %s", resp.status_code, resp.text[:500])
        return resp.ok, resp.status_code, resp.text
    except Exception as e:
        LOG.exception("Exception sending whatsapp template")
        return False, 0, str(e)


# ---------- Core processing ----------

def process_batch(limit: int = 500):
    session = Session()

    now_k = datetime.now(TZ)
    target = (now_k + timedelta(days=1)).date()  # reminders for tomorrow (in reminder tz)

    # define start and end of target day in TZ and convert to UTC for DB comparison
    start_k = TZ.localize(datetime.combine(target, dtime.min)).astimezone(pytz.UTC)
    end_k = TZ.localize(datetime.combine(target, dtime.max)).astimezone(pytz.UTC)

    LOG.info("Picking reminders for %s (local range %s - %s) -> UTC %s - %s", target, 
             TZ.localize(datetime.combine(target, dtime.min)), TZ.localize(datetime.combine(target, dtime.max)),
             start_k, end_k)

    # Fetch a locked batch using Postgres FOR UPDATE SKIP LOCKED pattern
    try:
        rows = session.execute(text("""
            WITH c AS (
                SELECT reminder_id FROM Reminders
                WHERE active = true
                  AND status = 'pending'
                  AND reminder_at >= :s AND reminder_at <= :e
                ORDER BY reminder_id
                FOR UPDATE SKIP LOCKED
                LIMIT :lim
            )
            SELECT r.* FROM Reminders r JOIN c ON r.reminder_id = c.reminder_id
        """), {"s": start_k, "e": end_k, "lim": limit}).fetchall()

        LOG.info("Locked %d reminders for processing", len(rows))

        for r in rows:
            try:
                reminder_id = r.reminder_id
                doctor_id = r.doctor_id   # <-- Fetch doctor_id here
                phone = r.pet_parent_phone
                pet = (r.pet_name or "").strip()
                clinic = (r.clinic_name or "").strip()
                rem_dt = r.reminder_at
                date_str = rem_dt.astimezone(TZ).strftime("%d-%b-%Y")
                metadata = r.metadata or {}
                template_name = "upcoming_clinic_visit"
                lang = metadata.get("whatsapp_language", "en")

                if not template_name:
                    LOG.warning("Reminder %s missing template_name in metadata — marking failed", reminder_id)
                    session.execute(text("UPDATE Reminders SET status='failed', updated_at=now() WHERE reminder_id=:id"), {"id": reminder_id})
                    session.commit()
                    continue

                # determine params: prefer explicit whatsapp_template_params, else default mapping
                params = metadata.get("whatsapp_template_params")
                if not isinstance(params, list):
                    params = [pet, date_str, clinic]
                
                doctor_row = session.execute(
                    text("SELECT whatsapp_access_token, whatsapp_number_id FROM Doctor WHERE doctor_id = :did"),
                    {"did": doctor_id}
                ).mappings().fetchone()
                whatsapp_token = doctor_row["whatsapp_access_token"] if doctor_row else None
                whatsapp_number_id = doctor_row["whatsapp_number_id"] if doctor_row else None
                print("WhatsApp Access = ", whatsapp_token)
                print("WhatsApp Token = ", whatsapp_number_id)

                ok, code, body = send_whatsapp_template(phone, template_name, lang, params, whatsapp_token, whatsapp_number_id)

                if ok:
                    session.execute(text("UPDATE Reminders SET status='sent', attempts = coalesce(attempts,0)+1, last_attempt_at=now(), updated_at=now() WHERE reminder_id=:id"), {"id": reminder_id})
                    LOG.info("Reminder %s sent (phone=%s)", reminder_id, phone)
                else:
                    session.execute(text("UPDATE Reminders SET attempts = coalesce(attempts,0)+1, last_attempt_at=now(), status = CASE WHEN coalesce(attempts,0)+1 >= coalesce(max_attempts,3) THEN 'failed' ELSE 'pending' END, updated_at=now() WHERE reminder_id=:id"), {"id": reminder_id})
                    LOG.warning("Reminder %s failed to send (http=%s) body=%s", reminder_id, code, body[:300])

                session.commit()

            except Exception:
                LOG.exception("Error processing reminder %s", r.reminder_id)
                session.rollback()

    except Exception:
        LOG.exception("Failed to fetch reminders batch")
    finally:
        session.close()


# ---------- Scheduler ----------

def job():
    LOG.info("Reminder job started")
    process_batch(limit=500)
    LOG.info("Reminder job finished")


def start_scheduler():
    sched = BlockingScheduler(timezone=TZ)
    # Daily at 08:30 local TZ
    sched.add_job(job, "cron", hour=11, minute=52, id="daily_reminders",
              replace_existing=True, misfire_grace_time=60)
    LOG.info("Starting scheduler (daily 11:52 %s)", TZ_NAME)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        LOG.info("Scheduler stopped")


if __name__ == "__main__":
    # quick sanity check
    LOG.info("reminders_worker starting (TZ=%s)", TZ_NAME)
    start_scheduler()
