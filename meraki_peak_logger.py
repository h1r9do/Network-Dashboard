#!/usr/bin/env python3

import os
import requests
import time
import datetime
import json
import re
import pandas as pd
import numpy as np
import glob
import threading
import queue
import logging
from dotenv import load_dotenv

# --- Setup logging ---
LOG_FILE = "/var/log/meraki_peak_logger.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# ANSI colors for console output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Load API keys
load_dotenv('/usr/local/bin/meraki.env')
api_keys = [v for k, v in os.environ.items() if k.startswith("MERAKI_API_KEY")]
API_KEYS = sorted(api_keys)
KEY_COUNT = len(API_KEYS)
logging.info(f"🔑 Using {KEY_COUNT} API keys.")

PRIMARY_DEST_IP = "208.67.222.222"
FALLBACK_DEST_IP = "8.8.8.8"

DATA_DIR = "/var/www/html/meraki-data"
os.makedirs(DATA_DIR, exist_ok=True)

MAX_TIMESPAN = 900
RESOLUTION = 60
REQUEST_DELAY = 20.00
FAILED_DEVICES = []
RATE_LIMIT_HITS = 0

job_queue = queue.Queue()
cycle_counter = 0
lock = threading.Lock()

# --- Console helper functions ---

def console_success(msg):
    print(f"{GREEN}{msg}{RESET}", flush=True)
    logging.info(msg)

def console_error(msg):
    print(f"{RED}{msg}{RESET}", flush=True)
    logging.error(msg)

def console_info(msg):
    print(msg, flush=True)
    logging.info(msg)

# --- General helpers ---

def convert_numpy_types(obj):
    if isinstance(obj, (pd.Timestamp, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    return obj

def is_valid_store(name):
    name = name.strip().upper()
    if "00" in name:
        return False
    return bool(re.match(r"^[A-Z]+ \d{2}$", name))

def load_latest_inventory():
    files = glob.glob(os.path.join(DATA_DIR, "mx_inventory_live_*.json"))
    if not files:
        raise FileNotFoundError("No inventory files found")
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file) as f:
        data = json.load(f)
    devices = data.get("devices", [])
    filtered = [d for d in devices if is_valid_store(d.get("network_name", ""))]
    return sorted(filtered, key=lambda d: d.get("network_name", "").strip().upper()), latest_file

def make_api_request(url, api_key, params=None):
    global RATE_LIMIT_HITS, REQUEST_DELAY
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    for attempt in range(3):
        try:
            time.sleep(REQUEST_DELAY)
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 429:
                with lock:
                    RATE_LIMIT_HITS += 1
                wait = int(response.headers.get("Retry-After", 1))
                console_error(f"⚠️  Rate limit hit. Waiting {wait}s... (Attempt {attempt+1})")
                time.sleep(wait)
                if RATE_LIMIT_HITS > 10 and REQUEST_DELAY < 2.0:
                    REQUEST_DELAY += 0.25
                    console_info(f"⚙️ Increased REQUEST_DELAY to {REQUEST_DELAY:.2f}s due to rate limits.")
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            console_error(f"❌ HTTP error {response.status_code}: {response.text.strip()} (Attempt {attempt+1})")
            if attempt == 2:
                return {"error": f"HTTP {response.status_code}: {response.text.strip()}"}
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as req_err:
            console_error(f"❌ Request exception: {req_err} (Attempt {attempt+1})")
            if attempt == 2:
                return {"error": str(req_err)}
            time.sleep(2 ** attempt)

def log_failed_device(store, uplink, serial, wan_label, reason):
    FAILED_DEVICES.append({
        "store": store,
        "uplink": uplink,
        "serial": serial,
        "wanLabel": wan_label,
        "reason": reason,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

def save_failed_devices():
    if not FAILED_DEVICES:
        return
    now = datetime.datetime.now(datetime.timezone.utc)
    filename = os.path.join(DATA_DIR, f"failed_devices_{now:%Y%m%d}.json")
    with open(filename, "a") as f:
        for entry in FAILED_DEVICES:
            f.write(json.dumps(convert_numpy_types(entry)) + "\n")

def save_records(records):
    now = datetime.datetime.now(datetime.timezone.utc)
    filename = os.path.join(DATA_DIR, f"wan_metrics_{now:%Y%m%d}.json")
    with open(filename, "a") as f:
        for record in records:
            f.write(json.dumps(convert_numpy_types(record)) + "\n")

def query_metrics(store, serial, uplink, wan_label, api_key):
    params = {
        "uplink": uplink,
        "ip": PRIMARY_DEST_IP,
        "timespan": MAX_TIMESPAN,
        "resolution": RESOLUTION
    }
    url = f"https://api.meraki.com/api/v1/devices/{serial}/lossAndLatencyHistory"
    data = make_api_request(url, api_key, params)

    if not data or not isinstance(data, list) or len(data) == 0:
        params["ip"] = FALLBACK_DEST_IP
        data = make_api_request(url, api_key, params)

    return data

def process_job(job, counters):
    store, serial, wan_label, uplink, api_key = job
    if not wan_label:
        console_error(f"❌ No WAN label: {store} {uplink}")
        counters['failures'] += 1
        log_failed_device(store, uplink, serial, wan_label, "No WAN label")
        return

    console_info(f"🔍 Querying {store} {uplink}...")
    data = query_metrics(store, serial, uplink, wan_label, api_key)
    
    if not data or (isinstance(data, dict) and "error" in data):
        error_msg = data.get("error", "Unknown error") if isinstance(data, dict) else "No data returned"
        console_error(f"❌ API ERROR: {store} {uplink} - {error_msg}")
        counters['failures'] += 1
        log_failed_device(store, uplink, serial, wan_label, error_msg)
        return

    if not isinstance(data, list) or len(data) == 0:
        console_error(f"❌ No valid data: {store} {uplink}")
        counters['failures'] += 1
        log_failed_device(store, uplink, serial, wan_label, "No or invalid data")
        return

    df = pd.DataFrame(data)
    df = df.dropna(subset=["jitter", "latencyMs", "lossPercent"])
    if df.empty:
        console_error(f"❌ Empty metrics: {store} {uplink}")
        counters['failures'] += 1
        log_failed_device(store, uplink, serial, wan_label, "Empty data")
        return

    metrics = {
        "store": store,
        "uplink": uplink,
        "serial": serial,
        "wanLabel": wan_label,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "min_jitter": round(df["jitter"].min(), 2),
        "max_jitter": round(df["jitter"].max(), 2),
        "avg_jitter": round(df["jitter"].mean(), 2),
        "min_latency": round(df["latencyMs"].min(), 2),
        "max_latency": round(df["latencyMs"].max(), 2),
        "avg_latency": round(df["latencyMs"].mean(), 2),
        "min_loss": round(df["lossPercent"].min(), 2),
        "max_loss": round(df["lossPercent"].max(), 2),
        "avg_loss": round(df["lossPercent"].mean(), 2),
    }
    console_success(f"✅ {store} {uplink} | Loss: {metrics['min_loss']}%/{metrics['avg_loss']}%/{metrics['max_loss']}% | Latency: {metrics['min_latency']}ms/{metrics['avg_latency']}ms/{metrics['max_latency']}ms | Jitter: {metrics['min_jitter']}ms/{metrics['avg_jitter']}ms/{metrics['max_jitter']}ms")
    counters['successes'] += 1
    save_records([metrics])

def job_worker(counters):
    while True:
        job = job_queue.get()
        if job is None:
            break
        process_job(job, counters)
        job_queue.task_done()

def log_metrics():
    global cycle_counter, RATE_LIMIT_HITS

    console_info("🚀 Meraki Queue Dispatcher Started")
    devices, source_file = load_latest_inventory()
    console_info(f"📦 Loaded {len(devices)} valid stores from {source_file}")

    while True:
        counters = {'successes': 0, 'failures': 0}
        console_info(f"♻️ Cycle {cycle_counter + 1}: Polling WAN1 and WAN2")
        start_time = time.time()

        for _ in API_KEYS:
            threading.Thread(target=job_worker, args=(counters,), daemon=True).start()

        for idx, device in enumerate(devices):
            api_key = API_KEYS[idx % len(API_KEYS)]

            wan1_label = device.get("wan1_label", "")
            if wan1_label:
                job_queue.put((device["network_name"], device["device_serial"], wan1_label, "wan1", api_key))

            wan2_label = device.get("wan2_label", "")
            if wan2_label:
                job_queue.put((device["network_name"], device["device_serial"], wan2_label, "wan2", api_key))

        job_queue.join()
        save_failed_devices()
        FAILED_DEVICES.clear()

        cycle_time = time.time() - start_time
        console_info(f"⏳ Cycle done in {cycle_time:.1f}s | Success: {counters['successes']} | Failures: {counters['failures']} | 429s: {RATE_LIMIT_HITS}")

        summary = {
            "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
            "total_queries": counters['successes'] + counters['failures'],
            "successful_queries": counters['successes'],
            "failed_queries": counters['failures'],
            "success_rate": round((counters['successes'] / (counters['successes'] + counters['failures'])) * 100, 2) if (counters['successes'] + counters['failures']) else 0
        }
        with open(os.path.join(DATA_DIR, f"wan_metrics_summary_{datetime.datetime.now().strftime('%Y%m%d')}.json"), "w") as f:
            json.dump(summary, f)

        RATE_LIMIT_HITS = 0
        cycle_counter += 1

        sleep_time = max(0, 300 - cycle_time)
        time.sleep(sleep_time)

if __name__ == "__main__":
    try:
        log_metrics()
    except KeyboardInterrupt:
        console_info("🛑 Stopped by user")
