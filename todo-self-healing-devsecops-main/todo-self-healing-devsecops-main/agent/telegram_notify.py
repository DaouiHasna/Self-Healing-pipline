import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message):
    """Send a message to Telegram. Silently skips if credentials are not set."""
    if not BOT_TOKEN or not CHAT_ID:
        print("[telegram] BOT_TOKEN or CHAT_ID not set — skipping notification")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # Allows <b>, <code> tags in messages
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[telegram] Message sent successfully")
    except Exception as e:
        print(f"[telegram] Failed to send message: {e}")


def send_failure_alert(job_name, pipeline_id, error_summary):
    """Send a structured failure notification."""
    msg = (
        f"🔴 <b>CI/CD Pipeline Failed</b>\n\n"
        f"<b>Pipeline:</b> #{pipeline_id}\n"
        f"<b>Failed job:</b> <code>{job_name}</code>\n\n"
        f"<b>Error summary:</b>\n<code>{error_summary[:800]}</code>\n\n"
        f"🤖 Self-healing agent is attempting a fix..."
    )
    send_telegram_message(msg)


def send_success_alert(pipeline_id, job_name, branch):
    """Send a structured success notification."""
    msg = (
        f"✅ <b>Self-Healing Successful</b>\n\n"
        f"<b>Pipeline:</b> #{pipeline_id}\n"
        f"<b>Fixed job:</b> <code>{job_name}</code>\n"
        f"<b>Branch:</b> <code>{branch}</code>\n\n"
        f"Fix committed and pushed. New pipeline triggered."
    )
    send_telegram_message(msg)


def send_give_up_alert(pipeline_id, job_name, reason):
    """Send an alert when self-healing fails."""
    msg = (
        f"❌ <b>Self-Healing Failed</b>\n\n"
        f"<b>Pipeline:</b> #{pipeline_id}\n"
        f"<b>Job:</b> <code>{job_name}</code>\n"
        f"<b>Reason:</b> {reason}\n\n"
        f"⚠️ Manual intervention required."
    )
    send_telegram_message(msg)
