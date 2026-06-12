import subprocess
import sys
import os


def validate_fix():
    """
    Run the test suite to verify the fix works.
    Installs Node deps first if node_modules is missing.
    Returns True if tests pass, False otherwise.
    """
    # Make sure we run from project root (one level up from agent/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Install node_modules if they're not there
    if not os.path.isdir(os.path.join(project_root, "node_modules")):
        print("[validator] node_modules not found, running npm install...")
        install = subprocess.run(
            ["npm", "install"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if install.returncode != 0:
            print("[validator] npm install failed:")
            print(install.stdout)
            print(install.stderr)
            return False

    print("[validator] Running npm test...")
    result = subprocess.run(
        ["npm", "test"],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    passed = result.returncode == 0
    print(f"[validator] Tests {'PASSED' if passed else 'FAILED'}")
    return passed
