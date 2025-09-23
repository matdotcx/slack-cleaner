import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

ADMIN_USER_IDS = set(os.environ.get("ADMIN_USER_IDS", "").split(","))
ADMIN_REVIEW_CHANNEL = os.environ.get("ADMIN_REVIEW_CHANNEL")
AUDIT_LOG_CHANNEL = os.environ.get("AUDIT_LOG_CHANNEL")

PORT = int(os.environ.get("PORT", 3000))

AUTO_APPROVE_MINUTES = int(os.environ.get("AUTO_APPROVE_MINUTES", 0))

def is_admin(user_id: str) -> bool:
    return user_id in ADMIN_USER_IDS

def validate_config():
    required = {
        "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
        "SLACK_USER_TOKEN": SLACK_USER_TOKEN,
        "SLACK_SIGNING_SECRET": SLACK_SIGNING_SECRET,
        "SLACK_APP_TOKEN": SLACK_APP_TOKEN,
        "ADMIN_REVIEW_CHANNEL": ADMIN_REVIEW_CHANNEL,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    if not ADMIN_USER_IDS or not list(ADMIN_USER_IDS)[0]:
        raise ValueError("At least one admin user ID must be configured in ADMIN_USER_IDS")