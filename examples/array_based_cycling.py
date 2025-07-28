#!/usr/bin/env python3
"""
Array-Based Battery Cycling Example

Demonstrates the new array-based cycling features that use ch1/ch2 data arrays
for enhanced analysis and control instead of just real-time stream processing.

New features showcased:
- Real-time step analysis using accumulated data arrays
- Enhanced cutoff logic with voltage trend analysis
- Performance metrics with energy calculations
- Data array access for custom analysis

Requirements:
- minismush server running on localhost:3000
- SMU device connected to channel 1
- requests library: pip install requests
"""

import requests
import json
import time
import sys

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

def create_test_with_array_features():
    """Create a test designed to showcase array-based features"""
    
    steps = [
        {"cycle": "start"},
        # Longer CC step to build up array data for analysis
        {"mode": "cc", "current": 0.020, "cutoff_V": 4.1, "cutoff_time_s": 1800},
        # CV step with enhanced array-based cutoff detection
        {"mode": "cv", "voltage": 4.1, "cutoff_A": 0.002, "cutoff_time_s": 1200},
        # Discharge with array analysis
        {"mode": "cc", "current": -0.015, "cutoff_V": 3.2, "cutoff_time_s": 1800},
        # Rest period to observe voltage relaxation in arrays
        {"mode": "rest", "cutoff_time_s": 300},
        {"cycle": "end"}
    ]
    
    return steps

def monitor_array_analysis():
    """Monitor the test using new array-based analysis endpoints"""
    
    print("\n" + "="*60)
    print("ARRAY-BASED CYCLING ANALYSIS")
    print("="*60)
    
    try:
        # Get step analysis
        step_analysis = make_request('GET', '/cycler/step_analysis')
        if step_analysis and not step_analysis.get('error'):
            print(f"\n📊 Current Step Analysis:")
            print(f"   Channel: {step_analysis['channel']}")
            print(f"   Cycle: {step_analysis['current_cycle']}")
            print(f"   Step: {step_analysis['current_step']} ({step_analysis['step_type']})")
            print(f"   Step Time: {step_analysis['step_time_s']:.1f}s")
            
            analysis = step_analysis['step_analysis']
            print(f"\n🔬 Array Analysis:")
            print(f"   Voltage Trend: {analysis['voltageTrend']:.6f} V/s")
            print(f"   Current Stability: {analysis['currentStability']:.4f}")
            print(f"   Step Avg Voltage: {analysis['stepAvgVoltage']:.4f} V")
            print(f"   Step Avg Current: {analysis['stepAvgCurrent']:.6f} A")
            print(f"   Data Points: {analysis['dataPointsInStep']}")
            
            print(f"\n⚡ Capacity:")
            print(f"   Step Ah: {step_analysis['step_ah']:.6f}")
            print(f"   Cycle Ah: {step_analysis['cycle_ah']:.6f}")
            print(f"   Total Ah: {step_analysis['total_ah']:.6f}")
        
        # Get performance metrics
        metrics = make_request('GET', '/cycler/performance_metrics')
        if metrics and not metrics.get('error'):
            print(f"\n📈 Performance Metrics:")
            print(f"   Runtime: {metrics['total_runtime_h']:.2f} hours")
            print(f"   Completion: {metrics['completion_percentage']:.1f}%")
            
            m = metrics['metrics']
            print(f"   Average Power: {m['avg_power_w']:.4f} W")
            print(f"   Total Energy: {m['total_energy_wh']:.4f} Wh")
            print(f"   Data Rate: {m['avg_data_rate']:.1f} points/sec")
            print(f"   Data Points: {m['data_points_collected']}")
        
        # Get raw data array info
        data_analysis = make_request('GET', f'/data/analysis?channel={CHANNEL}')
        if data_analysis and not data_analysis.get('error'):
            print(f"\n📋 Data Array Info:")
            print(f"   Total Points: {data_analysis['total_points']}")
            print(f"   Time Span: {data_analysis['time_span_hours']:.2f} hours")
            print(f"   Voltage Range: {data_analysis['voltage_range']['min']:.3f} - {data_analysis['voltage_range']['max']:.3f} V")
            print(f"   Current Range: {data_analysis['current_range']['min']:.6f} - {data_analysis['current_range']['max']:.6f} A")
    
    except Exception as e:
        print(f"Error during monitoring: {e}")

def demonstrate_array_access():
    """Demonstrate accessing the ch1/ch2 data arrays directly"""
    
    print(f"\n🔍 Accessing Data Arrays:")
    
    # Get last 10 data points from channel
    ch_data = make_request('GET', f'/data/ch{CHANNEL}?limit=10')
    if ch_data and ch_data.get('data'):
        print(f"   Last 10 data points from CH{CHANNEL}:")
        print(f"   Total points available: {ch_data['total_points']}")
        
        for i, point in enumerate(ch_data['data'][-5:]):  # Show last 5
            print(f"     [{i+1}] {point['voltage_V']:.4f}V, {point['current_A']:.6f}A @ {point['time_ms']}")
    
    # Get comprehensive analysis
    analysis = make_request('GET', f'/data/analysis?channel={CHANNEL}')
    if analysis and not analysis.get('error'):
        print(f"\n   Array Analysis Summary:")
        a = analysis['analysis']
        print(f"     Overall Voltage Trend: {a['voltageTrend']:.6f} V/s")
        print(f"     Overall Current Stability: {a['currentStability']:.4f}")
        print(f"     Overall Avg Voltage: {a['stepAvgVoltage']:.4f} V")
        print(f"     Overall Avg Current: {a['stepAvgCurrent']:.6f} A")

def main():
    """Main execution function"""
    print("Array-Based Battery Cycling Demo")
    print("="*40)
    print("This example showcases the new array-based cycling features:")
    print("  • Enhanced step analysis using data arrays")
    print("  • Voltage trend analysis for better cutoffs")
    print("  • Performance metrics with energy calculations")
    print("  • Direct access to ch1/ch2 data arrays")
    print(f"  • Logs automatically saved to /data/battery/")
    print()
    
    # Check server connectivity
    print("Checking server...")
    if make_request('GET', '/read/', expect_json=False) is None:
        print("✗ Cannot connect to server at", BASE_URL)
        sys.exit(1)
    print("✓ Server accessible")
    
    # Test metadata
    metadata = {
        'testName': 'Array-Based Cycling Demo',
        'testType': 'array_analysis_demo',
        'operator': 'python_demo',
        'batteryId': 'DEMO_CELL',
        'batteryType': 'Li-ion',
        'capacityAh': '1.0',
        'notes': 'Demo of array-based cycling with enhanced analysis features'
    }
    
    # Create and validate steps
    steps = create_test_with_array_features()
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
        'cycles': 2,  # Just 2 cycles for demo
        'enableLogging': True,
        'metadata': metadata,
        'steps': steps
    }
    
    print("\nStarting array-based cycling test...")
    result = make_request('POST', '/cycler/start', test_config)
    
    if result and result.get('success'):
        print("✓ Test started successfully!")
        print(f"  • Data will be logged to: /data/battery/")
        print(f"  • Using enhanced array-based analysis")
        print(f"  • Channel: {result.get('channel')}")
        print(f"  • Cycles: {result.get('cycles')}")
        
        # Wait a moment for some data to accumulate
        print("\nWaiting for data to accumulate...")
        time.sleep(5)
        
        # Demonstrate array-based monitoring
        monitor_array_analysis()
        
        # Demonstrate direct array access
        demonstrate_array_access()
        
        print(f"\n{'='*60}")
        print("MONITORING COMMANDS:")
        print("• Real-time step analysis: curl http://localhost:3000/cycler/step_analysis")
        print("• Performance metrics: curl http://localhost:3000/cycler/performance_metrics")
        print("• Data arrays: curl 'http://localhost:3000/data/ch1?limit=100'")
        print("• Array analysis: curl 'http://localhost:3000/data/analysis?channel=1'")
        print("• Force array processing: curl -X POST http://localhost:3000/cycler/process_arrays")
        print("• Standard status: curl http://localhost:3000/cycler/status")
        print("• Stop test: curl -X POST http://localhost:3000/cycler/stop")
        print("="*60)
        
    else:
        print("✗ Failed to start test")
        if result:
            print("Error:", result.get('error'))

if __name__ == "__main__":
    main()