#!/usr/bin/env python3
"""
Battery Cycling Example - 20 Cycles with Different Current Rates

This example demonstrates how to set up a 20-cycle battery test where:
- First cycle uses 2 mA charge/discharge current
- Remaining 19 cycles use 20 mA charge/discharge current

The node server handles all the cycling logic, timing, and data logging.

Requirements:
- minismush server running on localhost:3000
- SMU device connected to channel 1
- requests library: pip install requests
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:3000"
CHANNEL = 1

def make_request(method, endpoint, data=None, expect_json=True):
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        
        if expect_json:
            return response.json()
        else:
            return response.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON response from {url}")
        return None

def create_20_cycle_test():
    """Create a complete 20-cycle test definition"""
    
    # Step definition for all 20 cycles
    steps = [
        {"cycle": "start"},
        
        # First cycle at 2 mA (0.002 A)
        {"mode": "cc", "current": 0.002, "cutoff_V": 4.2, "cutoff_time_s": 7200},
        {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 3600},
        {"mode": "cc", "current": -0.002, "cutoff_V": 3.0, "cutoff_time_s": 7200},
        {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.001, "cutoff_time_s": 1800},
        
        # Remaining 19 cycles at 20 mA (0.020 A)
        # The cycler will automatically repeat this pattern
        {"mode": "cc", "current": 0.020, "cutoff_V": 4.2, "cutoff_time_s": 7200},
        {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 3600},
        {"mode": "cc", "current": -0.020, "cutoff_V": 3.0, "cutoff_time_s": 7200},
        {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.001, "cutoff_time_s": 1800},
        
        {"cycle": "end"}
    ]
    
    return steps

def start_battery_test():
    """Start the 20-cycle battery test"""
    
    print("Setting up 20-cycle battery test...")
    
    # Test metadata
    metadata = {
        'testName': '20-Cycle Formation Test',
        'testType': 'formation_cycling',
        'operator': 'python_script',
        'batteryId': 'CELL_001',
        'batteryType': 'Li-ion',
        'capacityAh': '2.0',
        'temperatureC': '25',
        'notes': '20-cycle test: first cycle at 2mA, remaining 19 cycles at 20mA'
    }
    
    # Create step definition
    steps = create_20_cycle_test()
    
    # Validate steps first
    print("Validating step definition...")
    validation = make_request('POST', '/cycler/validate', {'steps': steps})
    if not validation or not validation.get('success'):
        print("✗ Step validation failed:", validation.get('error') if validation else 'Unknown error')
        return False
    print("✓ Step definition is valid")
    
    # Start the test
    cycling_request = {
        'channel': CHANNEL,
        'cycles': 20,
        'enableLogging': True,
        'metadata': metadata,
        'steps': steps
    }
    
    print("Starting battery cycling test...")
    result = make_request('POST', '/cycler/start', cycling_request)
    
    if result and result.get('success'):
        print("✓ 20-cycle battery test started successfully!")
        print(f"  - Channel: {result.get('channel')}")
        print(f"  - Total cycles: {result.get('cycles')}")
        print(f"  - Log files automatically saved to: /data/battery/")
        print(f"  - Using enhanced array-based cycling analysis")
        print()
        print("The test is now running on the server.")
        print("Monitor progress with:")
        print("  curl http://localhost:3000/cycler/status")
        print("  curl http://localhost:3000/cycler/step_analysis")
        print("  curl http://localhost:3000/cycler/performance_metrics")
        print("Stop test with: curl -X POST http://localhost:3000/cycler/stop")
        return True
    else:
        print("✗ Failed to start battery cycling test")
        if result:
            print(f"Error: {result.get('error', 'Unknown error')}")
        return False

def main():
    """Main execution function"""
    print("Battery Cycling Test Setup")
    print("="*40)
    print("Configuration:")
    print("  - First cycle: 2 mA")
    print("  - Remaining 19 cycles: 20 mA")
    print("  - Charge voltage: 4.2V")
    print("  - Discharge voltage: 3.0V")
    print("  - Channel:", CHANNEL)
    print()
    
    # Check server connectivity
    print("Checking server connectivity...")
    result = make_request('GET', '/read/', expect_json=False)
    if result is None:
        print("✗ Cannot connect to minismush server at", BASE_URL)
        print("Make sure the server is running: node nodeforwarder.js 3000 /dev/ttyUSB0 115200")
        sys.exit(1)
    print("✓ Server is accessible")
    print()
    
    # Start the test
    if start_battery_test():
        print("\nTest setup complete! The server is now handling all cycling operations.")
    else:
        print("\nTest setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()