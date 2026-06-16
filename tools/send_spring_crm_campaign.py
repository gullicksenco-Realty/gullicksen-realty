#!/usr/bin/env python3
"""
Spring Existing-CRM Campaign — Daily SendGrid Runner
Sends up to 150 emails/day from the approved recipient list.
Tracks state so each contact receives the campaign exactly once.
Uses SendGrid v3 Mail API with inline logo attachments (Content-ID).
"""

import base64
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path("/Users/warden/.hermes/workspace/.env"))

CRM_DIR = Path("/Users/warden/.hermes/workspace/crm")
SENDGRID_KEY_PATH = CRM_DIR / "sendgrid_api_key.txt"  # Legacy fallback


# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT = Path("/Users/warden/gullicksen-realty")
OUTBOX = PROJECT / "agent-inbox/outbox"
RECIPIENT_CSV = OUTBOX / "2026-06-02-spring-market-crm-recipient-review.csv"
HTML_TEMPLATE = OUTBOX / "2026-06-02-spring-market-crm-email-preview.html"
STATE_PATH = CRM_DIR / "spring_crm_campaign_state.json"

LOGO_PATH = Path("/Users/warden/Desktop/gullicksen-realty/gullicksen-logo.png")
ERA_LOGO_PATH = CRM_DIR / "era_sunrise_logo.jpg"

SENDGRID_API = "https://api.sendgrid.com/v3/mail/send"
FROM_EMAIL = "mike@gullicksenrealty.com"
FROM_NAME = "Mike Gullicksen"
DAILY_CAP = 150
SUBJECT = "Spring market update for North Georgia"
CAMPAIGN_NAME = "spring-existing-crm"
EMAIL_RE = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")


def norm_email(value: str) -> str:
    value = (value or "").strip().lower()
    if value.startswith("mailto:"):
        value = value.removeprefix("mailto:").strip()
    return value if EMAIL_RE.match(value) else ""


def load_api_key() -> str:
    key = os.environ.get("SENDGRID_API_KEY", "").strip()
    if key:
        return key
    return SENDGRID_KEY_PATH.read_text().strip()


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"sent_emails": [], "send_log": []}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def load_recipients() -> list[dict]:
    if not RECIPIENT_CSV.exists():
        raise SystemExit(f"Recipient CSV not found: {RECIPIENT_CSV}")
    with RECIPIENT_CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))
    
    # Load CRM suppression list
    crm_suppressed = set()
    try:
        import sqlite3
        import sqlite3
        conn = sqlite3.connect(CRM_DIR / "crm.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Find ALL emails that are suppressed for ANY reason
        cursor.execute("""
            SELECT email1, email2 FROM contacts 
            WHERE email_optout = 1 OR email_bounced = 1 OR sms_optout = 1
            OR status IN ('unsubscribed', 'bounce', 'spam', 'invalid', 'blacklisted', 'suppressed')
        """)
        for row in cursor.fetchall():
            for field in ['email1', 'email2']:
                email = (row[field] or "").strip().lower()
                if email:
                    crm_suppressed.add(email)
        conn.close()
    except Exception as e:
        print(f"WARNING: Could not load CRM suppression list: {e}", file=sys.stderr)
    
    eligible = []
    for row in rows:
        email = norm_email(row.get("email") or "")
        if not email:
            continue
        if email in crm_suppressed:
            print(f"  SKIP (suppressed): {email}")
            continue
        row["email"] = email
        eligible.append(row)
    return eligible


def personalize_html(html: str, first_name: str) -> str:
    return html.replace("{first_name}", first_name or "there")


def file_to_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def build_payload(email: str, first_name: str, html_body: str, logo_b64: str, era_b64: str) -> dict:
    """Build SendGrid v3 payload with inline attachments (Content-ID) for logos."""
    # Plain text fallback
    text_body = f"""Hi {first_name or 'there'},

Spring has brought more inventory into several North Georgia markets, but the story is different county by county.

Cherokee County — Detached median $488K (-3.4%), inventory up 28.9%
Cobb County — Detached median $495.9K (+0.9%), inventory up 9.7%
Gwinnett County — Detached median $436K (+0.2%), inventory up 15.1%
Forsyth County — Detached median $635.8K (-8.2%), inventory up 18.0%

If you want a quick read on your neighborhood, reply with your address.

Mike Gullicksen
Gullicksen Realty & Co.
ERA Sunrise Realty
770-825-2626
mike@gullicksenrealty.com
"""
    return {
        "personalizations": [{"to": [{"email": email}]}],
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "reply_to": {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": SUBJECT,
        "content": [
            {"type": "text/plain", "value": text_body},
            {"type": "text/html", "value": html_body},
        ],
        "attachments": [
            {
                "content": logo_b64,
                "type": "image/png",
                "filename": "gullicksen-logo.png",
                "disposition": "inline",
                "content_id": "gullicksen_logo",
            },
            {
                "content": era_b64,
                "type": "image/jpeg",
                "filename": "era_sunrise_logo.jpg",
                "disposition": "inline",
                "content_id": "era_logo",
            },
        ],
        "categories": [CAMPAIGN_NAME],
    }


def send_one(api_key: str, payload: dict) -> tuple[bool, str]:
    req = urllib.request.Request(
        SENDGRID_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 202, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, f"HTTP {exc.code}: {body[:500]}"
    except Exception as exc:
        return False, str(exc)


def write_send_log(path: Path, rows: list[dict]) -> None:
    fieldnames = ["timestamp", "send_status", "response", "email", "contact_id", "first_name", "source"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_summary(path: Path, sent: int, failed: int, skipped: int, remaining: int) -> None:
    lines = [
        f"# Spring Existing-CRM SendGrid Campaign Summary",
        f"",
        f"Run time: {datetime.now().isoformat(timespec='seconds')}",
        f"",
        f"## Approved Scope",
        f"",
        f"- Approved by Mike: Spring existing-CRM SendGrid email campaign.",
        f"- Recipient source: `2026-06-02-spring-market-crm-recipient-review.csv`",
        f"- HTML source: `2026-06-02-spring-market-crm-email-preview.html`",
        f"- Subject: {SUBJECT}",
        f"- Daily cap: {DAILY_CAP}",
        f"- Channel: SendGrid email only",
        f"- No SMS, calls, social DMs, CRM import, paid lookup, or public posting.",
        f"",
        f"## Result",
        f"",
        f"- Accepted by SendGrid: {sent}",
        f"- Failed: {failed}",
        f"- Skipped (already sent): {skipped}",
        f"- Remaining in queue: {remaining}",
        f"",
        f"SendGrid HTTP 202 means accepted for delivery; it does not guarantee inbox placement.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    print(f"=== Spring CRM Campaign — {datetime.now().isoformat(timespec='seconds')} ===")

    api_key = load_api_key()
    state = load_state()
    already_sent = set(filter(None, (norm_email(e) for e in state.get("sent_emails", []))))

    recipients = load_recipients()
    html_template = HTML_TEMPLATE.read_text()

    # Pre-load logos (base64) — same for every email
    logo_b64 = file_to_b64(LOGO_PATH)
    era_b64 = file_to_b64(ERA_LOGO_PATH)

    # Filter out already-sent
    to_send = [r for r in recipients if (r.get("email") or "").strip().lower() not in already_sent]
    total_remaining = len(to_send)

    print(f"Total eligible: {len(recipients)}")
    print(f"Already sent: {len(already_sent)}")
    print(f"Remaining to send: {total_remaining}")
    print(f"Daily cap: {DAILY_CAP}")
    print()

    if total_remaining == 0:
        print("✅ Campaign complete — all contacts sent.")
        return 0

    batch = to_send[:DAILY_CAP]
    sent_count = 0
    failed_count = 0
    log_rows = []

    for row in batch:
        email = norm_email(row.get("email", ""))
        if not email:
            continue
        first_name = row.get("first_name") or (row.get("name", "").split()[0] if row.get("name") else "")
        contact_id = row.get("contact_id", "")
        source = row.get("source", "existing CRM")

        html = personalize_html(html_template, first_name)
        payload = build_payload(email, first_name, html, logo_b64, era_b64)
        ok, response = send_one(api_key, payload)

        status = "accepted" if ok else "failed"
        if ok:
            sent_count += 1
            state["sent_emails"].append(email.lower())
            print(f"  ✅ [{sent_count}] {email}")
        else:
            failed_count += 1
            print(f"  ❌ {email}: {response}")

        log_rows.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "send_status": status,
            "response": response,
            "email": email,
            "contact_id": contact_id,
            "first_name": first_name,
            "source": source,
        })

        save_state(state)
        time.sleep(0.5)

    skipped_count = total_remaining - len(batch)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = OUTBOX / f"sendgrid-spring-existing-crm-send-log-{stamp}.csv"
    summary_path = OUTBOX / f"sendgrid-spring-existing-crm-send-summary-{stamp}.md"

    write_send_log(log_path, log_rows)
    write_summary(summary_path, sent_count, failed_count, skipped_count, total_remaining - sent_count)

    print(f"\n✅ Done: {sent_count} sent, {failed_count} failed, {skipped_count} skipped")
    print(f"📄 Log: {log_path}")
    print(f"📄 Summary: {summary_path}")

    # Post-send health check
    try:
        import subprocess
        subprocess.run([sys.executable, str(PROJECT / "tools/campaign_health_check.py")], check=False)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
