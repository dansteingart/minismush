#!/usr/bin/env python3
"""
Simple Battery Cycling Example

This example shows how to set up a basic battery cycling test.
The node server handles all timing, control, and data logging.

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

def create_simple_test():
    """Create a simple 3-cycle test"""
    
    steps = [
        {"cycle": "start"},
        {"mode": "cc", "current": 0.010, "cutoff_V": 4.2, "cutoff_time_s": 3600},   # CC charge
        {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 1800},   # CV charge
        {"mode": "cc", "current": -0.010, "cutoff_V": 3.0, "cutoff_time_s": 3600},  # CC discharge
        {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.001, "cutoff_time_s": 900},   # CV discharge
        {"cycle": "end"}
    ]
    
    return steps

def main():
    """Main execution function"""
    print("Simple Battery Cycling Test")
    print("="*30)
    print("Configuration:")
    print("  - 3 cycles")
    print("  - 10 mA charge/discharge")
    print("  - 4.2V max, 3.0V min")
    print("  - Channel:", CHANNEL)
    print()
    
    # Check server connectivity
    print("Checking server...")
    if make_request('GET', '/read/', expect_json=False) is None:
        print("✗ Cannot connect to server at", BASE_URL)
        sys.exit(1)
    print("✓ Server accessible")
    
    # Test metadata
    metadata = {
        'testName': 'Simple Cycling Test',
        'testType': 'basic_cycling',
        'operator': 'python_user',
        'batteryId': 'TEST_CELL',
        'notes': 'Simple 3-cycle test at 10mA'
    }
    
    # Create and validate steps
    steps = create_simple_test()
    print("\nValidating test...")
    
    validation = make_request('POST', '/cycler/validate', {'steps': steps})
    if not validation or not validation.get('success'):
        print("✗ Invalid test definition")
        if validation:
            print("Error:", validation.get('error'))
        sys.exit(1)
    print("✓ Test definition valid")
    
    # Start test
    test_config = {
        'channel': CHANNEL,
        'cycles': 3,
        'enableLogging': True,
        'metadata': metadata,
        'steps': steps
    }
    
    print("\nStarting test...")
    result = make_request('POST', '/cycler/start', test_config)
    
    if result and result.get('success'):
        print("✓ Test started successfully!")
        print(f"  • Data will be logged to: /data/battery/")
        print(f"  • Using enhanced array-based analysis")
        print("\nMonitor with:")
        print("  curl http://localhost:3000/cycler/status")
        print("  curl http://localhost:3000/cycler/step_analysis    # Array-based analysis")
        print("  curl http://localhost:3000/cycler/performance_metrics")
        print("  curl 'http://localhost:3000/data/ch1?limit=10'    # Access data arrays")
        print("\nStop with:")
        print("  curl -X POST http://localhost:3000/cycler/stop")
    else:
        print("✗ Failed to start test")
        if result:
            print("Error:", result.get('error'))

if __name__ == "__main__":
    main()