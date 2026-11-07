# -*- coding: utf-8 -*-
"""
FZCORE Studio - Autonomous Vault Refiller & High-Converting Pitch Formatter
Formats uncontacted leads into high-converting, flaw-calibrated pitches (Full-Stack Web Dev & AI Automation)
and uploads directly to Hostinger Private Storage.
"""

import sys
import os
import json
import ftplib
import io
import re
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "outbound_engine" / "data"

FTP_HOST = os.environ.get("FTP_SERVER", "82.197.83.123")
FTP_USER = os.environ.get("FTP_USERNAME", "u476907848")
FTP_PASS = os.environ.get("FTP_PASSWORD", "")

JUNK_NAMES = {
    'business', 'owner', 'founder', 'admin', 'office', 'info', 'support', 'team',
    'operated', 'family', 'became', 'board', 'marketplace', 'energized', 'drop',
    'greater', 'orlando', 'houston', 'tampa', 'dallas', 'austin', 'miami', 'vancouver',
    'sydney', 'company', 'services', 'contractor', 'builders', 'roofing', 'remodeling',
    'cleaning', 'group', 'design', 'studio', 'solutions', 'management', 'enterprises',
    'inc', 'llc', 'corp', 'co', 'there', 'hello', 'contact', 'custom', 'luxury'
}

def clean_first_name(raw):
    if not raw:
        return None
    cleaned = re.sub(r'[^a-zA-Z\s]', '', str(raw)).strip()
    parts = cleaned.split()
    if not parts:
        return None
    first = parts[0].capitalize()
    if len(first) < 2 or first.lower() in JUNK_NAMES:
        return None
    return first

def clean_biz_name(raw):
    if not raw:
        return 'your business'
    cleaned = str(raw).strip()
    for delim in [':', '|', ' - ', ' -- ', ' | ']:
        if delim in cleaned:
            parts = cleaned.split(delim)
            if len(parts[0].strip()) >= 3:
                cleaned = parts[0].strip()
                break
    return cleaned

def get_niche_context(category):
    cat_lower = str(category).lower()
    if any(k in cat_lower for k in ['roof', 'siding', 'gutter', 'restoration']):
        return {
            'client_type': 'homeowners',
            'competitor_type': 'roofer in the area',
            'job_name': 'roof replacements and storm repairs',
            'deliverable': 'mobile speed-to-lead dispatch system and 1-tap call bar'
        }
    elif any(k in cat_lower for k in ['home', 'builder', 'remodel', 'fencing', 'pool', 'paver', 'epoxy', 'solar', 'hardscaping', 'plumbing', 'electrician', 'paint', 'concrete', 'tree', 'foundation']):
        return {
            'client_type': 'homeowners',
            'competitor_type': 'contractor on Google Maps',
            'job_name': 'high-ticket installations and remodels',
            'deliverable': 'instant mobile project intake and 1-tap dispatch bar'
        }
    elif any(k in cat_lower for k in ['janitorial', 'cleaning', 'pressure washing', 'commercial', 'hvac']):
        return {
            'client_type': 'property and facility managers',
            'competitor_type': 'commercial contractor on Google Maps',
            'job_name': 'commercial maintenance contracts',
            'deliverable': 'rapid commercial quote intake and direct phone dispatch'
        }
    elif any(k in cat_lower for k in ['detailing', 'car wash', 'tinting', 'ppf', 'audio']):
        return {
            'client_type': 'vehicle owners',
            'competitor_type': 'detail shop on Google Maps',
            'job_name': 'ceramic coating and paint protection packages',
            'deliverable': 'interactive package booking system and 1-tap call bar'
        }
    elif any(k in cat_lower for k in ['medspa', 'surgery', 'dentist', 'clinic', 'wellness', 'chiro']):
        return {
            'client_type': 'prospective patients',
            'competitor_type': 'clinic in the area',
            'job_name': 'high-value treatment consultations',
            'deliverable': 'direct consultation booking bridge and mobile call bar'
        }
    elif any(k in cat_lower for k in ['tax', 'cpa', 'law', 'legal', 'visa', 'immigration']):
        return {
            'client_type': 'prospective clients',
            'competitor_type': 'firm in the area',
            'job_name': 'retained client consultations',
            'deliverable': 'case assessment intake bridge and direct call bar'
        }
    else:
        return {
            'client_type': 'prospective clients',
            'competitor_type': 'local competitor on Google Maps',
            'job_name': 'new client projects',
            'deliverable': 'rapid mobile dispatch bridge and 1-tap call bar'
        }

def generate_high_converting_pitch(item, ctx, first_name, is_frontdesk, biz, city, cat, domain):
    import hashlib
    diagnostics = item.get('audit_diagnostics') or {}
    primary_flaw = str(diagnostics.get('primary_flaw') or item.get('primary_flaw') or '').lower()
    latency = diagnostics.get('latency_sec') or item.get('latency_sec') or 2.1
    input_count = diagnostics.get('input_count') or 6
    
    h = int(hashlib.md5(f"{domain}_{biz}".encode()).hexdigest(), 16)
    flaw_lower = primary_flaw.lower()
    cat_lower = str(cat).lower()
    first_name = clean_first_name(first_name)
    biz = clean_biz_name(biz)

    # Contextual trade nuances
    if any(k in cat_lower for k in ['roof', 'siding', 'gutter']):
        trade_label = "roof replacements and repairs"
        client_label = "homeowners"
        competitor_label = "roofer in the area"
    elif any(k in cat_lower for k in ['home', 'builder', 'remodel']):
        trade_label = "custom remodeling and builds"
        client_label = "homeowners"
        competitor_label = "builder on Google Maps"
    elif any(k in cat_lower for k in ['pool', 'paver', 'hardscape', 'epoxy', 'concrete']):
        trade_label = "outdoor living and installations"
        client_label = "homeowners"
        competitor_label = "contractor in the area"
    elif any(k in cat_lower for k in ['detail', 'tint', 'ppf']):
        trade_label = "ceramic coating and detailing"
        client_label = "vehicle owners"
        competitor_label = "detail shop on Google Maps"
    elif any(k in cat_lower for k in ['janitorial', 'cleaning', 'pressure washing', 'commercial', 'hvac']):
        trade_label = "commercial facility contracts"
        client_label = "property managers"
        competitor_label = "commercial provider on Google Maps"
    else:
        trade_label = f"{cat_lower} projects"
        client_label = "clients"
        competitor_label = "competitor on Google Maps"

    # 1. PSYCHOLOGICAL SUBJECT LINE ROTATION (No corporate templates)
    if not is_frontdesk and first_name:
        subj_candidates = [
            domain,
            f"{first_name.lower()}?",
            f"quick question re {city} projects",
            f"noticed something on {domain}",
            f"quick heads up for {first_name}",
            f"your site ({domain})"
        ]
    else:
        subj_candidates = [
            domain,
            f"question for the owner of {biz}",
            f"quick heads up re {domain}",
            f"{domain} inquiry flow",
            f"quick note for {biz} team"
        ]
    subject = subj_candidates[h % len(subj_candidates)]

    # 2. GREETING (CASUAL HUMAN)
    if not is_frontdesk and first_name:
        greetings = [f"Hey {first_name},", f"{first_name},", f"Hi {first_name},"]
    else:
        greetings = [
            f"Hey team,",
            f"Hi team,",
            f"Quick note for the owner of {biz},"
        ]
    greeting = greetings[h % len(greetings)]

    # 3. DYNAMIC OWNER-PSYCHOLOGY OPENER & CORE BODY
    archetype = (h >> 3) % 3

    # ANGLE 1: Speed-to-Lead / Missed Call SMS Webhook
    if 'speed-to-lead' in flaw_lower or 'sms' in flaw_lower or 'webhook' in flaw_lower or archetype == 0:
        bleed_type = "AI Speed-to-Lead Leak"
        if not is_frontdesk and first_name:
            if archetype == 0:
                opener = f"Quick heads up. I was looking at {domain} on my iPhone yesterday and noticed when someone submits a quote request, there is no automated text confirmation sent to their phone."
                economic_pain = f"In {city}, {client_label} looking for {trade_label} usually request quotes from 2 or 3 companies at once. Data shows 78% hire whichever contractor texts them first within 5 minutes. If your crew is up on a job site, that lead goes cold and calls the next {competitor_label}."
                asset_tease = f"I already set up the 30-second automated text bridge for {biz} to patch this."
                cta = f"Should I send the link over to this email?"
            elif archetype == 1:
                opener = f"Are you guys still taking on {trade_label} in {city} right now, or are you guys booked out for the month?"
                economic_pain = f"Reason I ask: I was on {domain} from mobile and noticed quote requests drop into an email inbox with no instant text back to the customer. When {client_label} browse on phones, that delay usually means they move to the next company on Maps."
                asset_tease = f"I put together a clean mobile 1-tap dispatch bar and instant text confirmation flow for {biz}."
                cta = f"Mind if I share a quick 20-second screen demo?"
            else:
                opener = f"I'm a web engineer specializing in local contractor sites."
                economic_pain = f"Was looking over {domain} and noticed quote submissions sit in an email inbox without an instant 30-second SMS trigger. When your team is out working, you're likely losing high-ticket {trade_label} to whoever responds first."
                asset_tease = f"I already mocked up a quick demo showing how the instant SMS dispatch flow works for {biz}."
                cta = f"Where should I send the preview?"
        else:
            opener = f"Quick heads up for the owner or whoever manages incoming estimates at {biz}."
            economic_pain = f"Was on {domain} from mobile and noticed when someone requests an estimate, it drops into an email inbox with zero text confirmation back to their phone. Most {client_label} in {city} reach out to multiple contractors and sign with whoever replies first."
            asset_tease = f"I already built a 30-second text confirmation bridge tailored for {biz} to solve this."
            cta = f"Could you pass this to the owner or let me know if I can shoot the 20-second demo over?"

    # ANGLE 2: Turnkey Bento Architecture & Authority Redesign
    elif 'wordpress' in flaw_lower or 'redesign' in flaw_lower or 'legacy' in flaw_lower or 'theme' in flaw_lower or 'architecture' in flaw_lower:
        bleed_type = "Outdated Website Architecture"
        if not is_frontdesk and first_name:
            opener = f"Quick heads up regarding {domain}."
            economic_pain = f"Was checking your site on mobile and noticed the layout is still running on an older boxed format. When high-ticket {client_label} in {city} are comparing 3 bids for {trade_label}, modern Bento-grid layouts with instant tap-to-call and verified project proof convert noticeably higher."
            asset_tease = f"I put together an executive redesign concept specifically for {biz} showing what your work looks like in a modern layout."
            cta = f"Would you be against me sending over a quick 30-second preview link?"
        else:
            opener = f"Quick question for the owner or founder of {biz}."
            economic_pain = f"Looked at {domain} on mobile and noticed the site is running on an older boxed theme compared to the newer contractor sites in {city}. High-ticket {client_label} judge credibility in seconds on their phone before calling."
            asset_tease = f"I put together a modern redesign concept specifically for {biz}."
            cta = f"Could you point me to the owner or let me know if I can share the short preview?"

    # ANGLE 3: Form Friction Drop-Off (7+ Fields)
    elif 'form' in flaw_lower or 'friction' in flaw_lower or 'abandonment' in flaw_lower:
        bleed_type = "Form Friction Drop-Off"
        if not is_frontdesk and first_name:
            opener = f"Quick observation re {domain} quote intake."
            economic_pain = f"Pulled up your site on my phone and noticed the contact form asks for {input_count}+ fields upfront on a single screen. On mobile, that friction causes over 60% of {client_label} to abandon the page before submitting."
            asset_tease = f"Switching to a 3-step progressive scope intake (Project Type -> Timeline -> Contact) usually doubles completed submissions. I already mocked one up for {biz}."
            cta = f"Mind if I send over a quick 20-second screen preview?"
        else:
            opener = f"Quick note for the owner of {biz}."
            economic_pain = f"Noticed the quote intake on {domain} demands {input_count}+ fields upfront on one page, which causes mobile visitors to bounce back to Google Maps."
            asset_tease = f"I mocked up a clean 3-step mobile intake tailored for {biz} that doubles completed submissions."
            cta = f"Could you pass this to the owner or let me know if I can send the preview over?"

    # ANGLE 4: Cellular Mobile Latency (TTFB > 2.5s)
    elif 'latency' in flaw_lower or 'speed' in flaw_lower or 'ttfb' in flaw_lower or 'cellular' in flaw_lower:
        bleed_type = "Cellular Mobile Latency"
        if not is_frontdesk and first_name:
            opener = f"Quick technical heads up re {domain}."
            economic_pain = f"Clocked your mobile load time at over {latency}s on cellular data due to older asset scripts. On phones, every second of lag costs you about 20% of incoming {client_label} before they even see your reviews."
            asset_tease = f"I rebuilt a lightweight edge preview for {biz} that loads instantly on any phone."
            cta = f"Mind if I shoot over a quick side-by-side speed comparison?"
        else:
            opener = f"Quick note for whoever oversees technical operations at {biz}."
            economic_pain = f"Clocked {domain}'s mobile load time at over {latency}s on phones, causing local {client_label} to bounce back to Google search before the page renders."
            asset_tease = f"I put together a quick side-by-side speed preview for {biz}."
            cta = f"Could you point me to the owner or let me know if I can share it?"

    # ANGLE 5: Default Mobile 1-Tap Dispatch & Fast Inquiry
    else:
        bleed_type = "Mobile Conversion Leak"
        if not is_frontdesk and first_name:
            opener = f"Quick heads up. Was on {domain} from my phone yesterday and noticed the phone number in your header isn't 1-tap clickable, and quote requests go straight to email without an automated text back."
            economic_pain = f"When local {client_label} look for {trade_label}, having to copy-paste digits or wait hours for a reply usually leads them to call the next {competitor_label}."
            asset_tease = f"I put together a clean mobile 1-tap call bar and instant text confirmation flow specifically for {biz}."
            cta = f"Should I send the 20-second preview link over?"
        else:
            opener = f"Quick note for the owner of {biz}."
            economic_pain = f"Pulled up {domain} on mobile and noticed there is no sticky 1-tap call button, and incoming inquiries don't trigger an automated text confirmation back to the customer."
            asset_tease = f"I mocked up a clean mobile dispatch bar and instant text flow tailored for {biz}."
            cta = f"Could you point me to the owner or let me know if I can send over the short preview?"

    body = f"{greeting}\n\n{opener}\n\n{economic_pain}\n\n{asset_tease}\n\n{cta}\n\nFaiz"
    return subject, body, bleed_type

def refill_vault():
    print("=" * 70)
    print("📦 [VAULT REFILLER] Preparing Fresh Uncontacted Pitches for Hostinger...")
    print("=" * 70)

    # 1. Connect to Hostinger FTP & download latest sent ledger
    ftp = ftplib.FTP(FTP_HOST, timeout=30)
    connected = False
    passwords_to_try = [p for p in [os.environ.get("FTP_PASSWORD")] if p]
    for p in passwords_to_try:
        try:
            ftp.login(FTP_USER, p)
            ftp.set_pasv(True)
            print("[+] Logged into Hostinger FTP.")
            connected = True
            break
        except Exception:
            pass
    if not connected:
        print("[!] FTP connection error: 530 Login failed across all fallback credentials.")
        return False

    bio_ledger = io.BytesIO()
    remote_ledger = "/domains/fzcorestudio.com/outbound_engine/sent_ledger.json"
    try:
        ftp.retrbinary(f"RETR {remote_ledger}", bio_ledger.write)
        bio_ledger.seek(0)
        ledger_data = json.loads(bio_ledger.read().decode('utf-8', errors='ignore'))
        print(f"[+] Retrieved active ledger: {len(ledger_data)} sent entries.")
    except Exception as e:
        print(f"[!] Could not read remote ledger: {e}")
        ledger_data = {}

    sent_emails = set()
    for k, v in ledger_data.items():
        if isinstance(v, dict):
            em = v.get('recipient_email') or v.get('email') or v.get('recipient')
            if em:
                sent_emails.add(str(em).lower().strip())

    # 2. Pool uncontacted leads from all high-intent vetted datasets
    all_leads = []
    for fn in ["vetted_master_dossier.json", "morning_leads_latest.json", "vetted_revenue_bleed_leads.json"]:
        fpath = DATA_DIR / fn
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if isinstance(d, list):
                        all_leads.extend(d)
                        print(f"[+] Loaded {len(d)} leads from {fn}")
            except Exception as e:
                print(f"[!] Error reading {fn}: {e}")

    if not all_leads:
        print("[!] No leads found across datasets.")
        ftp.quit()
        return False

    # Load suppression blacklist
    bio_supp = io.BytesIO()
    suppressed = set()
    try:
        ftp.retrbinary("RETR /domains/fzcorestudio.com/outbound_engine/suppression_list.json", bio_supp.write)
        s_raw = json.loads(bio_supp.getvalue().decode('utf-8', errors='ignore'))
        if isinstance(s_raw, dict):
            suppressed = {k.lower().strip() for k in s_raw.keys()}
        elif isinstance(s_raw, list):
            suppressed = {str(k).lower().strip() for k in s_raw}
        print(f"[+] Loaded {len(suppressed)} blacklisted addresses from suppression list.")
    except Exception as e:
        print(f"[!] Could not load suppression list: {e}")

    BANNED_EMAIL_DOMAINS = {
        'sentry.io', 'wixpress.com', 'cloudflare.com', 'angi.com', 'homestars.com',
        'yelp.com', 'thumbtack.com', 'bbb.org', 'facebook.com', 'instagram.com',
        'example.com', 'domain.com', 'yourdomain.com', 'hostinger.com', 'mailchannels.net'
    }
    TRUNCATED_TYPO_PREFIXES = {'nfo', 'ervice', 'ontact', 'upport', 'dmin', 'ffice', 'ello', 'nquiries'}

    def is_clean(e):
        if not e or '@' not in e:
            return False
        e = e.lower().strip().replace('%20', '').strip(" '<>():,;\"")
        parts = e.split('@')
        if len(parts) != 2:
            return False
        pfx, dom = parts[0], parts[1]
        if len(pfx) < 2 or len(pfx) > 40 or pfx in TRUNCATED_TYPO_PREFIXES:
            return False
        if any(dom.endswith(b) for b in BANNED_EMAIL_DOMAINS):
            return False
        if any(e.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif', '.js', '.css']):
            return False
        return True

    GENERIC_PREFIXES = {'info', 'office', 'contact', 'admin', 'support', 'sales', 'hello', 'inquiries', 'help', 'team', 'service', 'enquiries'}

    pool = {}
    for item in all_leads:
        dm = item.get('decision_maker') or {}
        em = dm.get('verified_email') or item.get('recipient_email') or item.get('email') or item.get('verified_email')
        if em and '@' in str(em):
            em_clean = str(em).lower().strip().replace('%20', '').strip(" '<>():,;\"")
            if not is_clean(em_clean):
                continue
            if em_clean in suppressed:
                continue
            if em_clean not in sent_emails and em_clean not in pool:
                pool[em_clean] = item

    print(f"[+] Total uncontacted leads available in dataset: {len(pool)}")

    formatted_pitches = []
    for em, item in pool.items():
        prefix = em.split('@')[0]
        base_prefix = prefix.split('.')[0].split('_')[0].split('-')[0]
        is_frontdesk = base_prefix in GENERIC_PREFIXES

        dm = item.get('decision_maker') or {}
        raw_name = item.get('recipient_name') or dm.get('first_name') or dm.get('name')
        first_name = clean_first_name(raw_name)

        biz = clean_biz_name(item.get('business_name'))
        city = item.get('city') or 'your area'
        state = item.get('state') or 'US'
        cat = item.get('category') or 'contractor'
        domain = item.get('domain') or item.get('website', '').replace('https://', '').replace('http://', '').strip('/')
        ctx = get_niche_context(cat)

        subject, body, bleed_type = generate_high_converting_pitch(item, ctx, first_name, is_frontdesk, biz, city, cat, domain)

        formatted_pitches.append({
            'lead_id': f'FZ-{abs(hash(em)) % 10000000000}',
            'business_name': biz,
            'recipient_email': em,
            'recipient_name': first_name or 'Owner',
            'category': cat,
            'city': city,
            'state': state,
            'website': item.get('website', ''),
            'domain': domain,
            'reviews_count': item.get('reviews_count', 0),
            'rating': item.get('rating', 5.0),
            'subject': subject,
            'body': body,
            'bleed_type': bleed_type,
            'lead': item
        })

    print(f"[+] Formatted {len(formatted_pitches)} pitches.")

    # Save locally
    approved_file = DATA_DIR / "approved_pitches.json"
    with open(approved_file, "w", encoding="utf-8") as f:
        json.dump(formatted_pitches, f, indent=2)

    # Upload to Hostinger Private Vault
    bio_upload = io.BytesIO(json.dumps(formatted_pitches, indent=2).encode('utf-8'))
    remote_pitches = "/domains/fzcorestudio.com/outbound_engine/approved_pitches.json"
    ftp.storbinary(f"STOR {remote_pitches}", bio_upload)
    ftp.quit()

    print(f"✅ [SUCCESS] Hostinger Vault Refilled: {len(formatted_pitches)} active pitches ready for cloud dispatcher!")
    return True

if __name__ == "__main__":
    refill_vault()
