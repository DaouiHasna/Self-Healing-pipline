import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID")
PIPELINE_ID = os.getenv("CI_PIPELINE_ID", "?")
BRANCH      = os.getenv("CI_COMMIT_BRANCH", "?")
PROJECT_URL = os.getenv("CI_PROJECT_URL", "")


def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("[notify] Credentials not set — skipping")
        return

    pipeline_link = f"{PROJECT_URL}/-/pipelines/{PIPELINE_ID}" if PROJECT_URL else f"#{PIPELINE_ID}"

    msg = (
        f"✅ Pipeline Passed\n\n"
        f"Branch: {BRANCH}\n"
        f"Pipeline: {pipeline_link}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)

    if resp.ok:
        print("[notify] ✅ Success notification sent")
    else:
        print(f"[notify] Failed: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    main()
