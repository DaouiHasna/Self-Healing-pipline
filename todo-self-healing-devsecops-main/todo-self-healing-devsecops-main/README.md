# Self-Healing CI/CD — Todo App

A GitLab CI/CD pipeline that **automatically detects failures, asks Mistral AI to fix the broken code, validates the fix, and pushes a corrected commit** — all without human intervention.

## How it works

```
Push → build → test → security
                ↓ (on failure)
           self-heal-job
              │
              ├─ 1. Fetch failed job log from GitLab API
              ├─ 2. Send Telegram alert 🔴
              ├─ 3. Ask Mistral AI for a fix
              ├─ 4. Write fixed code to disk
              ├─ 5. Run npm test to validate
              ├─ 6. git commit + push (triggers new pipeline)
              └─ 7. Send Telegram alert ✅ or ❌
```

## Setup

### 1. Clone and install
```bash
npm install
pip install -r requirements.txt
cp .env.example .env
# Fill in your .env values
```

### 2. Set GitLab CI/CD variables
Go to **GitLab → Your project → Settings → CI/CD → Variables** and add:

| Variable | Description |
|---|---|
| `MISTRAL_API_KEY` | From [console.mistral.ai](https://console.mistral.ai) |
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Your chat/group ID |
| `GITLAB_TOKEN` | Personal Access Token with `api` + `write_repository` scopes |

### 3. Enable pipeline token write access
Go to **Settings → CI/CD → Token Access** and ensure `CI_JOB_TOKEN` can push to the repository (or use your `GITLAB_TOKEN`).

### 4. Run locally
```bash
# Run tests
npm test

# Run self-healing agent manually (requires .env)
python agent/main.py
```

## Files

```
├── .gitlab-ci.yml          # Pipeline definition
├── server.js               # Express API server
├── public/
│   ├── app.js              # Core todo logic (what gets fixed)
│   └── index.html          # Frontend
├── tests/
│   └── app.test.js         # Jest test suite
├── data/
│   └── tasks.json          # JSON "database"
├── agent/
│   ├── main.py             # Orchestrator
│   ├── gitlab_monitor.py   # Fetches failed job info from GitLab API
│   ├── mistral_fix.py      # Calls Mistral AI for a code fix
│   ├── patcher.py          # Writes the fix to disk
│   ├── validator.py        # Runs npm test to check the fix
│   ├── git_handler.py      # Commits and pushes the fix
│   └── telegram_notify.py  # Sends Telegram notifications
├── requirements.txt        # Python dependencies
└── .env.example            # Environment variable template
```

## Adding more files to fix

Edit `JOB_FILE_MAP` in `agent/main.py`:

```python
JOB_FILE_MAP = {
    "test-job":   "public/app.js",
    "build-job":  "server.js",
    "lint-job":   "public/app.js",
    "default":    "public/app.js",
}
```
