import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Always prefer the Personal Access Token (GITLAB_TOKEN) over CI_JOB_TOKEN
# CI_JOB_TOKEN does NOT have permission to read pipeline jobs via the API
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
PROJECT_ID   = os.getenv("PROJECT_ID") or os.getenv("CI_PROJECT_ID")
GITLAB_URL   = os.getenv("GITLAB_URL") or os.getenv("CI_SERVER_URL", "https://gitlab.com")
PIPELINE_ID  = os.getenv("CI_PIPELINE_ID")

if not GITLAB_TOKEN:
    raise EnvironmentError(
        "GITLAB_TOKEN is not set. "
        "Create a Personal Access Token with 'api' scope at "
        "GitLab → User Settings → Access Tokens and add it as a CI/CD variable."
    )

HEADERS = {"PRIVATE-TOKEN": GITLAB_TOKEN}


def get_failed_jobs():
    """Get failed jobs from the current pipeline."""
    if PIPELINE_ID:
        url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines/{PIPELINE_ID}/jobs"
    else:
        # Local/manual run — use the latest pipeline
        resp = requests.get(
            f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines?per_page=1",
            headers=HEADERS
        )
        resp.raise_for_status()
        pipelines = resp.json()
        if not pipelines:
            return []
        url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines/{pipelines[0]['id']}/jobs"

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    jobs = response.json()
    failed = [job for job in jobs if job["status"] == "failed"]
    print(f"[monitor] Found {len(failed)} failed job(s) in pipeline {PIPELINE_ID or 'latest'}")
    return failed


def get_job_trace(job_id):
    """Download the full log of a specific job."""
    url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/jobs/{job_id}/trace"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text
