#!/usr/bin/env python3
"""
Really Simple Battery Cycling Example - 20 lines

Just cycles a battery through charge/discharge using the cycler.
No classes, no complexity - just start a test and let the server handle it.
"""

from minismush_client import BatteryCycler

# Connect to server
cycler = BatteryCycler("http://localhost:3000")

# Create simple cycle: charge to 4.2V, discharge to 3.0V
steps = [
    {"cycle": "start"},
    {"mode": "cc", "current": 0.010, "cutoff_V": 4.2, "cutoff_time_s": 3600},  # 10mA charge
    {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 1800},  # CV hold
    {"mode": "cc", "current": -0.010, "cutoff_V": 3.0, "cutoff_time_s": 3600}, # 10mA discharge
    {"cycle": "end"}
]

# Start 3 cycles on channel 1
result = cycler.start_test(channel=1, steps=steps, cycles=3)
print(f"Started: {result['message']}")
print("Check status: curl http://localhost:3000/cycler/status")
print("Stop test: curl -X POST http://localhost:3000/cycler/stop")