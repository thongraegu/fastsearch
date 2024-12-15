import os
import subprocess
import sys
import urllib.request

APP_DIR = "FastSearchApp"
VENV_DIR = os.path.join(APP_DIR, "venv")
FASTSEARCH_URL = "https://raw.githubusercontent.com/thongraegu/fastsearch/main/fastsearch.py"
FASTSEARCH_PY = os.path.join(APP_DIR, "fastsearch.py")

def run_command(cmd, shell=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell)
    if result.returncode != 0:
        sys.exit(f"Command failed with exit code {result.returncode}")

def main():
    # 1. Create folder if not exists
    if not os.path.exists(APP_DIR):
        os.mkdir(APP_DIR)

    # 2. Create a virtual environment
    if not os.path.exists(VENV_DIR):
        run_command(f"python -m venv {VENV_DIR}")

    # Determine python binary inside the venv
    python_bin = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(VENV_DIR, "bin", "python")

    # 3. Download fastsearch.py from GitHub
    print("Downloading fastsearch.py...")
    urllib.request.urlretrieve(FASTSEARCH_URL, FASTSEARCH_PY)

    # 4. Upgrade pip and install dependencies
    run_command(f"{python_bin} -m pip install --upgrade pip")
    run_command(f"{python_bin} -m pip install PyQt5 pyinstaller")

    # Change working directory to APP_DIR so pyinstaller runs inside it
    os.chdir(APP_DIR)

    # 5. Run pyinstaller to build the executable
    run_command(f"{python_bin} -m PyInstaller --name FastSearch --onefile --windowed fastsearch.py")

    print("Build complete. Check the 'dist' folder inside 'FastSearchApp' for the FastSearch executable.")

if __name__ == "__main__":
    main()
