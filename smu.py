import serial
import socket
import time
import json
from enum import Enum
from typing import Optional, Tuple, Dict, Union
from dataclasses import dataclass

@dataclass
class WifiStatus:
    connected: bool
    ssid: str
    ip_address: str
    rssi: int

class ConnectionType(Enum):
    USB = "usb"
    NETWORK = "network"

class SMUException(Exception):
    """Custom exception for SMU-related errors"""
    pass

class SMU:
    """Interface for the SMU device supporting both USB and network connections"""
    
    def __init__(self, connection_type: ConnectionType, port: str = "/dev/ttyACM0", 
                 host: str = "192.168.1.1", tcp_port: int = 3333):
        """
        Initialize SMU connection
        
        Args:
            connection_type: Type of connection (USB or Network)
            port: Serial port for USB connection
            host: IP address for network connection
            tcp_port: TCP port for network connection
        """
        self.connection_type = connection_type
        self._connection = None
        
        if connection_type == ConnectionType.USB:
            try:
                self._connection = serial.Serial(port, 115200, timeout=1)
            except serial.SerialException as e:
                raise SMUException(f"Failed to open USB connection: {e}")
        else:
            try:
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connection.connect((host, tcp_port))
                self._connection.settimeout(1.0)
            except socket.error as e:
                raise SMUException(f"Failed to open network connection: {e}")

    def _send_command(self, command: str) -> str:
        """
        Send command and get response
        
        Args:
            command: Command string to send
            
        Returns:
            Response from device
        """
        try:
            if self.connection_type == ConnectionType.USB:
                self._connection.write(f"{command}\n".encode())
                response = self._connection.readline().decode().strip()
            else:
                self._connection.send(f"{command}".encode())
                response = self._connection.recv(1024).decode().strip()
            
            # Check if response is an acknowledgment
            if response == "OK":
                return response
                
            # For query commands (ending with ?), return the raw response
            if command.endswith("?"):
                return response
                
            # For other commands, return the response
            return response
            
        except (serial.SerialException, socket.error) as e:
            raise SMUException(f"Communication error: {e}")

    def get_identity(self) -> str:
        """Get device identification"""
        return self._send_command("*IDN?")

    def reset(self):
        """Reset the device"""
        self._send_command("*RST")

    # Source and Measurement Methods
    def set_voltage(self, channel: int, voltage: float):
        """
        Set voltage for specified channel
        
        Args:
            channel: Channel number (1 or 2)
            voltage: Voltage value in volts
        """
        self._send_command(f"SOUR{channel}:VOLT {voltage}")

    def set_current(self, channel: int, current: float):
        """
        Set current for specified channel
        
        Args:
            channel: Channel number (1 or 2)
            current: Current value in amperes
        """
        self._send_command(f"SOUR{channel}:CURR {current}")

    def measure_voltage(self, channel: int) -> float:
        """
        Measure voltage on specified channel
        
        Args:
            channel: Channel number (1 or 2)
            
        Returns:
            Measured voltage in volts
        """
        response = self._send_command(f"MEAS{channel}:VOLT?")
        return float(response)

    def measure_current(self, channel: int) -> float:
        """
        Measure current on specified channel
        
        Args:
            channel: Channel number (1 or 2)
            
        Returns:
            Measured current in amperes
        """
        response = self._send_command(f"MEAS{channel}:CURR?")
        return float(response)
    
    def measure_voltage_and_current(self, channel: int) -> Tuple[float, float]:
        """
        Measure both voltage and current on specified channel
        
        Args:
            channel: Channel number (1 or 2)
            
        Returns:
            Tuple of (voltage, current)
        """
        response = self._send_command(f"MEAS{channel}:VOLT:CURR?")
        voltage, current = map(float, response.split(','))
        return voltage, current

    # Channel Configuration Methods
    def enable_channel(self, channel: int):
        """Enable specified channel"""
        self._send_command(f"OUTP{channel} ON")

    def disable_channel(self, channel: int):
        """Disable specified channel"""
        self._send_command(f"OUTP{channel} OFF")

    def set_voltage_range(self, channel: int, range_type: str):
        """
        Set voltage range for channel
        
        Args:
            channel: Channel number (1 or 2)
            range_type: 'AUTO', 'LOW', or 'HIGH'
        """
        if range_type not in ['AUTO', 'LOW', 'HIGH']:
            raise ValueError("Range type must be 'AUTO', 'LOW', or 'HIGH'")
        self._send_command(f"SOUR{channel}:VOLT:RANGE {range_type}")

    def set_mode(self, channel: int, mode: str):
        """
        Set channel mode (FIMV or FVMI)
        
        Args:
            channel: Channel number (1 or 2)
            mode: 'FIMV' or 'FVMI'
        """
        if mode not in ['FIMV', 'FVMI']:
            raise ValueError("Mode must be 'FIMV' or 'FVMI'")
        self._send_command(f"SOUR{channel}:{mode} ENA")

    # Data Streaming Methods
    def start_streaming(self, channel: int):
        """Start data streaming for specified channel"""
        self._send_command(f"SOUR{channel}:DATA:STREAM ON")

    def stop_streaming(self, channel: int):
        """Stop data streaming for specified channel"""
        self._send_command(f"SOUR{channel}:DATA:STREAM OFF")

    def read_streaming_data(self) -> Tuple[int, float, float, float]:
        """
        Read a single data packet from the streaming buffer
        
        Returns:
            Tuple of (channel, timestamp, voltage, current) from the streaming data
        """
        if self.connection_type == ConnectionType.USB:
            # Read the data packet
            data = self._connection.readline().decode().strip()
            try:
                channel, timestamp, voltage, current = data.split(',')
                return int(channel), float(timestamp), float(voltage), float(current)
            except ValueError as e:
                raise SMUException(f"Failed to parse streaming data: {data}")
        else:
            raise SMUException("Streaming is only supported over USB connection")

    def set_sample_rate(self, channel: int, rate: float):
        """
        Set sample rate for specified channel
        
        Args:
            channel: Channel number (1 or 2)
            rate: Sample rate in Hz
        """
        self._send_command(f"SOUR{channel}:DATA:SRATE {rate}")

    # System Configuration Methods
    def set_led_brightness(self, brightness: int):
        """
        Set LED brightness (0-100)
        
        Args:
            brightness: Brightness percentage (0-100)
        """
        if not 0 <= brightness <= 100:
            raise ValueError("Brightness must be between 0 and 100")
        self._send_command(f"SYST:LED {brightness}")

    def get_led_brightness(self) -> int:
        """Get current LED brightness"""
        response = self._send_command("SYST:LED?")
        return int(response)

    def get_temperatures(self) -> Tuple[float, float, float]:
        """
        Get system temperatures
        
        Returns:
            Tuple of (adc_temp, channel1_temp, channel2_temp)
        """
        response = self._send_command("SYST:TEMP?")
        return tuple(map(float, response.split(',')))

    def set_time(self, timestamp: int):
        """
        Set the device's internal clock using a Unix timestamp in milliseconds
        
        Args:
            timestamp: Unix timestamp in milliseconds
        """
        self._send_command(f"SYST:TIME {timestamp}")

    # WiFi Configuration Methods
    def wifi_scan(self) -> list:
        """
        Scan for available WiFi networks
        
        Returns:
            List of available networks
        """
        response = self._send_command("SYST:WIFI:SCAN?")
        return json.loads(response)

    def get_wifi_status(self) -> WifiStatus:
        """
        Get current WiFi status
        
        Returns:
            WifiStatus object with connection details
        """
        response = self._send_command("SYST:WIFI?")
        status_dict = json.loads(response)
        return WifiStatus(
            connected=status_dict.get('connected', False),
            ssid=status_dict.get('ssid', ''),
            ip_address=status_dict.get('ip', ''),
            rssi=status_dict.get('rssi', 0)
        )

    def set_wifi_credentials(self, ssid: str, password: str):
        """
        Set WiFi credentials
        
        Args:
            ssid: Network SSID
            password: Network password
        """
        self._send_command(f'SYST:WIFI:SSID "{ssid}"')
        self._send_command(f'SYST:WIFI:PASS "{password}"')

    def enable_wifi(self):
        """Enable WiFi"""
        self._send_command("SYST:WIFI ENA")

    def disable_wifi(self):
        """Disable WiFi"""
        self._send_command("SYST:WIFI DIS")

    def close(self):
        """Close the connection"""
        if self._connection:
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
