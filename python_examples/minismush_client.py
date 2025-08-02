#!/usr/bin/env python3
"""
MinismuSH Client Library

A Python library for controlling SMU (Source Measure Unit) devices and battery cycler
functionality through the minismush server.

Author: minismush team
License: MIT

Usage:
    from minismush_client import SMUClient, BatteryCycler
    
    # Create client
    smu = SMUClient("http://localhost:3000")
    
    # Basic SMU operations
    smu.enable_channel(1)
    smu.set_voltage(1, 3.3)
    voltage = smu.measure_voltage(1)
    
    # Battery cycling
    cycler = BatteryCycler("http://localhost:3000")
    steps = cycler.create_cycle_steps(charge_current=0.01, discharge_current=-0.01)
    cycler.start_test(channel=1, steps=steps, cycles=10)
"""

import requests
import json
import time
from typing import Optional, Dict, List, Union, Any


class MinismuSHError(Exception):
    """Base exception for MinismuSH client errors"""
    pass


class SMUError(MinismuSHError):
    """SMU-specific errors"""
    pass


class CyclerError(MinismuSHError):
    """Battery cycler-specific errors"""
    pass


class BaseClient:
    """Base client with common HTTP functionality"""
    
    def __init__(self, base_url: str = "http://localhost:3000", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                expect_json: bool = True) -> Union[Dict, str, None]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            
            if expect_json:
                return response.json()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            raise MinismuSHError(f"Request failed: {e}")
        except json.JSONDecodeError:
            raise MinismuSHError(f"Invalid JSON response from {url}")
    
    def test_connection(self) -> bool:
        """Test if server is accessible"""
        try:
            self._request('GET', '/read/', expect_json=False)
            return True
        except MinismuSHError:
            return False


class SMUClient(BaseClient):
    """
    SMU (Source Measure Unit) client for device control and measurements
    
    For custom requests that return plain text instead of JSON, use:
    result = smu.raw_request('GET', '/your/endpoint', expect_json=False)
    """
    
    def __init__(self, base_url: str = "http://localhost:3000", timeout: int = 10):
        super().__init__(base_url, timeout)
    
    def raw_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                   expect_json: bool = True) -> Union[Dict, str, None]:
        """
        Make a custom request to any SMU endpoint
        
        Args:
            method: HTTP method ('GET', 'POST')
            endpoint: API endpoint (e.g., '/smu/custom_endpoint')
            data: Request data for POST requests
            expect_json: Whether to parse response as JSON
        
        Returns:
            Parsed JSON dict or raw text string
        """
        return self._request(method, endpoint, data, expect_json)
    
    # Device Information
    def get_identity(self) -> str:
        """Get SMU device identification string"""
        result = self._request('GET', '/smu/get_identity', expect_json=False)
        return str(result).strip()
    
    def reset_device(self) -> Dict:
        """Reset SMU device to default state"""
        return self._request('POST', '/smu/reset')
    
    # Channel Control
    def enable_channel(self, channel: int) -> Dict:
        """Enable specified channel"""
        return self._request('POST', '/smu/enable_channel', {'channel': channel})
    
    def disable_channel(self, channel: int) -> Dict:
        """Disable specified channel"""
        return self._request('POST', '/smu/disable_channel', {'channel': channel})
    
    def set_voltage_range(self, channel: int, range_setting: str) -> Dict:
        """Set voltage range for channel (AUTO, LOW, HIGH)"""
        return self._request('POST', '/smu/set_voltage_range', {
            'channel': channel, 
            'range': range_setting
        })
    
    # Source Operations
    def set_voltage(self, channel: int, voltage: float) -> Dict:
        """Set output voltage"""
        return self._request('POST', '/smu/set_potential', {
            'channel': channel, 
            'potential': voltage
        })
    
    def set_current(self, channel: int, current: float) -> Dict:
        """Set output current"""
        return self._request('POST', '/smu/set_current', {
            'channel': channel, 
            'current': current
        })
    
    # Measurement Operations
    def measure_voltage(self, channel: int) -> float:
        """Measure voltage on channel"""
        result = self._request('POST', '/smu/measure_voltage', {'channel': channel})
        if isinstance(result, dict) and 'voltage' in result:
            return float(result['voltage'])
        raise SMUError(f"Invalid voltage measurement response: {result}")
    
    def measure_current(self, channel: int) -> float:
        """Measure current on channel"""
        result = self._request('POST', '/smu/measure_current', {'channel': channel})
        if isinstance(result, dict) and 'current' in result:
            return float(result['current'])
        raise SMUError(f"Invalid current measurement response: {result}")
    
    def measure_voltage_and_current(self, channel: int) -> Dict[str, float]:
        """Measure both voltage and current"""
        result = self._request('POST', '/smu/measure_voltage_and_current', {'channel': channel})
        if isinstance(result, dict) and 'voltage' in result and 'current' in result:
            return {
                'voltage': float(result['voltage']),
                'current': float(result['current']),
                'timestamp': result.get('timestamp')
            }
        raise SMUError(f"Invalid measurement response: {result}")
    
    # Data Streaming
    def start_streaming(self, channel: int) -> Dict:
        """Start continuous data streaming"""
        return self._request('POST', '/smu/start_streaming', {'channel': channel})
    
    def stop_streaming(self, channel: int) -> Dict:
        """Stop data streaming"""
        return self._request('POST', '/smu/stop_streaming', {'channel': channel})
    
    def set_sample_rate(self, channel: int, rate: int) -> Dict:
        """Set streaming sample rate (Hz)"""
        return self._request('POST', '/smu/set_sample_rate', {
            'channel': channel, 
            'rate': rate
        })
    
    # System Management
    def set_led_brightness(self, brightness: int) -> Dict:
        """Set LED brightness (0-100%)"""
        return self._request('POST', '/smu/set_led_brightness', {'brightness': brightness})
    
    def get_led_brightness(self) -> int:
        """Get current LED brightness"""
        result = self._request('GET', '/smu/get_led_brightness', expect_json=False)
        return int(str(result).strip())
    
    def get_temperatures(self) -> Dict:
        """Get system temperatures"""
        return self._request('GET', '/smu/get_temperatures')
    
    def set_time(self, timestamp: int) -> Dict:
        """Set device internal clock"""
        return self._request('POST', '/smu/set_time', {'timestamp': timestamp})
    
    # WiFi Configuration
    def wifi_scan(self) -> List[Dict]:
        """Scan for available WiFi networks"""
        result = self._request('GET', '/smu/wifi_scan')
        return result if isinstance(result, list) else []
    
    def get_wifi_status(self) -> Dict:
        """Get current WiFi connection status"""
        return self._request('GET', '/smu/get_wifi_status')
    
    def set_wifi_credentials(self, ssid: str, password: str) -> Dict:
        """Set WiFi network credentials"""
        return self._request('POST', '/smu/set_wifi_credentials', {
            'ssid': ssid, 
            'password': password
        })
    
    def enable_wifi(self) -> Dict:
        """Enable WiFi connection"""
        return self._request('POST', '/smu/enable_wifi')
    
    def disable_wifi(self) -> Dict:
        """Disable WiFi connection"""
        return self._request('POST', '/smu/disable_wifi')
    
    # Data Logging
    def start_csv_log(self, filename: str, channels: Optional[List[int]] = None) -> Dict:
        """
        Start CSV logging with enhanced dual logging system
        
        Args:
            filename: Base filename (without extension)
            channels: List of channels to log (optional)
        
        Returns:
            Response dictionary with logging status
        """
        data = {'filename': filename}
        if channels:
            data['channels'] = channels
        return self._request('POST', '/start_csv_log', data)
    
    def start_sqlite_log(self, filename: str, table: str = 'readings') -> Dict:
        """
        Start SQLite logging
        
        Args:
            filename: Database filename (without extension)
            table: Table name for data storage
        
        Returns:
            Response dictionary with logging status
        """
        return self._request('POST', '/start_sqlite_log', {
            'filename': filename,
            'table': table
        })
    
    def stop_log(self) -> Dict:
        """Stop all active logging (data and command logs)"""
        return self._request('POST', '/stop_log')
    
    def get_log_status(self) -> Dict:
        """Get current logging status"""
        return self._request('GET', '/log_status')


class BatteryCycler(BaseClient):
    """
    Battery cycler client for automated battery testing
    
    For custom requests that return plain text instead of JSON, use:
    result = cycler.raw_request('GET', '/your/endpoint', expect_json=False)
    """
    
    def __init__(self, base_url: str = "http://localhost:3000", timeout: int = 10):
        super().__init__(base_url, timeout)
    
    def raw_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                   expect_json: bool = True) -> Union[Dict, str, None]:
        """
        Make a custom request to any cycler endpoint
        
        Args:
            method: HTTP method ('GET', 'POST')
            endpoint: API endpoint (e.g., '/cycler/custom_endpoint')
            data: Request data for POST requests
            expect_json: Whether to parse response as JSON
        
        Returns:
            Parsed JSON dict or raw text string
        """
        return self._request(method, endpoint, data, expect_json)
    
    # Step Creation Helpers
    def create_cycle_steps(self, 
                          charge_current: float = 0.01,
                          discharge_current: float = -0.01,
                          charge_voltage: float = 4.2,
                          discharge_voltage: float = 3.0,
                          cv_current_cutoff: float = 0.001,
                          cv_hold_time: int = 1800,
                          cc_timeout: int = 7200) -> List[Dict]:
        """
        Create standard 4-step battery cycle
        
        Args:
            charge_current: CC charge current (A)
            discharge_current: CC discharge current (A, negative)
            charge_voltage: Maximum charge voltage (V)
            discharge_voltage: Minimum discharge voltage (V)
            cv_current_cutoff: CV current cutoff (A)
            cv_hold_time: CV hold time (seconds)
            cc_timeout: CC step timeout (seconds)
        
        Returns:
            List of step definitions
        """
        return [
            {"cycle": "start"},
            {"mode": "cc", "current": charge_current, "cutoff_V": charge_voltage, "cutoff_time_s": cc_timeout},
            {"mode": "cv", "voltage": charge_voltage, "cutoff_A": cv_current_cutoff, "cutoff_time_s": cv_hold_time},
            {"mode": "cc", "current": discharge_current, "cutoff_V": discharge_voltage, "cutoff_time_s": cc_timeout},
            {"mode": "cv", "voltage": discharge_voltage, "cutoff_A": -cv_current_cutoff, "cutoff_time_s": cv_hold_time},
            {"cycle": "end"}
        ]
    
    def create_formation_steps(self, 
                              formation_current: float = 0.002,
                              normal_current: float = 0.020,
                              charge_voltage: float = 4.2,
                              discharge_voltage: float = 3.0) -> List[Dict]:
        """
        Create formation cycling steps (first cycle at low current, remainder at normal current)
        
        Args:
            formation_current: First cycle current (A)
            normal_current: Remaining cycles current (A)
            charge_voltage: Maximum charge voltage (V)
            discharge_voltage: Minimum discharge voltage (V)
        
        Returns:
            List of step definitions
        """
        return [
            {"cycle": "start"},
            
            # First cycle at formation current
            {"mode": "cc", "current": formation_current, "cutoff_V": charge_voltage, "cutoff_time_s": 7200},
            {"mode": "cv", "voltage": charge_voltage, "cutoff_A": 0.001, "cutoff_time_s": 3600},
            {"mode": "cc", "current": -formation_current, "cutoff_V": discharge_voltage, "cutoff_time_s": 7200},
            {"mode": "cv", "voltage": discharge_voltage, "cutoff_A": -0.001, "cutoff_time_s": 1800},
            
            # Remaining cycles at normal current
            {"mode": "cc", "current": normal_current, "cutoff_V": charge_voltage, "cutoff_time_s": 7200},
            {"mode": "cv", "voltage": charge_voltage, "cutoff_A": 0.001, "cutoff_time_s": 3600},
            {"mode": "cc", "current": -normal_current, "cutoff_V": discharge_voltage, "cutoff_time_s": 7200},
            {"mode": "cv", "voltage": discharge_voltage, "cutoff_A": -0.001, "cutoff_time_s": 1800},
            
            {"cycle": "end"}
        ]
    
    def create_custom_step(self, 
                          mode: str,
                          current: Optional[float] = None,
                          voltage: Optional[float] = None,
                          cutoff_V: Optional[float] = None,
                          cutoff_A: Optional[float] = None,
                          cutoff_time_s: Optional[int] = None,
                          cutoff_Ah: Optional[float] = None) -> Dict:
        """
        Create a custom step definition
        
        Args:
            mode: Step mode ('cc', 'cv', 'ocv', 'rest')
            current: Current setting for CC mode (A)
            voltage: Voltage setting for CV mode (V)
            cutoff_V: Voltage cutoff (V)
            cutoff_A: Current cutoff (A)
            cutoff_time_s: Time cutoff (seconds)
            cutoff_Ah: Capacity cutoff (Ah)
        
        Returns:
            Step definition dictionary
        """
        step = {"mode": mode}
        
        if current is not None:
            step["current"] = current
        if voltage is not None:
            step["voltage"] = voltage
        if cutoff_V is not None:
            step["cutoff_V"] = cutoff_V
        if cutoff_A is not None:
            step["cutoff_A"] = cutoff_A
        if cutoff_time_s is not None:
            step["cutoff_time_s"] = cutoff_time_s
        if cutoff_Ah is not None:
            step["cutoff_Ah"] = cutoff_Ah
        
        return step
    
    # Cycler Control
    def validate_steps(self, steps: List[Dict]) -> Dict:
        """Validate step definition"""
        result = self._request('POST', '/cycler/validate', {'steps': steps})
        if not result or not result.get('success'):
            raise CyclerError(f"Step validation failed: {result.get('error') if result else 'Unknown error'}")
        return result
    
    def start_test(self, 
                   channel: int,
                   steps: List[Dict],
                   cycles: int = 1,
                   enable_logging: bool = True,
                   metadata: Optional[Dict] = None) -> Dict:
        """
        Start battery cycling test
        
        Args:
            channel: SMU channel number
            steps: List of step definitions
            cycles: Number of cycles to run
            enable_logging: Enable automatic data logging
            metadata: Test metadata dictionary
        
        Returns:
            Start response dictionary
        """
        if metadata is None:
            metadata = {}
        
        # Validate steps first
        self.validate_steps(steps)
        
        request_data = {
            'channel': channel,
            'cycles': cycles,
            'enableLogging': enable_logging,
            'metadata': metadata,
            'steps': steps
        }
        
        result = self._request('POST', '/cycler/start', request_data)
        if not result or not result.get('success'):
            raise CyclerError(f"Failed to start cycler: {result.get('error') if result else 'Unknown error'}")
        
        return result
    
    def stop_test(self) -> Dict:
        """Stop running cycling test"""
        return self._request('POST', '/cycler/stop')
    
    def pause_test(self) -> Dict:
        """Pause running cycling test"""
        return self._request('POST', '/cycler/pause')
    
    def resume_test(self) -> Dict:
        """Resume paused cycling test"""
        return self._request('POST', '/cycler/resume')
    
    def get_status(self) -> Dict:
        """Get current cycling status"""
        return self._request('GET', '/cycler/status')
    
    def is_running(self) -> bool:
        """Check if cycler is currently running"""
        try:
            status = self.get_status()
            return status.get('isRunning', False)
        except MinismuSHError:
            return False
    
    def wait_for_completion(self, 
                           check_interval: int = 30,
                           progress_callback: Optional[callable] = None) -> Dict:
        """
        Wait for cycling test to complete
        
        Args:
            check_interval: Status check interval (seconds)
            progress_callback: Optional callback for progress updates
        
        Returns:
            Final status dictionary
        """
        print("Waiting for test completion...")
        
        try:
            while True:
                status = self.get_status()
                
                if not status.get('isRunning'):
                    print("\n✓ Test completed!")
                    return status
                
                if progress_callback:
                    progress_callback(status)
                else:
                    # Default progress display
                    cycle = status.get('currentCycle', 0)
                    total_cycles = status.get('totalCycles', 0)
                    step_time = status.get('stepTime', 0)
                    total_time = status.get('totalTime', 0)
                    total_ah = status.get('totalAh', 0)
                    current_step = status.get('currentStep', {})
                    step_mode = current_step.get('mode', 'unknown').upper()
                    
                    print(f"\rCycle {cycle}/{total_cycles} | Step: {step_mode} | "
                          f"Step time: {step_time:.1f}s | "
                          f"Total time: {total_time/3600:.1f}h | "
                          f"Total Ah: {total_ah:.3f}", end='', flush=True)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            print("Note: Test continues running on server.")
            return self.get_status()


# Convenience Functions
def create_smu_client(base_url: str = "http://localhost:3000") -> SMUClient:
    """Create and test SMU client connection"""
    client = SMUClient(base_url)
    if not client.test_connection():
        raise MinismuSHError(f"Cannot connect to server at {base_url}")
    return client


def create_cycler_client(base_url: str = "http://localhost:3000") -> BatteryCycler:
    """Create and test battery cycler client connection"""
    client = BatteryCycler(base_url)
    if not client.test_connection():
        raise MinismuSHError(f"Cannot connect to server at {base_url}")
    return client


# Example usage
if __name__ == "__main__":
    # Example SMU usage
    print("SMU Client Example")
    print("=" * 20)
    
    try:
        smu = create_smu_client()
        print("✓ Connected to SMU server")
        
        # Basic measurements
        smu.enable_channel(1)
        smu.set_voltage(1, 3.3)
        voltage = smu.measure_voltage(1)
        current = smu.measure_current(1)
        
        print(f"Channel 1: {voltage:.3f}V, {current:.6f}A")
        
    except MinismuSHError as e:
        print(f"SMU Error: {e}")
    
    print("\nBattery Cycler Example")
    print("=" * 25)
    
    try:
        cycler = create_cycler_client()
        print("✓ Connected to cycler server")
        
        # Create simple 3-cycle test
        steps = cycler.create_cycle_steps(
            charge_current=0.01,    # 10 mA charge
            discharge_current=-0.01  # 10 mA discharge
        )
        
        metadata = {
            'testName': 'Library Example Test',
            'batteryId': 'DEMO_CELL',
            'operator': 'python_library'
        }
        
        result = cycler.start_test(
            channel=1,
            steps=steps,
            cycles=3,
            metadata=metadata
        )
        
        print(f"✓ Test started: {result.get('message')}")
        print("Monitor with cycler.get_status() or cycler.wait_for_completion()")
        
    except MinismuSHError as e:
        print(f"Cycler Error: {e}")