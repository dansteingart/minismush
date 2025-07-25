#!/usr/bin/env python3
"""
MinismuSH Library Usage Examples

This script demonstrates how to use the minismush_client library for
both SMU control and battery cycling operations.

Requirements:
- minismush server running on localhost:3000
- requests library: pip install requests
"""

import sys
import os

# Add parent directory to path to import the library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minismush_client import SMUClient, BatteryCycler, MinismuSHError


def smu_example():
    """Demonstrate basic SMU operations"""
    print("SMU Control Example")
    print("=" * 30)
    
    try:
        # Create SMU client
        smu = SMUClient("http://localhost:3000")
        
        # Test connection
        if not smu.test_connection():
            print("✗ Cannot connect to server")
            return
        print("✓ Connected to SMU server")
        
        # Get device info
        identity = smu.get_identity()
        print(f"Device: {identity}")
        
        # Channel operations
        channel = 1
        print(f"\nChannel {channel} operations:")
        
        # Enable channel and set voltage
        smu.enable_channel(channel)
        smu.set_voltage(channel, 3.3)
        print(f"✓ Set channel {channel} to 3.3V")
        
        # Take measurements
        measurements = smu.measure_voltage_and_current(channel)
        print(f"Measurement: {measurements['voltage']:.3f}V, {measurements['current']:.6f}A")
        
        # Set current mode
        smu.set_current(channel, 0.001)  # 1 mA
        print(f"✓ Set channel {channel} to 1 mA")
        
        measurements = smu.measure_voltage_and_current(channel)
        print(f"Measurement: {measurements['voltage']:.3f}V, {measurements['current']:.6f}A")
        
        # Disable channel
        smu.disable_channel(channel)
        print(f"✓ Disabled channel {channel}")
        
    except MinismuSHError as e:
        print(f"✗ SMU Error: {e}")


def simple_cycling_example():
    """Demonstrate simple battery cycling"""
    print("\n\nSimple Battery Cycling Example")
    print("=" * 40)
    
    try:
        # Create cycler client
        cycler = BatteryCycler("http://localhost:3000")
        
        # Test connection
        if not cycler.test_connection():
            print("✗ Cannot connect to server")
            return
        print("✓ Connected to cycler server")
        
        # Create simple test steps
        steps = cycler.create_cycle_steps(
            charge_current=0.010,      # 10 mA charge
            discharge_current=-0.010,  # 10 mA discharge
            charge_voltage=4.2,        # Charge to 4.2V
            discharge_voltage=3.0,     # Discharge to 3.0V
        )
        
        print(f"✓ Created {len(steps)} step definitions")
        
        # Test metadata
        metadata = {
            'testName': 'Library Simple Test',
            'testType': 'demonstration',
            'batteryId': 'DEMO_CELL_001',
            'operator': 'library_user',
            'notes': 'Simple 3-cycle test using Python library'
        }
        
        # Start test
        result = cycler.start_test(
            channel=1,
            steps=steps,
            cycles=3,
            enable_logging=True,
            metadata=metadata
        )
        
        print(f"✓ Test started successfully!")
        print(f"  - Channel: {result.get('channel')}")
        print(f"  - Cycles: {result.get('cycles')}")
        print(f"  - Message: {result.get('message')}")
        
        # Show how to monitor (but don't actually wait)
        print(f"\nTo monitor progress:")
        print(f"  status = cycler.get_status()")
        print(f"  cycler.wait_for_completion()  # Blocks until done")
        print(f"\nTo control:")
        print(f"  cycler.pause_test()")
        print(f"  cycler.resume_test()")
        print(f"  cycler.stop_test()")
        
        # Show current status
        status = cycler.get_status()
        if status.get('isRunning'):
            print(f"\n✓ Test is running - Cycle {status.get('currentCycle')}/{status.get('totalCycles')}")
        
    except MinismuSHError as e:
        print(f"✗ Cycler Error: {e}")


def formation_cycling_example():
    """Demonstrate formation cycling with different currents"""
    print("\n\nFormation Cycling Example")
    print("=" * 35)
    
    try:
        cycler = BatteryCycler("http://localhost:3000")
        
        if not cycler.test_connection():
            print("✗ Cannot connect to server")
            return
        print("✓ Connected to cycler server")
        
        # Create formation steps (first cycle at 2mA, remaining at 20mA)
        steps = cycler.create_formation_steps(
            formation_current=0.002,  # 2 mA for first cycle
            normal_current=0.020,     # 20 mA for remaining cycles
            charge_voltage=4.2,
            discharge_voltage=3.0
        )
        
        print(f"✓ Created formation cycling steps ({len(steps)} total)")
        
        # Rich metadata
        metadata = {
            'testName': '20-Cycle Formation Test',
            'testType': 'formation_cycling',
            'batteryId': 'FORM_CELL_001',
            'batteryType': 'Li-ion',
            'capacityAh': '2.0',
            'temperatureC': '25',
            'operator': 'formation_tech',
            'notes': 'Formation cycling: first cycle 2mA, remaining 19 cycles 20mA'
        }
        
        # This would start a 20-cycle formation test
        print(f"\nTo start 20-cycle formation test:")
        print(f"  result = cycler.start_test(")
        print(f"      channel=1,")
        print(f"      steps=steps,")
        print(f"      cycles=20,")
        print(f"      metadata=metadata")
        print(f"  )")
        print(f"\n(Not actually starting - would run for hours)")
        
    except MinismuSHError as e:
        print(f"✗ Formation Cycler Error: {e}")


def custom_step_example():
    """Demonstrate custom step creation"""
    print("\n\nCustom Step Creation Example")
    print("=" * 40)
    
    try:
        cycler = BatteryCycler("http://localhost:3000")
        
        # Create custom steps manually
        custom_steps = [
            {"cycle": "start"},
            
            # Custom CC charge with capacity limit
            cycler.create_custom_step(
                mode="cc",
                current=0.050,      # 50 mA
                cutoff_V=4.2,
                cutoff_Ah=0.5,      # Stop at 0.5 Ah
                cutoff_time_s=3600
            ),
            
            # Rest period
            cycler.create_custom_step(
                mode="rest",
                cutoff_time_s=1800  # 30 minute rest
            ),
            
            # High rate discharge
            cycler.create_custom_step(
                mode="cc",
                current=-0.200,     # 200 mA discharge
                cutoff_V=3.0,
                cutoff_time_s=1800
            ),
            
            {"cycle": "end"}
        ]
        
        # Validate the custom steps
        validation = cycler.validate_steps(custom_steps)
        print(f"✓ Custom steps validated: {validation.get('message')}")
        print(f"  Total steps: {validation.get('totalSteps')}")
        
        print(f"\nCustom step example created successfully!")
        print(f"Steps include: CC charge with Ah limit, rest, high-rate discharge")
        
    except MinismuSHError as e:
        print(f"✗ Custom Step Error: {e}")


def main():
    """Run all examples"""
    print("MinismuSH Python Library Examples")
    print("=" * 50)
    
    # Run examples
    smu_example()
    simple_cycling_example()
    formation_cycling_example()
    custom_step_example()
    
    print(f"\n\nLibrary Examples Complete!")
    print(f"Import the library with: from minismush_client import SMUClient, BatteryCycler")


if __name__ == "__main__":
    main()