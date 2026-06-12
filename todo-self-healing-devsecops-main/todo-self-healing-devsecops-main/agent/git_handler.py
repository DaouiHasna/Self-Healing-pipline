import subprocess
import os
from urllib.parse import urlparse


def commit_and_push(repo_path, message):
    project_root = os.path.abspath(repo_path)

    # Configure git identity
    git_user  = os.getenv("GIT_USER_NAME", "Self-Healing Bot")
    git_email = os.getenv("GIT_USER_EMAIL", "ci-bot@self-healing.local")
    _run(["git", "config", "user.name", git_user], project_root)
    _run(["git", "config", "user.email", git_email], project_root)

    # ── Auth: prefer Personal Access Token, fall back to CI_JOB_TOKEN ────────
    gitlab_token    = os.getenv("GITLAB_TOKEN")          # Personal Access Token
    ci_token        = os.getenv("CI_JOB_TOKEN")          # Short-lived job token
    ci_project_url  = os.getenv("CI_PROJECT_URL", "")    # e.g. https://gitlab.com/user/repo
    ci_project_path = os.getenv("CI_PROJECT_PATH", "")   # e.g. user/repo
    ci_server_host  = os.getenv("CI_SERVER_HOST", "gitlab.com")

    if gitlab_token and ci_project_path:
        # Most reliable — Personal Access Token with write_repository scope
        auth_url = f"https://oauth2:{gitlab_token}@{ci_server_host}/{ci_project_path}.git"
        _run(["git", "remote", "set-url", "origin", auth_url], project_root)
        print("[git] Using GITLAB_TOKEN (Personal Access Token) for push")
    elif ci_token and ci_project_url:
        # Fallback — requires Token Access to be enabled in GitLab project settings
        parsed = urlparse(ci_project_url)
        auth_url = f"{parsed.scheme}://gitlab-ci-token:{ci_token}@{parsed.netloc}{parsed.path}.git"
        _run(["git", "remote", "set-url", "origin", auth_url], project_root)
        print("[git] Using CI_JOB_TOKEN for push")
    else:
        print("[git] WARNING: No auth token found — push may fail")

    # ── Stage and commit ──────────────────────────────────────────────────────
    _run(["git", "add", "-A"], project_root)

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root, capture_output=True, text=True
    )
    if not status.stdout.strip():
        print("[git] Nothing to commit — fix did not change any files")
        return False

    _run(["git", "commit", "-m", message], project_root)

    # ── Push ──────────────────────────────────────────────────────────────────
    branch = os.getenv("CI_COMMIT_BRANCH") or _get_current_branch(project_root)
    print(f"[git] Pushing to branch: {branch}")
    _run(["git", "push", "origin", f"HEAD:{branch}"], project_root)
    print("[git] Push successful")
    return True


def _run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {' '.join(cmd)}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    return result.stdout


def _get_current_branch(repo_path):
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path, capture_output=True, text=True
    )
    return result.stdout.strip() or "main"
