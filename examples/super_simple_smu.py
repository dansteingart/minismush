#!/usr/bin/env python3
"""
Super Simple SMU Example - Manual Control

Direct SMU control like your example - no cycling, just manual commands.
"""

from minismush_client import SMUClient
from time import sleep

smu = SMUClient("http://localhost:3000")

print(f"Device: {smu.get_identity()}")
smu.enable_channel(1)
smu.start_streaming(1)
smu.set_sample_rate(1, 100)

smu.set_current(1, 0)        # 0A
sleep(5)
smu.set_current(1, 0.01)     # 10mA
sleep(5)
smu.set_current(1, 0)        # 0A
sleep(5)

smu.stop_streaming(1)
smu.disable_channel(1)
print("Done!")