
# fh_violation_engine.py

import re
import json
from datetime import datetime
from pathlib import Path

DU_LOG_PATH = "/home/users/praveen.joe/logs/dulogs.txt"
CU_LOG_PATH = "/home/users/praveen.joe/logs/cucplogs.txt"
OUTPUT_PATH = "fh_protocol_violations_enhanced.json"

DU_RULES = [
    {"pattern": r"(CRC error|PDSCH decoding failure)", "type": "DU Decode Error", "description": "Potential corruption or misaligned IQ frames detected by DU.", "severity": "medium"},
    {"pattern": r"Timing drift.*?(\d+)ns", "type": "Timing Drift", "description": "DU timing drift exceeded acceptable threshold.", "severity": "high"},
    {"pattern": r"Sync lost.*?port\s*(\d+)", "type": "DU Sync Loss", "description": "DU reported loss of synchronization with RU.", "severity": "high"}
]

CU_RULES = [
    {"pattern": r"F1SetupFailure|F1Setup timeout", "type": "F1 Setup Failure", "description": "F1 interface failed to establish in expected time.", "severity": "high"},
    {"pattern": r"UEContextSetup.*?timeout", "type": "UE Context Setup Delay", "description": "UE Context setup delayed or failed, potential S-Plane violation.", "severity": "medium"},
    {"pattern": r"RRCSetupFailure|RRCReestablishmentFailure", "type": "RRC Failure", "description": "RRC signaling failed or UE failed to respond.", "severity": "high"}
]

ecpri_gaps = [
    {"timestamp": "2024-05-20T14:21:35Z", "type": "eCPRI Packet Loss", "description": "Sequence gap detected from 10042 to 10045 on eCPRI interface (port 4).", "impact": "IQ frames lost, potential UL decoding issue at DU.", "severity": "high"}
]

def parse_log(log_path, rules):
    events = []
    with open(log_path, "r", errors="ignore") as f:
        for line in f:
            for rule in rules:
                if re.search(rule["pattern"], line, re.IGNORECASE):
                    ts_match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", line)
                    ts = ts_match.group(1) if ts_match else "00:00:00"
                    full_timestamp = datetime.now().strftime("%Y-%m-%dT") + ts + "Z"
                    events.append({
                        "timestamp": full_timestamp,
                        "type": rule["type"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                        "log_line": line.strip()
                    })
    return events

def correlate_events(du_events, cu_events):
    correlated = []
    for du in du_events:
        du_time = datetime.strptime(du["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        for cu in cu_events:
            cu_time = datetime.strptime(cu["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            if abs((du_time - cu_time).total_seconds()) <= 5:
                correlated.append({
                    "timestamp": du["timestamp"],
                    "type": f"{du['type']} + {cu['type']}",
                    "description": f"Correlated event between DU and CU: {du['description']} / {cu['description']}",
                    "severity": "critical",
                    "du_log": du["log_line"],
                    "cu_log": cu["log_line"]
                })
    return correlated

def run_violation_scan():
    du_events = parse_log(DU_LOG_PATH, DU_RULES) if Path(DU_LOG_PATH).exists() else []
    cu_events = parse_log(CU_LOG_PATH, CU_RULES) if Path(CU_LOG_PATH).exists() else []
    correlated = correlate_events(du_events, cu_events)
    all_violations = du_events + cu_events + ecpri_gaps + correlated
    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_violations, f, indent=2)

if __name__ == "__main__":
    run_violation_scan()
