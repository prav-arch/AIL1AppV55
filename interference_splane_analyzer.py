
# interference_splane_analyzer.py

import re
import json
from datetime import datetime
from pathlib import Path

DU_LOG = "/home/users/praveen.joe/logs/dulogs.txt"
CU_LOG = "/home/users/praveen.joe/logs/cucplogs.txt"
OUTPUT_PATH = "interference_splane_issues.json"

INTERFERENCE_RULES = [
    { "pattern": r"SINR drop|RSRP at -\d+ dBm|BLER increased", "type": "Interference Suspected", "description": "Poor SINR or RSRP detected.", "severity": "high" },
    { "pattern": r"CRC error|PDSCH decoding failure|UL retransmissions", "type": "Interference Impact", "description": "Radio decoding issues suggest interference.", "severity": "medium" },
    { "pattern": r"Timing drift.*?(\d+)ns", "type": "Timing Drift", "description": "Timing instability, possibly from RF interference.", "severity": "high" }
]

SPLANE_RULES = [
    { "pattern": r"F1SetupRequest took (\d+)ms", "type": "S-Plane Delay", "description": "F1SetupRequest latency high.", "severity": "medium", "threshold_ms": 200 },
    { "pattern": r"UEContextSetupRequest took (\d+)ms", "type": "S-Plane Delay", "description": "UEContextSetup delay.", "severity": "high", "threshold_ms": 250 },
    { "pattern": r"RRCSetup delayed", "type": "S-Plane Delay", "description": "RRC setup delay.", "severity": "high" }
]

def parse_logs(path, rules):
    results = []
    with open(path, "r", errors="ignore") as f:
        for line in f:
            for rule in rules:
                match = re.search(rule["pattern"], line, re.IGNORECASE)
                if match:
                    ts_match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", line)
                    timestamp = datetime.now().strftime("%Y-%m-%dT") + (ts_match.group(1) if ts_match else "00:00:00") + "Z"
                    entry = { "timestamp": timestamp, "type": rule["type"], "description": rule["description"], "log_line": line.strip(), "severity": rule.get("severity", "medium") }
                    if "threshold_ms" in rule:
                        if int(match.group(1)) > rule["threshold_ms"]:
                            entry["delay_ms"] = int(match.group(1))
                            results.append(entry)
                    else:
                        results.append(entry)
    return results

def run_analysis():
    i_events = parse_logs(DU_LOG, INTERFERENCE_RULES) if Path(DU_LOG).exists() else []
    s_events = parse_logs(CU_LOG, SPLANE_RULES) if Path(CU_LOG).exists() else []
    all_issues = i_events + s_events
    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_issues, f, indent=2)

if __name__ == "__main__":
    run_analysis()
