#!/usr/bin/env python3
"""
Super Simple Battery Cycling Example

Just run a basic battery test and monitor until done.
Uses minismush_client for convenience.
"""

import time
from minismush_client import create_smu_client, create_cycler_client

# Server and test parameters
SERVER_URL = "http://localhost:3000"
CHANNEL = 1
CHARGE_CURRENT = 0.01      # 10 mA
DISCHARGE_CURRENT = -0.01  # 10 mA  
MAX_VOLTAGE = 4.2          # 4.2V
MIN_VOLTAGE = 3.0          # 3.0V
CYCLES = 3

print("Starting simple battery test...")

# Connect to server
smu = create_smu_client(SERVER_URL)
cycler = create_cycler_client(SERVER_URL)
print("✓ Connected to server")

# Start logging
smu.start_csv_log("simple_test", channels=[CHANNEL])
print("✓ Logging started")

# Create simple cycling steps
steps = [
    {"cycle": "start"},
    {"mode": "cc", "current": CHARGE_CURRENT, "cutoff_V": MAX_VOLTAGE, "cutoff_time_s": 3600},
    {"mode": "cv", "voltage": MAX_VOLTAGE, "cutoff_A": 0.001, "cutoff_time_s": 1800},
    {"mode": "cc", "current": DISCHARGE_CURRENT, "cutoff_V": MIN_VOLTAGE, "cutoff_time_s": 3600},
    {"mode": "cv", "voltage": MIN_VOLTAGE, "cutoff_A": -0.001, "cutoff_time_s": 900},
    {"cycle": "end"}
]

# Start the test
cycler.start_test(CHANNEL, steps, CYCLES)
print("✓ Test started")

# Monitor until done
print("\nMonitoring test progress...")
print("Press Ctrl+C to stop monitoring (test continues on server)")

try:
    while cycler.is_running():
        status = cycler.get_status()
        
        # Show progress
        cycle = status.get('currentCycle', 0)
        total_cycles = status.get('totalCycles', 0)
        step_time = status.get('stepTime', 0)
        total_time = status.get('totalTime', 0)
        current_step = status.get('currentStep', {})
        step_mode = current_step.get('mode', 'unknown').upper()
        
        print(f"\rCycle {cycle}/{total_cycles} | {step_mode} | "
              f"Step: {step_time:.0f}s | Total: {total_time/60:.1f}min", 
              end='', flush=True)
        
        time.sleep(10)  # Check every 10 seconds
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped. Test continues on server.")

print("\n✓ Test completed!")
print("Data saved to: /data/battery/simple_test.csv")