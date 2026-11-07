# -*- coding: utf-8 -*-
"""
FZCORE STUDIO - Autonomous Cloud SMTP Dispatcher
Runs 100% on GitHub Actions Cloud Runners (Zero PC Dependency).
Connects to Hostinger SMTP SSL (Port 465) across 48 quarantined mailboxes.
Pacing: 18-35s humanized anti-spam jitter.
"""

import os
import sys
import json
import time
import ssl
import random
import ftplib
import io
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

FTP_HOST = os.environ.get("FTP_SERVER", "82.197.83.123")
FTP_USER = os.environ.get("FTP_USERNAME", "u476907848")
FTP_PASS = os.environ.get("FTP_PASSWORD", "")
SUBDOMAIN_MAIL_PASS = os.environ.get("SUBDOMAIN_MAIL_PASS", "")

SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465

TZ_MAP = {
    # Eastern (UTC-4 / UTC-5)
    'FL': -5, 'GA': -5, 'NY': -5, 'NC': -5, 'SC': -5, 'VA': -5,
    'PA': -5, 'OH': -5, 'MI': -5, 'NJ': -5, 'MA': -5, 'MD': -5,
    'DC': -5, 'CT': -5, 'DE': -5, 'ON': -5, 'QC': -5,
    # Central (UTC-6)
    'TX': -6, 'IL': -6, 'TN': -6, 'MO': -6, 'MN': -6, 'WI': -6,
    'IN': -6, 'AL': -6, 'LA': -6, 'KY': -6, 'OK': -6, 'KS': -6,
    'IA': -6, 'AR': -6, 'MS': -6, 'NE': -6,
    # Mountain (UTC-7)
    'CO': -7, 'AZ': -7, 'UT': -7, 'NV': -7, 'NM': -7, 'ID': -7,
    # Pacific (UTC-8)
    'CA': -8, 'WA': -8, 'OR': -8, 'BC': -8
}

def is_golden_window(state_str):
    offset = TZ_MAP.get(str(state_str).upper().strip(), -5) # Default Eastern
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    local_hour = (utc_now.hour + offset) % 24
    local_min = utc_now.minute
    # Contractor active window: 7:15 AM to 5:45 PM local
    time_float = local_hour + (local_min / 60.0)
    return 7.25 <= time_float <= 17.75

def run_cloud_dispatch(batch_size=50, is_surge=False):
    print("=" * 75)
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] FZCORE Autonomous Cloud SMTP Dispatcher")
    print(f"Batch Size: {batch_size} | Mode: {'SURGE (All Timezones)' if is_surge else 'Daylight Golden Window'}")
    print("=" * 75)

    if not FTP_PASS or not SUBDOMAIN_MAIL_PASS:
        print("[!] ERROR: Missing FTP_PASSWORD or SUBDOMAIN_MAIL_PASS in environment secrets.")
        sys.exit(1)

    # 1. Connect to Hostinger FTP & Fetch Vault Data
    print("[*] Connecting to Hostinger FTP to fetch vault and ledgers...")
    ftp = ftplib.FTP(FTP_HOST, timeout=30)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.set_pasv(True)

    def read_ftp_json(path):
        bio = io.BytesIO()
        try:
            ftp.retrbinary(f"RETR {path}", bio.write)
            return json.loads(bio.getvalue().decode('utf-8'))
        except Exception as e:
            print(f"[!] Notice: Could not read {path}: {e}")
            return {}

    approved_pitches = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/approved_pitches.json")
    if isinstance(approved_pitches, dict):
        approved_pitches = list(approved_pitches.values())
    if not isinstance(approved_pitches, list):
        approved_pitches = []

    sent_ledger = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/sent_ledger.json")
    suppression_raw = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/suppression_list.json")
    mailboxes = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/mailboxes.json")

    suppressed = set()
    if isinstance(suppression_raw, dict):
        suppressed = {k.lower().strip() for k in suppression_raw.keys()}
    elif isinstance(suppression_raw, list):
        suppressed = {str(k).lower().strip() for k in suppression_raw}

    sent_emails = set()
    for k, v in sent_ledger.items():
        if isinstance(v, dict):
            em = v.get("email") or v.get("recipient_email")
            if em:
                sent_emails.add(str(em).lower().strip())

    print(f"[+] Vault Loaded: {len(approved_pitches)} pitches | Sent Ledger: {len(sent_ledger)} | Suppressed: {len(suppressed)}")
    print(f"[+] Mailbox Pool: {len(mailboxes)} active Hostinger mailboxes")

    # Filter uncontacted
    pending = []
    for item in approved_pitches:
        em = (item.get("recipient_email") or item.get("email") or "").strip().lower()
        if not em or "@" not in em:
            continue
        if em in sent_emails or em in suppressed:
            continue
        
        state = item.get("state") or "US"
        if not is_surge and not is_golden_window(state):
            continue
        pending.append(item)

    print(f"[+] Pending Deliverable Pitches (In Golden Window): {len(pending)}")
    if not pending:
        print("[*] Zero pitches pending in active timezone window right now. Exiting gracefully.")
        ftp.quit()
        return

    random.shuffle(pending)
    selected_batch = pending[:batch_size]
    print(f"[*] Dispatching batch of {len(selected_batch)} emails across {len(mailboxes)} mailboxes...\n")

    dispatched_count = 0
    ssl_context = ssl.create_default_context()
    box_idx = random.randint(0, len(mailboxes) - 1)

    for idx, pitch in enumerate(selected_batch):
        box = mailboxes[box_idx % len(mailboxes)]
        box_idx += 1

        sender_email = box["user"]
        sender_name = box.get("name", "Faiz")
        subdomain = sender_email.split("@")[1]

        recipient_email = pitch["recipient_email"]
        recipient_name = pitch.get("recipient_name", "Business Owner")
        biz_name = pitch.get("business_name", "Contractor")
        subject = pitch.get("subject", f"Quick question regarding {biz_name}")
        body_text = pitch.get("body", "")

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = f"{recipient_name} <{recipient_email}>"
        msg["Reply-To"] = "Faiz Majeed <faiz@fzcorestudio.com>"
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=subdomain)

        # Plain & Clean HTML
        paras = "".join(f'<p style="margin: 0 0 14px 0; font-size: 14px; line-height: 1.55; color: #111827;">{p.replace(chr(10), "<br>")}</p>' for p in body_text.split("\n\n"))
        body_html = f"""<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 14px; color: #111827;">{paras}</body></html>"""

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        print(f"[{idx+1}/{len(selected_batch)}] Sending from {sender_email} -> {recipient_email} ({biz_name})...")

        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl_context, timeout=25) as server:
                server.login(sender_email, SUBDOMAIN_MAIL_PASS)
                server.sendmail(sender_email, [recipient_email], msg.as_string())
            
            dispatched_count += 1
            lead_id = pitch.get("lead_id") or f"FZ-US-{int(time.time())}-{dispatched_count}"
            sent_ledger[lead_id] = {
                "email": recipient_email,
                "business_name": biz_name,
                "sender": sender_email,
                "subject": subject,
                "sent_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "DELIVERED"
            }
            print(f"   ✓ DELIVERED successfully via {sender_email}")

        except Exception as e:
            print(f"   [!] SMTP Delivery Error on {sender_email}: {e}")

        # Humanized Anti-Spam Jitter (18 to 35 seconds)
        if idx < len(selected_batch) - 1:
            delay = random.uniform(18.0, 32.0)
            print(f"   ⏳ Human Jitter Delay: {round(delay, 1)}s...")
            time.sleep(delay)

    # 4. Upload updated ledger back to Hostinger FTP
    print(f"\n[*] Uploading updated ledger ({len(sent_ledger)} entries) to Hostinger FTP...")
    bio_up = io.BytesIO(json.dumps(sent_ledger, indent=2).encode('utf-8'))
    ftp.storbinary("STOR /domains/fzcorestudio.com/outbound_engine/sent_ledger.json", bio_up)
    ftp.quit()

    print(f"✅ [COMPLETE] Batch finished: {dispatched_count} emails delivered safely.")
    print("=" * 75)

if __name__ == "__main__":
    b_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    surge = "--surge" in sys.argv or "-s" in sys.argv
    run_cloud_dispatch(batch_size=b_size, is_surge=surge)
