
# cp_up_coupling_detector.py

import re
import json
from datetime import datetime

LOG_PATH = "/home/users/praveen.joe/logs/cu_du_combined.log"
OUTPUT_PATH = "cp_up_coupling_issues.json"

CPLANE_RULES = [
    {"pattern": r"RRCSetupFailure|UEContextSetupFailure|F1SetupFailure", "type": "Control Plane Issue", "description": "Control-plane signaling failure.", "severity": "high"},
    {"pattern": r"RRCReestablishmentFailure|RRCConnectionRelease", "type": "Control Plane Release", "description": "Unexpected RRC release.", "severity": "medium"}
]

UPLANE_RULES = [
    {"pattern": r"DRB release|DL throughput drop|uplink re-transmissions", "type": "User Plane Degradation", "description": "Data flow interruption or degraded UP.", "severity": "high"},
    {"pattern": r"QoS mismatch|Bearer drop", "type": "User Plane QoS Issue", "description": "QoS mismatch or bearer drop.", "severity": "medium"}
]

def parse_log(path, rules):
    events = []
    with open(path, "r", errors="ignore") as f:
        for line in f:
            for rule in rules:
                if re.search(rule["pattern"], line, re.IGNORECASE):
                    ts_match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", line)
                    ts = ts_match.group(1) if ts_match else "00:00:00"
                    timestamp = datetime.now().strftime("%Y-%m-%dT") + ts + "Z"
                    events.append({ "timestamp": timestamp, "type": rule["type"], "description": rule["description"], "severity": rule["severity"], "log_line": line.strip() })
    return events

def correlate(cp_events, up_events):
    results = []
    for cp in cp_events:
        cp_time = datetime.strptime(cp["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        for up in up_events:
            up_time = datetime.strptime(up["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            if abs((cp_time - up_time).total_seconds()) <= 5:
                results.append({
                    "timestamp": cp["timestamp"],
                    "type": f"{cp['type']} + {up['type']}",
                    "description": f"Coupled issue: {cp['description']} and {up['description']}",
                    "severity": "critical",
                    "cp_log": cp["log_line"],
                    "up_log": up["log_line"]
                })
    return results

def run_cp_up_analysis():
    cp = parse_log(LOG_PATH, CPLANE_RULES)
    up = parse_log(LOG_PATH, UPLANE_RULES)
    coupled = correlate(cp, up)
    data = cp + up + coupled
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    run_cp_up_analysis()
