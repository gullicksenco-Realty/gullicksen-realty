#!/usr/bin/env python3
"""
Twilio A2P 10DLC Campaign Resubmission Script
Gullicksen Realty — 2026-05-24
"""

import json
import os
import urllib.request
import base64
import sys
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path("/Users/warden/.hermes/workspace/.env"))

# Load config
CRM_DIR = Path("/Users/warden/.hermes/workspace/crm")
CONFIG_PATH = CRM_DIR / "twilio_config.json"

def load_config():
    """Load from env first, fallback to JSON."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if account_sid and auth_token:
        config = {"account_sid": account_sid, "auth_token": auth_token}
        # Load remaining fields from JSON if available
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open() as f:
                json_config = json.load(f)
            for key in json_config:
                if key not in config:
                    config[key] = json_config[key]
        return config
    with CONFIG_PATH.open() as f:
        return json.load(f)

config = load_config()

ACCOUNT_SID = config['account_sid']
AUTH_TOKEN = config['auth_token']
BRAND_SID = config.get('brand_sid', '')
MESSAGING_SERVICE_SID = config.get('messaging_service_sid', '')
OLD_CAMPAIGN_SID = config.get('campaign_sid', '')

MESSAGE_FLOW = (
    "Consumer visits gullicksenrealty.com/sms-optin.html. The page says SMS is optional "
    "and separate from buying, selling, property info, callbacks, consultations, or services. "
    "Consumer enters name and phone. The SMS consent checkbox is separate, unchecked by default, "
    "and not required. If consumer leaves it unchecked and submits, the form still submits "
    "successfully; Gullicksen Realty may provide requested help by non-SMS methods such as phone "
    "call or email, and no SMS is sent. The success message confirms no SMS opt-in. If consumer "
    "checks the box and submits, Gullicksen Realty records opt-in source, timestamp, phone number, "
    "and consent language in the CRM. Only checked-box opt-ins receive optional SMS marketing "
    "updates. Gullicksen Realty does not text BatchData numbers, MLS expired/withdrawn owners, "
    "cold CRM leads, DNC contacts, or anyone without documented SMS opt-in."
)

OPT_IN_MESSAGE = (
    "Gullicksen Realty: You are subscribed to optional SMS updates. "
    "Msg frequency varies (avg 2-5/week). Msg and data rates may apply. "
    "Reply STOP to opt out. Reply HELP for help. "
    "Consent is not a condition of purchase or service. "
    "Privacy: gullicksenrealty.com/privacy.html Terms: gullicksenrealty.com/terms.html"
)

OPT_OUT_MESSAGE = (
    "You have been unsubscribed from Gullicksen Realty SMS alerts. "
    "You will not receive further messages. "
    "Reply HELP for assistance or visit gullicksenrealty.com to resubscribe."
)

HELP_MESSAGE = (
    "Gullicksen Realty SMS Help: You are subscribed to optional SMS updates from gullicksenrealty.com. "
    "Msg frequency varies (avg 2-5/week). Reply STOP to unsubscribe. "
    "Call (770) 265-2480 or email mike@gullicksenrealty.com. Data rates may apply."
)

MESSAGE_SAMPLES = [
    "Gullicksen Realty: Optional North Georgia real estate update. New market notes are available at gullicksenrealty.com. Reply STOP to opt out.",
    "Gullicksen Realty: Cherokee County market update. Inventory and buyer activity changed this week. Questions? Call (770) 265-2480. Reply STOP to opt out.",
    "Gullicksen Realty: Optional real estate update for subscribers. View current resources at gullicksenrealty.com or reply HELP for help. Reply STOP to opt out."
]


def twilio_api(method, path, data=None):
    url = f"https://messaging.twilio.com/v1{path}"
    credentials = base64.b64encode(f"{ACCOUNT_SID}:{AUTH_TOKEN}".encode()).decode()
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    encoded_data = None
    if data:
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return {'success': True, 'status': resp.status, 'body': json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return {'success': False, 'status': e.code, 'body': json.loads(body)}
        except:
            return {'success': False, 'status': e.code, 'body': body}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def check_brand():
    result = twilio_api('GET', f'/a2pBrandRegistrations/{BRAND_SID}')
    if result['success']:
        brand = result['body']
        print(f"Brand Status: {brand.get('brand_registration_status', 'unknown')}")
        return brand.get('brand_registration_status') == 'APPROVED'
    else:
        print(f"Brand check failed: {result.get('body', result.get('error'))}")
        return False


def create_campaign():
    campaign_data = {
        'BrandRegistrationSid': BRAND_SID,
        'MessagingServiceSid': MESSAGING_SERVICE_SID,
        'Description': 'Gullicksen Realty Optional SMS Updates - voluntary marketing SMS to web-form subscribers only',
        'UseCase': 'MIXED',
        'HasEmbeddedPhone': 'true',
        'HasEmbeddedLink': 'true',
        'MessageFlow': MESSAGE_FLOW,
        'OptInMessage': OPT_IN_MESSAGE,
        'OptOutMessage': OPT_OUT_MESSAGE,
        'HelpMessage': HELP_MESSAGE,
        'OptInKeywords': 'START,YES,ALERTS,PROPERTY',
        'OptOutKeywords': 'STOP,UNSUBSCRIBE,CANCEL,END,QUIT',
        'HelpKeywords': 'HELP,INFO',
    }
    for i, sample in enumerate(MESSAGE_SAMPLES):
        campaign_data[f'MessageSamples[{i}]'] = sample

    print("Creating new A2P campaign...")
    print(f"Brand: {BRAND_SID}")
    print(f"Messaging Service: {MESSAGING_SERVICE_SID}")
    print(f"Old campaign (rejected): {OLD_CAMPAIGN_SID}")
    print()

    result = twilio_api('POST', '/a2pCampaigns', campaign_data)

    if result['success']:
        campaign = result['body']
        print(f"Campaign created successfully!")
        print(f"   Campaign SID: {campaign.get('sid')}")
        print(f"   Status: {campaign.get('campaign_status')}")
        print(f"   Use Case: {campaign.get('use_case')}")
        return campaign
    else:
        print(f"Campaign creation failed:")
        print(f"   Status: {result.get('status')}")
        if isinstance(result.get('body'), dict):
            print(f"   Error: {result['body'].get('message', result['body'])}")
            print(f"   Code: {result['body'].get('code', 'N/A')}")
        else:
            print(f"   Response: {result.get('body', result.get('error'))}")
        return None


def print_manual_instructions():
    print("FALLBACK: Manual Console Submission")
    print("=" * 60)
    print()
    print("Go to: https://console.twilio.com/us1/develop/sms/senders/a2p-10dlc/campaigns")
    print()
    print("Click 'Create New Campaign' and enter:")
    print()
    print(f"Brand Registration SID: {BRAND_SID}")
    print(f"Messaging Service SID: {MESSAGING_SERVICE_SID}")
    print()
    print("CAMPAIGN DESCRIPTION:")
    print("Gullicksen Realty Optional SMS Updates - voluntary marketing SMS to web-form subscribers only")
    print()
    print("USE CASE: Mixed (Marketing + Customer Care)")
    print("Has Embedded Phone: Yes")
    print("Has Embedded Link: Yes")
    print()
    print("MESSAGE FLOW (PASTE EXACTLY):")
    print(MESSAGE_FLOW)
    print()
    print("OPT-IN MESSAGE (PASTE EXACTLY):")
    print(OPT_IN_MESSAGE)
    print()
    print("OPT-OUT MESSAGE (PASTE EXACTLY):")
    print(OPT_OUT_MESSAGE)
    print()
    print("HELP MESSAGE (PASTE EXACTLY):")
    print(HELP_MESSAGE)
    print()
    print("MESSAGE SAMPLES:")
    for i, sample in enumerate(MESSAGE_SAMPLES, 1):
        print(f"  {i}. {sample}")
    print()
    print("OPT-IN KEYWORDS: START, YES, ALERTS, PROPERTY")
    print("OPT-OUT KEYWORDS: STOP, UNSUBSCRIBE, CANCEL, END, QUIT")
    print("HELP KEYWORDS: HELP, INFO")
    print()


def main():
    print("=" * 60)
    print("Twilio A2P 10DLC Campaign Resubmission")
    print("Gullicksen Realty - 2026-05-24")
    print("=" * 60)
    print()

    print("Step 1: Verifying brand status...")
    brand_ok = check_brand()
    if not brand_ok:
        print("Warning: Brand not approved. Campaign creation may fail.")
    print()

    print("Step 2: Creating new campaign...")
    campaign = create_campaign()
    print()

    if campaign:
        config['new_campaign_sid'] = campaign.get('sid')
        config['new_campaign_status'] = campaign.get('campaign_status')
        config['resubmitted_at'] = '2026-05-24T18:00:00Z'
        config['resubmission_reason'] = 'Fixed MESSAGE_FLOW for error 30923'

        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)

        print("Configuration updated with new campaign SID.")
        print()
        print("Next steps:")
        print("1. Twilio will review the campaign (typically 1-3 business days)")
        print("2. Monitor campaign status in Twilio Console")
        print("3. If approved, update messaging service to use new campaign")
        print()
        print("Resubmission complete.")
        return 0
    else:
        print("API submission failed.")
        print()
        print_manual_instructions()
        return 1


if __name__ == "__main__":
    sys.exit(main())
