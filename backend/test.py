import subprocess
import os

def load_env_vars(env_path):
    env = {}
    if os.path.isfile(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    return env

env_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'covise.env')
env_vars = load_env_vars(env_path)

# Path to the covise executable
covise_executable = r"C:\Users\Dennis\Apps\covise\zebu\bin\covise.exe"

# Optional: Set working directory or environment variables if needed
working_dir = os.path.dirname(covise_executable)
env = os.environ.copy()
env.update(env_vars)
print("Merged env:", {k: env[k] for k in env_vars.keys()})
# Launch covise
try:
    subprocess.Popen([covise_executable], cwd=working_dir, env=env)
    print("COVISE launched successfully.")
except FileNotFoundError:
    print("COVISE executable not found at:", covise_executable)
except Exception as e:
    print("Error launching COVISE:", e)