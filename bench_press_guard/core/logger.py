import csv
import time
import os
from datetime import datetime

class FailureLogger:
    def __init__(self, output_file="bench_press_log.csv"):
        self.output_file = output_file
        
        # Create file with header if not exists
        if not os.path.exists(self.output_file):
            with open(self.output_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "BenchID", "State", "Reason", "Latency_ms"])

    def log(self, bench_id, state, reason, latency_sec):
        timestamp = datetime.now().isoformat()
        latency_ms = int(latency_sec * 1000)
        
        # Print to console
        color = "\033[92m" if state == "NORMAL" else "\033[91m" # Green or Red
        reset = "\033[0m"
        print(f"{color}[{timestamp}] BENCH {bench_id}: {state} | {reason} (Latency: {latency_ms}ms){reset}")
        
        # Write to file
        with open(self.output_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, bench_id, state, reason, latency_ms])
