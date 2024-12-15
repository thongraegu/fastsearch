import os
import subprocess
import urllib.request
import sys

# Define the script location
script_location = os.path.dirname(os.path.abspath(__file__))

# Create the "fastsearch" folder
fastsearch_folder = os.path.join(script_location, "fastsearch")
os.makedirs(fastsearch_folder, exist_ok=True)

# Set up the virtual environment
venv_folder = os.path.join(fastsearch_folder, "venv")
subprocess.run([sys.executable, "-m", "venv", venv_folder], check=True)

# Function to run commands in the virtual environment
def run_in_venv(command):
    if os.name == "nt":
        activate_script = os.path.join(venv_folder, "Scripts", "activate.bat")
        command = f'cmd /c "{activate_script} && {command}"'
    else:
        activate_script = os.path.join(venv_folder, "bin", "activate")
        command = f'bash -c "source {activate_script} && {command}"'
    subprocess.run(command, shell=True, check=True)

# Download the fastsearch.py file
fastsearch_url = "https://raw.githubusercontent.com/thongraegu/fastsearch/main/fastsearch.py"
fastsearch_file = os.path.join(fastsearch_folder, "fastsearch.py")
urllib.request.urlretrieve(fastsearch_url, fastsearch_file)

# Install the required libraries
run_in_venv(f"{os.path.join(venv_folder, 'Scripts', 'pip')} install PyQt5 pyinstaller")

# Create the .exe file using PyInstaller with the --windowed flag
run_in_venv(f"{os.path.join(venv_folder, 'Scripts', 'pyinstaller')} --name FastSearch --onefile --windowed {fastsearch_file}")

print("Script execution completed successfully.")
