"""
diag_email_failures.py  —  show why emails are failing + test SMTP live
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
from app.config import settings
from app.models.email import EmailLog, EmailContact
from app.database import SessionLocal
from dotenv import load_dotenv
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()


db = SessionLocal()

total_failed = db.query(EmailLog).filter(EmailLog.status == "failed").count()
total_sent = db.query(EmailLog).filter(EmailLog.status == "sent").count()
total_pend = db.query(EmailLog).filter(EmailLog.status == "pending").count()
print(f"\n── Email Log Summary ─────────────────────────")
print(f"  sent:    {total_sent}")
print(f"  failed:  {total_failed}")
print(f"  pending: {total_pend}")

# Top failure reasons
print(f"\n── Top Failure Reasons ───────────────────────")
logs = db.query(EmailLog).filter(EmailLog.status == "failed").limit(200).all()
seen: dict = {}
for l in logs:
    err = (l.error_message or "no error stored")[:160]
    seen[err] = seen.get(err, 0) + 1
for msg, cnt in sorted(seen.items(), key=lambda x: -x[1]):
    print(f"  [x{cnt:>3}]  {msg}")

# Sample of bad email addresses
print(f"\n── Sample Contact Emails (first 20) ─────────")
contacts = db.query(EmailContact).limit(20).all()
for c in contacts:
    print(f"  {c.email}")

db.close()

# ── Live SMTP test ────────────────────────────────────────────────────────────
print(f"\n── Live SMTP Test ────────────────────────────")
print(f"  host:  {settings.SMTP_HOST}:{settings.SMTP_PORT}")
print(f"  user:  {settings.SMTP_USERNAME}")
print(f"  from:  {settings.SMTP_FROM_EMAIL}")
print(f"  pass_len (stripped): {len(settings.SMTP_PASSWORD.replace(' ', ''))}")


async def test_smtp():
    import ssl
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "JobRadar SMTP Test"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = settings.SMTP_FROM_EMAIL   # send to self
    msg.attach(MIMEText(
        "JobRadar SMTP test — if you see this, Gmail is working!", "plain", "utf-8"))
    port = settings.SMTP_PORT
    use_tls = port == 465
    tls_ctx = ssl.create_default_context() if use_tls else None
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=port,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD.replace(" ", ""),
            use_tls=use_tls,
            start_tls=(port == 587),
            tls_context=tls_ctx,
        )
        print("  RESULT: SUCCESS — email delivered to", settings.SMTP_FROM_EMAIL)
    except Exception as exc:
        print(f"  RESULT: FAILED — {exc}")

asyncio.run(test_smtp())
