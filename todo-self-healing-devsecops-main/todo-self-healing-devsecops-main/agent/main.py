"""
Self-Healing CI/CD Agent
========================
Triggered by GitLab CI when a pipeline stage fails (when: on_failure).
Flow:
  1. Find which job(s) failed in this pipeline
  2. Fetch the error log (trace) of the first failed job
  3. Determine which source file to fix
  4. Ask Mistral AI to generate a fix
  5. Write the fix to disk
  6. Run the test suite to validate
  7. Commit & push if valid → triggers a new pipeline
  8. Notify via Telegram at every key step
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from gitlab_monitor import get_failed_jobs, get_job_trace
from mistral_fix import generate_fix
from patcher import overwrite_file
from validator import validate_fix
from git_handler import commit_and_push
from telegram_notify import send_failure_alert, send_success_alert, send_give_up_alert

# Map job names → the file to fix.
# Add more mappings as your project grows.
JOB_FILE_MAP = {
    "test-job":   "public/app.js",
    "build-job":  "server.js",
    "default":    "public/app.js",   # fallback
}

PIPELINE_ID = os.getenv("CI_PIPELINE_ID", "unknown")
BRANCH = os.getenv("CI_COMMIT_BRANCH", "main")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def pick_target_file(job_name):
    for key, filepath in JOB_FILE_MAP.items():
        if key in job_name:
            return filepath
    return JOB_FILE_MAP["default"]


def main():
    print(f"[main] Self-healing agent started — pipeline #{PIPELINE_ID}, branch '{BRANCH}'")

    # ── Step 1: Find failed jobs ──────────────────────────────────────────────
    try:
        failed_jobs = get_failed_jobs()
    except Exception as e:
        print(f"[main] Could not fetch failed jobs: {e}")
        sys.exit(1)

    if not failed_jobs:
        print("[main] No failed jobs found — nothing to do")
        sys.exit(0)

    job = failed_jobs[0]
    job_name = job.get("name", "unknown")
    job_id = job["id"]
    print(f"[main] Targeting job: '{job_name}' (id={job_id})")

    # ── Step 2: Get the error log ─────────────────────────────────────────────
    try:
        trace = get_job_trace(job_id)
    except Exception as e:
        msg = f"Could not fetch job trace: {e}"
        print(f"[main] {msg}")
        send_give_up_alert(PIPELINE_ID, job_name, msg)
        sys.exit(1)

    # Send Telegram alert about the failure
    error_summary = trace[-1200:] if len(trace) > 1200 else trace  # last 1200 chars
    send_failure_alert(job_name, PIPELINE_ID, error_summary)

    # ── Step 3: Choose file to fix ────────────────────────────────────────────
    target_file = pick_target_file(job_name)
    target_path = os.path.join(PROJECT_ROOT, target_file)
    print(f"[main] Will attempt to fix: {target_file}")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            broken_code = f.read()
    except FileNotFoundError:
        msg = f"Target file not found: {target_path}"
        print(f"[main] {msg}")
        send_give_up_alert(PIPELINE_ID, job_name, msg)
        sys.exit(1)

    # ── Step 4: Generate fix via Mistral ──────────────────────────────────────
    print("[main] Requesting fix from Mistral AI...")
    try:
        fixed_code = generate_fix(trace, broken_code, filename=target_file)
    except Exception as e:
        msg = f"Mistral AI request failed: {e}"
        print(f"[main] {msg}")
        send_give_up_alert(PIPELINE_ID, job_name, msg)
        sys.exit(1)

    if not fixed_code.strip():
        msg = "Mistral returned an empty fix"
        print(f"[main] {msg}")
        send_give_up_alert(PIPELINE_ID, job_name, msg)
        sys.exit(1)

    # ── Step 5: Write the fix ─────────────────────────────────────────────────
    overwrite_file(target_path, fixed_code)

    # ── Step 6: Validate ──────────────────────────────────────────────────────
    print("[main] Validating fix...")
    if validate_fix():
        # ── Step 7: Commit & push ─────────────────────────────────────────────
        try:
            pushed = commit_and_push(
                PROJECT_ROOT,
                f"fix: self-healing patch for '{job_name}' in pipeline #{PIPELINE_ID}"
            )
        except Exception as e:
            msg = f"Git push failed: {e}"
            print(f"[main] {msg}")
            send_give_up_alert(PIPELINE_ID, job_name, msg)
            sys.exit(1)

        if pushed:
            send_success_alert(PIPELINE_ID, job_name, BRANCH)
            print("[main] ✅ Self-healing complete — fix pushed!")
        else:
            print("[main] Fix was valid but no changes were detected to push")
    else:
        msg = "Test suite still fails after applying AI fix"
        print(f"[main] {msg}")
        send_give_up_alert(PIPELINE_ID, job_name, msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
