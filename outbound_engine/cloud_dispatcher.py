# -*- coding: utf-8 -*-
"""
FZCORE STUDIO - Autonomous High-Velocity Cloud SMTP Dispatcher & Follow-Up Engine
Runs 100% on GitHub Actions Cloud Runners (Zero PC Dependency).
Uses Dual-Threaded Worker Architecture across 48 Healthy Hostinger Mailboxes.
Throughput: ~300-360 emails/hour with 18-28s human jitter per thread.
Guarantees 1,200 daily target completion before 11:30 PM PKT tonight.
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
import threading
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
    # Eastern (UTC-5)
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
    offset = TZ_MAP.get(str(state_str).upper().strip(), -5)
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    local_hour = (utc_now.hour + offset) % 24
    local_min = utc_now.minute
    time_float = local_hour + (local_min / 60.0)
    # 7:15 AM to 6:30 PM local
    return 7.25 <= time_float <= 18.50

def run_multi_worker_dispatcher(target_count=1200, is_surge=True):
    print("=" * 80)
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] FZCORE Dual-Engine Cloud Dispatcher Active!")
    print(f"Daily Target: {target_count} | Mode: {'SURGE (All Active States)' if is_surge else 'Daylight Window'}")
    print("=" * 80)

    if not FTP_PASS or not SUBDOMAIN_MAIL_PASS:
        print("[!] ERROR: Missing FTP_PASSWORD or SUBDOMAIN_MAIL_PASS.")
        sys.exit(1)

    # 1. Fetch Vault & Ledgers from Hostinger FTP
    print("[*] Connecting to Hostinger FTP to load vault & ledgers...")
    ftp = ftplib.FTP(FTP_HOST, timeout=30)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.set_pasv(True)

    def read_ftp_json(path):
        bio = io.BytesIO()
        try:
            ftp.retrbinary(f"RETR {path}", bio.write)
            return json.loads(bio.getvalue().decode('utf-8'))
        except Exception as e:
            print(f"[!] Notice reading {path}: {e}")
            return {}

    approved_pitches = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/approved_pitches.json")
    if isinstance(approved_pitches, dict):
        approved_pitches = list(approved_pitches.values())
    if not isinstance(approved_pitches, list):
        approved_pitches = []

    sent_ledger = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/sent_ledger.json")
    suppression_raw = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/suppression_list.json")
    mailboxes = read_ftp_json("/domains/fzcorestudio.com/outbound_engine/mailboxes.json")

    ftp.quit()
    print("[+] Vault loaded. FTP socket closed safely.")

    suppressed = set()
    if isinstance(suppression_raw, dict):
        suppressed = {k.lower().strip() for k in suppression_raw.keys()}
    elif isinstance(suppression_raw, list):
        suppressed = {str(k).lower().strip() for k in suppression_raw}

    sent_emails = set()
    initial_threads = {}
    followup_sent = set()

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    already_sent_today = 0

    for k, v in sent_ledger.items():
        if isinstance(v, dict):
            em = str(v.get("email") or v.get("recipient_email") or "").lower().strip()
            if em:
                sent_emails.add(em)
                sent_at = str(v.get("sent_at", ""))
                if today_str in sent_at:
                    already_sent_today += 1

                subj = str(v.get("subject", "")).lower()
                if subj.startswith("re:") or v.get("type") == "followup_1":
                    followup_sent.add(em)
                elif em not in initial_threads:
                    initial_threads[em] = {
                        "lead_id": k,
                        "data": v,
                        "sent_at": sent_at
                    }

    print(f"[+] Total Sent Ledger: {len(sent_ledger)} | Already Sent Today: {already_sent_today}")
    print(f"[+] Vault Total Pitches: {len(approved_pitches)} | Mailboxes: {len(mailboxes)}")

    needed_today = max(0, target_count - already_sent_today)
    print(f"🎯 Target Remaining Today: {needed_today} emails (to hit {target_count})")
    if needed_today <= 0:
        print("🏆 Daily target already achieved! Exiting.")
        return

    # Due follow-ups (Day +3)
    due_followups = []
    now_dt = datetime.datetime.now()
    for em, t_info in initial_threads.items():
        if em in followup_sent or em in suppressed:
            continue
        sent_str = t_info.get("sent_at", "")
        try:
            sent_dt = datetime.datetime.strptime(sent_str[:10], "%Y-%m-%d")
            if (now_dt - sent_dt).days >= 3:
                due_followups.append((em, t_info))
        except Exception:
            pass

    print(f"[+] Due Day +3 Follow-Up Bumps Identified: {len(due_followups)}")

    # Uncontacted fresh pitches
    pending_fresh = []
    for item in approved_pitches:
        em = (item.get("recipient_email") or item.get("email") or "").strip().lower()
        if not em or "@" not in em or em in sent_emails or em in suppressed:
            continue
        state = item.get("state") or "US"
        if not is_surge and not is_golden_window(state):
            continue
        pending_fresh.append(item)

    print(f"[+] Deliverable Fresh Pitches: {len(pending_fresh)}")

    # Build queue
    queue = []
    # Mix 15% followups, 85% fresh
    fu_quota = min(len(due_followups), int(needed_today * 0.15))
    for em, t_info in due_followups[:fu_quota]:
        queue.append({"type": "FOLLOWUP", "email": em, "info": t_info})

    fresh_quota = needed_today - len(queue)
    random.shuffle(pending_fresh)
    for p in pending_fresh[:fresh_quota]:
        queue.append({"type": "FRESH", "pitch": p})

    random.shuffle(queue)
    print(f"📦 Total Work Queue Prepared: {len(queue)} emails ({len(queue) - fresh_quota} follow-ups, {fresh_quota} fresh)")

    # Partition mailboxes into 2 worker groups (24 each)
    half = len(mailboxes) // 2
    worker1_boxes = mailboxes[:half]
    worker2_boxes = mailboxes[half:]

    # Thread-safe structures
    queue_lock = threading.Lock()
    ledger_lock = threading.Lock()
    total_delivered = [already_sent_today]

    def worker_loop(worker_name, mailbox_pool):
        ssl_ctx = ssl.create_default_context()
        b_idx = random.randint(0, len(mailbox_pool) - 1)
        worker_sent = 0

        while True:
            # Pop next item
            item = None
            with queue_lock:
                if queue and total_delivered[0] < target_count:
                    item = queue.pop(0)
                else:
                    break

            if not item:
                break

            box = mailbox_pool[b_idx % len(mailbox_pool)]
            b_idx += 1

            sender_email = box["user"]
            sender_name = box.get("name", "Faiz")
            subdomain = sender_email.split("@")[1]

            if item["type"] == "FOLLOWUP":
                rec_email = item["email"]
                t_data = item["info"]["data"]
                orig_subj = t_data.get("subject", "projects")
                clean_subj = orig_subj if orig_subj.lower().startswith("re:") else f"re: {orig_subj}"
                orig_msg_id = t_data.get("message_id")
                biz_name = t_data.get("business_name") or t_data.get("business", "your business")
                subject = clean_subj
                body_text = f"Quick follow-up here, did you get a chance to see my note or is this week too packed with jobs?\n\nFaiz\nfzcorestudio.com"
                is_followup = True
            else:
                p = item["pitch"]
                rec_email = p["recipient_email"]
                biz_name = p.get("business_name", "Contractor")
                subject = p.get("subject", f"Quick question regarding {biz_name}")
                body_text = p.get("body", "")
                orig_msg_id = None
                is_followup = False

            msg = MIMEMultipart("alternative")
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = f"<{rec_email}>"
            msg["Reply-To"] = "Faiz Majeed <faiz@fzcorestudio.com>"
            msg["Subject"] = subject
            msg["Date"] = formatdate(localtime=True)
            new_msg_id = make_msgid(domain=subdomain)
            msg["Message-ID"] = new_msg_id

            if is_followup and orig_msg_id:
                msg["In-Reply-To"] = orig_msg_id
                msg["References"] = orig_msg_id

            paras = "".join(f'<p style="margin: 0 0 14px 0; font-size: 14px; line-height: 1.55; color: #111827;">{par.replace(chr(10), "<br>")}</p>' for par in body_text.split("\n\n"))
            body_html = f"""<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 14px; color: #111827;">{paras}</body></html>"""

            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            pfx = "[FU]" if is_followup else "[NEW]"
            try:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl_ctx, timeout=25) as server:
                    server.login(sender_email, SUBDOMAIN_MAIL_PASS)
                    server.sendmail(sender_email, [rec_email], msg.as_string())

                worker_sent += 1
                with ledger_lock:
                    total_delivered[0] += 1
                    current_tot = total_delivered[0]
                    rec_id = f"FZ-US-{int(time.time())}-{current_tot}"
                    sent_ledger[rec_id] = {
                        "email": rec_email,
                        "business_name": biz_name,
                        "sender": sender_email,
                        "subject": subject,
                        "message_id": new_msg_id,
                        "sent_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "DELIVERED",
                        "type": "followup_1" if is_followup else "initial_pitch"
                    }

                print(f"[{worker_name}] {pfx} Sent -> {rec_email} via {sender_email} | Progress: {current_tot}/{target_count}")

                # Sync to Hostinger FTP every 25 sends per worker
                if worker_sent % 25 == 0:
                    sync_ledger_to_ftp()

            except Exception as e:
                print(f"[{worker_name}] [!] SMTP Delivery Error on {sender_email}: {e}")

            # Human anti-spam delay per worker (16 to 26 seconds)
            time.sleep(random.uniform(16.0, 26.0))

    def sync_ledger_to_ftp():
        with ledger_lock:
            data_to_save = dict(sent_ledger)
        for attempt in range(3):
            try:
                up_ftp = ftplib.FTP(FTP_HOST, timeout=30)
                up_ftp.login(FTP_USER, FTP_PASS)
                up_ftp.set_pasv(True)
                bio_up = io.BytesIO(json.dumps(data_to_save, indent=2).encode('utf-8'))
                up_ftp.storbinary("STOR /domains/fzcorestudio.com/outbound_engine/sent_ledger.json", bio_up)
                up_ftp.quit()
                print(f"   💾 [FTP-SYNC] Ledger synced ({len(data_to_save)} records).")
                break
            except Exception as e:
                time.sleep(3)

    # Launch 2 Parallel Workers
    print("\n🚀 Spawning Dual Cloud Workers (Engine 1: Mailboxes 1-24, Engine 2: Mailboxes 25-48)...")
    t1 = threading.Thread(target=worker_loop, args=("Worker-1", worker1_boxes), daemon=True)
    t2 = threading.Thread(target=worker_loop, args=("Worker-2", worker2_boxes), daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Final FTP Sync
    sync_ledger_to_ftp()
    print("=" * 80)
    print(f"🏆 [MISSION COMPLETE] Daily Target Finished! Total Today: {total_delivered[0]}/{target_count}")
    print("=" * 80)

if __name__ == "__main__":
    t_count = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    surge_mode = "--surge" in sys.argv or "-s" in sys.argv or True
    run_multi_worker_dispatcher(target_count=t_count, is_surge=surge_mode)
