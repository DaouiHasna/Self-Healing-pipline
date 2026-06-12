import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")


def generate_fix(error_log, broken_code, filename="unknown"):
    """Ask Mistral to fix the broken code based on the error log."""
    if not API_KEY:
        raise ValueError("MISTRAL_API_KEY is not set in environment or .env file")

    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert software engineer. "
                    "You receive a CI/CD error log and the broken source file. "
                    "Return ONLY the corrected code with NO explanation, NO markdown fences, NO preamble. "
                    "The output must be valid, runnable source code only."
                )
            },
            {
                "role": "user",
                "content": (
                    f"FILE: {filename}\n\n"
                    f"ERROR LOG:\n{error_log}\n\n"
                    f"BROKEN CODE:\n{broken_code}"
                )
            }
        ],
        "temperature": 0.1,  # Low temperature = more deterministic/safe fix
        "max_tokens": 4096
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    fixed_code = result["choices"][0]["message"]["content"]

    # Strip accidental markdown fences if Mistral adds them anyway
    if fixed_code.startswith("```"):
        lines = fixed_code.splitlines()
        # Remove first and last fence lines
        fixed_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return fixed_code
