#!/usr/bin/env python3
"""
Send the explicitly approved BatchData 42 email campaign.

Approved scope:
- Recipient source: sendgrid-recipient-review-batchdata-42.csv
- Recipients: review_status == candidate_review, de-duplicated by email
- Templates: approved Expired and Withdrawn HTML drafts
- Channel: email only
- No SMS, no calls, no CRM enrollment changes
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path("/Users/warden/.hermes/workspace/.env"))

CRM_DIR = Path("/Users/warden/.hermes/workspace/crm")
OUTBOX = Path("/Users/warden/gullicksen-realty/agent-inbox/outbox")
RECIPIENT_CSV = OUTBOX / "sendgrid-recipient-review-batchdata-42.csv"
EXPIRED_HTML = OUTBOX / "sendgrid-draft-expired-batchdata-42.html"
WITHDRAWN_HTML = OUTBOX / "sendgrid-draft-withdrawn-batchdata-42.html"
SENDGRID_KEY_PATH = CRM_DIR / "sendgrid_api_key.txt"  # Legacy fallback
SENDGRID_API = "https://api.sendgrid.com/v3/mail/send"
FROM_EMAIL = "mike@gullicksenrealty.com"
FROM_NAME = "Mike Gullicksen"
MAX_SENDS = 23


ASSETS = {
    "gullicksen-logo.png": Path("/Users/warden/gullicksen-realty/website/images/gullicksen-logo.png"),
    "footer-signature.jpg": Path("/Users/warden/gullicksen-realty/website/images/10496204_10152631403418453_9073215226705263273_o.jpg"),
    "expired-reset.png": Path("/Users/warden/gullicksen-realty/marketing/social-media-graphics/templates/instagram/ig-template-expired-reset.png"),
    "market-pulse.png": Path("/Users/warden/gullicksen-realty/marketing/social-media-graphics/templates/instagram/ig-template-market-pulse.png"),
}


def load_api_key() -> str:
    key = os.environ.get("SENDGRID_API_KEY", "").strip()
    if key:
        return key
    return SENDGRID_KEY_PATH.read_text().strip()


def load_recipients() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with RECIPIENT_CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))

    # Load CRM suppression list
    crm_suppressed = set()
    try:
        import sqlite3
        crm_db = Path("/Users/warden/.hermes/workspace/crm/crm.db")
        if crm_db.exists():
            conn = sqlite3.connect(crm_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
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
    skipped = []
    seen_emails = set()
    for row in rows:
        email = row.get("best_email", "").strip().lower()
        if row.get("review_status") != "candidate_review":
            skipped.append({**row, "skip_reason": "not_candidate_review"})
            continue
        if not email:
            skipped.append({**row, "skip_reason": "missing_email"})
            continue
        if email in crm_suppressed:
            skipped.append({**row, "skip_reason": "crm_suppressed"})
            continue
        if row.get("deceased") == "True" or row.get("litigator") == "True":
            skipped.append({**row, "skip_reason": "safety_suppression"})
            continue
        if row.get("listing_status") not in {"Expired", "Withdrawn"}:
            skipped.append({**row, "skip_reason": "unsupported_listing_status"})
            continue
        if email in seen_emails:
            skipped.append({**row, "skip_reason": "duplicate_email"})
            continue
        seen_emails.add(email)
        eligible.append(row)

    if len(eligible) > MAX_SENDS:
        raise SystemExit(f"Refusing to send {len(eligible)} emails; approval cap is {MAX_SENDS}.")
    return eligible, skipped


def text_from_row(row: dict[str, str]) -> str:
    first_name = first_name_from_owner(row.get("owner_name", ""))
    status = row["listing_status"]
    address = row["property_address"]
    city = row["property_city"]
    county = row["county"]
    if status == "Expired":
        body = f"""Hi {first_name},

My name is Mike Gullicksen with Gullicksen & Co. Realty with ERA Sunrise Realty in Canton.

I noticed your property at {address} in {city} recently came off the market as expired. I understand how frustrating it can be when a listing does not sell.

When a home expires, it is usually worth taking a fresh look at three things: pricing position, buyer reach, and how the property is presented online. I help sellers review those pieces clearly before they decide whether to relist.

If you are still considering selling, I would welcome a quick 10-minute conversation about what could be adjusted before going back on the market. No pressure, just honest market insight.

Would you be open to a brief conversation this week?
"""
    else:
        body = f"""Hi {first_name},

My name is Mike Gullicksen with Gullicksen & Co. Realty with ERA Sunrise Realty in Canton.

I noticed your property at {address} in {city} was recently withdrawn from the market. I understand circumstances change, and sometimes the best next step is to pause and reassess.

If selling is still on your mind, I would be happy to look at the listing strategy with you and talk through what might need to change before another attempt. That may include pricing position, buyer targeting, presentation, or timing.

No pressure and no obligation. I would simply be glad to give you a clear second opinion.

Would you be open to a brief conversation this week?
"""
    footer = f"""
Mike Gullicksen
770-825-2626
Agent | GA.432833
mike@gullicksenrealty.com
Gullicksen Realty & Co.
157 Reinhardt College Parkway, Canton, GA 30114
770-265-2480
gullicksenrealty.com

You're receiving this email because of a property listing record in the {county} area. We respect your privacy and will not share your information.
Unsubscribe: mailto:mike@gullicksenrealty.com?subject=Unsubscribe
"""
    return body + footer


def first_name_from_owner(owner_name: str) -> str:
    clean = owner_name.strip()
    if not clean:
        return "there"
    for sep in [" & ", " and ", ","]:
        clean = clean.split(sep)[0]
    first = clean.split()[0] if clean.split() else ""
    return first or "there"


def personalize_html(row: dict[str, str]) -> str:
    template = EXPIRED_HTML if row["listing_status"] == "Expired" else WITHDRAWN_HTML
    html = template.read_text()
    replacements = {
        "{first_name}": first_name_from_owner(row.get("owner_name", "")),
        "{property_address}": row.get("property_address", ""),
        "{city}": row.get("property_city", ""),
        "{county}": row.get("county", ""),
        "{{unsubscribe_url}}": "mailto:mike@gullicksenrealty.com?subject=Unsubscribe",
        "{{preferences_url}}": "mailto:mike@gullicksenrealty.com?subject=Email%20preferences",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return html


def asset_attachment(name: str) -> dict[str, str]:
    path = ASSETS[name]
    content_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return {
        "content": base64.b64encode(path.read_bytes()).decode("ascii"),
        "type": content_type,
        "filename": name,
        "disposition": "inline",
        "content_id": name,
    }


def attachments_for_status(status: str) -> list[dict[str, str]]:
    names = ["gullicksen-logo.png", "footer-signature.jpg"]
    names.append("expired-reset.png" if status == "Expired" else "market-pulse.png")
    return [asset_attachment(name) for name in names]


def subject_for_status(status: str, address: str) -> str:
    if status == "Expired":
        return f"Your {address} Listing Didn't Sell - Here's What Happened"
    return f"Your {address} Listing Was Pulled - Let's Talk"


def send_one(api_key: str, row: dict[str, str]) -> tuple[bool, str]:
    email = row["best_email"].strip()
    status = row["listing_status"]
    unsubscribe = "mailto:mike@gullicksenrealty.com?subject=Unsubscribe"
    payload = {
        "personalizations": [{
            "to": [{"email": email}],
            "custom_args": {
                "campaign": row.get("campaign", ""),
                "mls_number": row.get("mls_number", ""),
                "approved_scope": "batchdata_42_email_only",
            },
        }],
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "reply_to": {"email": FROM_EMAIL, "name": FROM_NAME},
        "subject": subject_for_status(status, row.get("property_address", "")),
        "content": [
            {"type": "text/plain", "value": text_from_row(row)},
            {"type": "text/html", "value": personalize_html(row)},
        ],
        "attachments": attachments_for_status(status),
        "headers": {
            "List-Unsubscribe": f"<{unsubscribe}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
        "categories": ["batchdata-42", status.lower()],
    }
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


def write_send_log(path: Path, sent: list[dict[str, str]], skipped: list[dict[str, str]]) -> None:
    fieldnames = [
        "timestamp",
        "send_status",
        "response",
        "email",
        "campaign",
        "mls_number",
        "listing_status",
        "property_address",
        "suppression_reason",
        "skip_reason",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sent:
            writer.writerow(row)
        for row in skipped:
            writer.writerow({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "send_status": "skipped",
                "response": "",
                "email": row.get("best_email", ""),
                "campaign": row.get("campaign", ""),
                "mls_number": row.get("mls_number", ""),
                "listing_status": row.get("listing_status", ""),
                "property_address": row.get("property_address", ""),
                "suppression_reason": row.get("suppression_reason", ""),
                "skip_reason": row.get("skip_reason", ""),
            })


def write_summary(path: Path, sent: list[dict[str, str]], skipped: list[dict[str, str]]) -> None:
    accepted = sum(1 for row in sent if row["send_status"] == "accepted")
    failed = sum(1 for row in sent if row["send_status"] == "failed")
    expired = sum(1 for row in sent if row["listing_status"] == "Expired" and row["send_status"] == "accepted")
    withdrawn = sum(1 for row in sent if row["listing_status"] == "Withdrawn" and row["send_status"] == "accepted")
    lines = [
        "# BatchData 42 SendGrid Campaign Send Summary",
        "",
        f"Run time: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Approved Scope",
        "",
        "- Approved by Mike: send the BatchData 42 email campaign only to reviewed eligible recipients in sendgrid-recipient-review-batchdata-42.csv.",
        "- No SMS or calls approved.",
        "- Templates used: approved Expired and Withdrawn draft HTML files.",
        "",
        "## Result",
        "",
        f"- Accepted by SendGrid: {accepted}",
        f"- Failed: {failed}",
        f"- Accepted Expired emails: {expired}",
        f"- Accepted Withdrawn emails: {withdrawn}",
        f"- Skipped rows: {len(skipped)}",
        "",
        "SendGrid HTTP 202 means accepted for delivery; it does not guarantee inbox placement.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    if not args.approved:
        raise SystemExit("Refusing to send without --approved.")

    recipients, skipped = load_recipients()
    api_key = load_api_key()
    sent_rows = []
    for row in recipients:
        ok, response = send_one(api_key, row)
        sent_rows.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "send_status": "accepted" if ok else "failed",
            "response": response,
            "email": row.get("best_email", ""),
            "campaign": row.get("campaign", ""),
            "mls_number": row.get("mls_number", ""),
            "listing_status": row.get("listing_status", ""),
            "property_address": row.get("property_address", ""),
            "suppression_reason": row.get("suppression_reason", ""),
            "skip_reason": "",
        })
        time.sleep(0.25)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = OUTBOX / f"sendgrid-batchdata-42-send-log-{stamp}.csv"
    summary_path = OUTBOX / f"sendgrid-batchdata-42-send-summary-{stamp}.md"
    write_send_log(log_path, sent_rows, skipped)
    write_summary(summary_path, sent_rows, skipped)

    # Run post-send health check
    try:
        subprocess.run([sys.executable, "/Users/warden/gullicksen-realty/tools/campaign_health_check.py"], check=False)
    except Exception:
        pass

    print(json.dumps({
        "accepted": sum(1 for row in sent_rows if row["send_status"] == "accepted"),
        "failed": sum(1 for row in sent_rows if row["send_status"] == "failed"),
        "skipped": len(skipped),
        "summary": str(summary_path),
        "log": str(log_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
