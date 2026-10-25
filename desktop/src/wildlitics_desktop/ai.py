"""Run the official SpeciesNet CLI in a separate, explicitly selected environment."""
from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import signal
import subprocess
import threading

SPECIESNET_VERSION = "5.0.6"
DEFAULT_MODEL = "kaggle:google/speciesnet/pyTorch/v4.0.3a/1"


def default_ai_python():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "Wildlitics" / "ai-runtime"
    return str(base / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))


def command_for_run(python, run):
    executable = Path(python).expanduser()
    if not executable.is_file():
        raise ValueError("Select the Python executable from an installed SpeciesNet AI environment")
    params = json.loads(run["parameters"])
    folder = Path(run["folder"])
    return [str(executable), "-u", "-m", "speciesnet.scripts.run_model",
            "--model", params["model"], "--instances_json", str(folder / "instances.json"),
            "--predictions_json", str(folder / "predictions.json"),
            "--detection_threshold_for_classification", str(params["threshold"]),
            "--max_classifications_per_detection", "5", "--batch_size", "4",
            "--run_mode", "multi_thread", "--bypass_prompts", "--noprogress_bars"]


def runtime_command(python):
    return [str(python), "-c", "import importlib.metadata as m; import torch, speciesnet; "
            "print('SpeciesNet',m.version('speciesnet')); print('PyTorch',torch.__version__); "
            "print('Device: '+('CUDA' if torch.cuda.is_available() else 'CPU')); "
            f"assert m.version('speciesnet')=='{SPECIESNET_VERSION}', 'Use SpeciesNet {SPECIESNET_VERSION}'"]


def _stop(process):
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
    except (OSError, subprocess.SubprocessError):
        process.kill()


def run_process(command, log_path, *, cancelled=None, on_line=None):
    """Stream logs and support cancellation even while the child emits no output."""
    event = cancelled or threading.Event()
    if event.is_set():
        return {"returncode": None, "cancelled": True, "tail": "Cancelled before launch"}
    env = os.environ.copy()
    env.update({"PYTHONUNBUFFERED": "1", "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4"})
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               text=True, encoding="utf-8", errors="replace", env=env, **kwargs)
    finished = threading.Event()

    def watch():
        while not finished.wait(.15):
            if event.is_set():
                _stop(process)
                return

    monitor = threading.Thread(target=watch, daemon=True)
    monitor.start()
    tail = deque(maxlen=45)
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log_path.open("a", encoding="utf-8") as log:
            for line in process.stdout:
                log.write(line)
                log.flush()
                tail.append(line.rstrip())
                if on_line:
                    on_line(line.rstrip())
        code = process.wait()
    finally:
        finished.set()
        if process.poll() is None:
            _stop(process)
        process.stdout.close()
        monitor.join(timeout=2)
    return {"returncode": code, "cancelled": event.is_set(), "tail": "\n".join(tail)}
