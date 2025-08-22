import json
import socket
import sys
import time
from datetime import datetime, timezone
import platform
import psutil
import requests

CONFIG_FILE = "./agent_config.json"

def load_config(path=CONFIG_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def collect_processes():
    for p in psutil.process_iter(attrs=[]):
        try:
            p.cpu_percent(interval=None)
        except psutil.Error:
            pass

    time.sleep(0.2)

    processes = []
    for p in psutil.process_iter(attrs=['pid', 'ppid', 'name', 'memory_info']):
        try:
            info = p.info
            cpu = p.cpu_percent(interval=None)
            mem = info.get('memory_info').rss if info.get('memory_info') else 0
            processes.append({
                "pid": int(info.get('pid', -1)),
                "ppid": int(info.get('ppid', -1)),
                "name": info.get('name') or "unknown",
                "cpu_percent": float(cpu),
                "memory_rss": int(mem),
                "memory_percent": float(p.memory_percent()),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return processes

def collect_system_details():
    uname = platform.uname()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "operating_system": uname.system,
        "processor": uname.processor,
        "number_of_cores": psutil.cpu_count(logical=False),
        "number_of_threads": psutil.cpu_count(logical=True),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "ram_available_gb": round(mem.available / (1024 ** 3), 2),
        "ram_used_gb": round(mem.total / (1024 ** 3), 2) - round(mem.available / (1024 ** 3), 2),
        "storage_total_gb": round(disk.total / (1024 ** 3), 2),
        "storage_used_gb": round(disk.total / (1024 ** 3), 2) - round(disk.free / (1024 ** 3), 2),
        "storage_free_gb": round(disk.free / (1024 ** 3), 2)
    }

def payload():
    return {
        "hostname": socket.gethostname(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "processes": collect_processes(),
        "system_details": collect_system_details()
    }

def main():
    try:
        cfg = load_config()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)
    try:
        data = payload()
        resp = requests.post(
            cfg["api_url"],
            json=data,
            headers={"X-API-KEY": cfg["api_key"]},
            timeout=cfg.get("timeout_seconds", 10),
        )
        if resp.status_code >= 400:
            print(f"Server returned {resp.status_code}: {resp.text}")
            sys.exit(2)
        print("Process and system snapshot sent successfully.")
    except requests.RequestException as e:
        print(f"Network error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()