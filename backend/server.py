from flask import Flask, request, jsonify, render_template
import subprocess
import webbrowser
import os
import json
import threading

import psutil
# ...existing code...

def is_pid_running(pid):
    """Return True if process with pid is running, else False."""
    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'), static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.default.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
APP_SEARCH_DIRECTORIES = config.get('appSearchDirectories', [])

def stream_output(stream, prefix):
    for line in iter(stream.readline, ''):
        if line:
            print(f"{prefix}: {line.strip()}")
    stream.close()

def monitor_process(process, app_name):
    process.wait()
    print(f"Process {app_name} with PID {process.pid} has terminated.")

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

def find_app_executable(app_filename):
    # Search for the executable in APP_SEARCH_DIRECTORIES
    for directory in APP_SEARCH_DIRECTORIES:
        app_path = os.path.join(directory, app_filename)
        if os.path.isfile(app_path):
            return app_path
    # Fallback: search in PATH
    return app_filename

# Configuration
APPS = {
    "COVISE": "covise.exe",
    "OpenCOVER": "opencover.exe",
    "opencover": "opencover.exe",
    "Notepad": "notepad.exe",
}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/demos', methods=['GET'])
def get_demos():
    demos_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'demos.json')
    with open(demos_path, 'r') as f:
        demos = json.load(f)
    return jsonify({"demos": demos})

@app.route('/launch_demo', methods=['POST'])
def launch_demo():
    data = request.json
    for entry in data.get('launch', []):
        program = entry['program']
        args = entry.get('args', [])
        exe_path = find_app_executable(APPS[program])
        env_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'covise.env')
        env_vars = load_env_vars(env_path)
        env = os.environ.copy()
        for k, v in env_vars.items():
            if k.lower() == "path":
                env["PATH"] = v
            else:
                env[k] = v
        subprocess.Popen(
            [exe_path] + args,
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    return jsonify({"status": "success"})

@app.route('/launch', methods=['POST'])
def launch_app():
    app_name = request.json.get('app')
    print(f"Launching app: {app_name}")
    if app_name in APPS:
        exe_path = find_app_executable(APPS[app_name])
        print(f"Executable path: {exe_path}")
        # Load environment variables from covise.env
        env_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'covise.env')
        env_vars = load_env_vars(env_path)
        try:
            env = os.environ.copy()
            env.update(env_vars)
            process = subprocess.Popen(
                exe_path,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # For string output instead of bytes
            )
            # Start a thread to print stderr in real time
            threading.Thread(target=stream_output, args=(process.stderr, "STDERR"), daemon=True).start()
            threading.Thread(target=monitor_process, args=(process, app_name), daemon=True).start()
            return jsonify({"status": "success", "pid": process.pid})
        except Exception as e:
            print(f"Error launching app: {e}")
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "App not found"})

@app.route('/apps', methods=['GET'])
def get_apps():
    return jsonify({"apps": list(APPS.keys())})

if __name__ == '__main__':
    # Auto-open browser
    webbrowser.open('http://localhost:5000')
    app.run(port=5000)