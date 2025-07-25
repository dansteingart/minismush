# SMU API Documentation

This document lists all available SMU (Source Measure Unit) API endpoints for the minismush system.

## Device Control

### Device Identity and Status
- **GET** `/smu/get_identity` - Get SMU device identification string
- **POST** `/smu/reset` - Reset the SMU device to default state

### Channel Management
- **POST** `/smu/enable_channel` - Enable specified channel
  ```json
  {"channel": 1}
  ```
- **POST** `/smu/disable_channel` - Disable specified channel
  ```json
  {"channel": 1}
  ```
- **POST** `/smu/set_voltage_range` - Set voltage range for channel
  ```json
  {"channel": 1, "range": "AUTO|LOW|HIGH"}
  ```

## Source Operations

### Voltage Control
- **POST** `/smu/set_potential` - Set output voltage
  ```json
  {"channel": 1, "potential": 3.3}
  ```

### Current Control  
- **POST** `/smu/set_current` - Set output current
  ```json
  {"channel": 1, "current": 0.010}
  ```

## Measurement Operations

### Voltage Measurements
- **POST** `/smu/measure_voltage` - Measure voltage on channel
  ```json
  {"channel": 1}
  ```

### Current Measurements
- **POST** `/smu/measure_current` - Measure current on channel
  ```json
  {"channel": 1}
  ```

### Combined Measurements
- **POST** `/smu/measure_voltage_and_current` - Measure both voltage and current
  ```json
  {"channel": 1}
  ```

## Data Streaming

### Stream Control
- **POST** `/smu/start_streaming` - Start continuous data streaming
  ```json
  {"channel": 1}
  ```
- **POST** `/smu/stop_streaming` - Stop data streaming
  ```json
  {"channel": 1}
  ```
- **POST** `/smu/set_sample_rate` - Set streaming sample rate
  ```json
  {"channel": 1, "rate": 1000}
  ```

## System Management

### LED Control
- **POST** `/smu/set_led_brightness` - Set LED brightness (0-100%)
  ```json
  {"brightness": 75}
  ```
- **GET** `/smu/get_led_brightness` - Get current LED brightness

### Temperature Monitoring
- **GET** `/smu/get_temperatures` - Get system temperatures

### Time Management
- **POST** `/smu/set_time` - Set device internal clock
  ```json
  {"timestamp": 1642086400000}
  ```

## WiFi Configuration

### Network Discovery
- **GET** `/smu/wifi_scan` - Scan for available WiFi networks
- **GET** `/smu/get_wifi_status` - Get current WiFi connection status

### WiFi Control
- **POST** `/smu/set_wifi_credentials` - Set WiFi network credentials
  ```json
  {"ssid": "NetworkName", "password": "password123"}
  ```
- **POST** `/smu/enable_wifi` - Enable WiFi connection
- **POST** `/smu/disable_wifi` - Disable WiFi connection

## Battery Cycler

### Cycler Control
- **POST** `/cycler/start` - Start battery cycling test
  ```json
  {
    "channel": 1,
    "cycles": 10,
    "enableLogging": true,
    "metadata": {
      "testName": "Formation Test",
      "batteryId": "CELL_001",
      "operator": "lab_tech"
    },
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.020, "cutoff_V": 4.2},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001},
      {"cycle": "end"}
    ]
  }
  ```
- **POST** `/cycler/stop` - Stop cycling test
- **POST** `/cycler/pause` - Pause cycling test
- **POST** `/cycler/resume` - Resume paused test
- **GET** `/cycler/status` - Get current cycling status
- **POST** `/cycler/validate` - Validate step definition
  ```json
  {"steps": [...]}
  ```

### Step Modes
- **CC (Constant Current)**: `{"mode": "cc", "current": 0.020, "cutoff_V": 4.2}`
- **CV (Constant Voltage)**: `{"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001}`
- **OCV (Open Circuit)**: `{"mode": "ocv", "cutoff_time_s": 1800}`
- **REST**: `{"mode": "rest", "cutoff_time_s": 3600}`

### Cutoff Conditions
- `cutoff_V` - Voltage cutoff (V)
- `cutoff_V_min` - Minimum voltage limit (V)
- `cutoff_V_max` - Maximum voltage limit (V)
- `cutoff_A` - Current cutoff (A)
- `cutoff_Ah` - Capacity cutoff (Ah)
- `cutoff_time_s` - Time cutoff (seconds)

## Core Serial Communication

### Basic Operations
- **GET** `/read/` - Read current serial buffer contents
- **GET** `/write/{payload}` - Write data to serial port
- **GET** `/writecf/{payload}` - Write data with CRLF
- **POST** `/write` - Write JSON payload
  ```json
  {"payload": "command_string"}
  ```

### Connection Management
- **GET** `/reconnect` - Reconnect to serial port
- **POST** `/reconnect` - Reconnect with new parameters
  ```json
  {"sp": "/dev/ttyUSB0", "baud": "115200"}
  ```
- **GET** `/disconnect` - Disconnect from serial port
- **GET** `/list_ports` - List available serial ports

### Status
- **GET** `/lastread/` - Get timestamp of last data received

## Data Logging (Non-Cycler)

### CSV Logging
- **POST** `/start_csv_log` - Start CSV data logging
  ```json
  {"filename": "data.csv", "columns": ["timestamp", "voltage", "current"]}
  ```

### SQLite Logging
- **POST** `/start_sqlite_log` - Start SQLite data logging
  ```json
  {"filename": "data.db", "table": "measurements", "columns": ["timestamp", "voltage"]}
  ```

### Logging Control
- **POST** `/stop_log` - Stop active logging
- **GET** `/log_status` - Get current logging status

## Web Interfaces

### Basic Interfaces
- **GET** `/` - Console interface (terminal-style)
- **GET** `/console` - Console interface
- **GET** `/connect` - Connection management interface

## Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {...}
}
```

### Error Response
```json
{
  "error": "Error description"
}
```

### Measurement Response
```json
{
  "voltage": 3.345,
  "current": 0.0234,
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

## Example Usage

### Basic Voltage Measurement
```bash
# Set 3.3V on channel 1
curl -X POST "http://localhost:3000/smu/set_potential" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "potential": 3.3}'

# Enable channel
curl -X POST "http://localhost:3000/smu/enable_channel" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Measure voltage
curl -X POST "http://localhost:3000/smu/measure_voltage" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'
```

### Simple Battery Test
```bash
curl -X POST "http://localhost:3000/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 3,
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.010, "cutoff_V": 4.2},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001},
      {"mode": "cc", "current": -0.010, "cutoff_V": 3.0},
      {"cycle": "end"}
    ]
  }'
```

## Notes

- All POST endpoints require `Content-Type: application/json` header
- Channel numbers typically start from 1
- Current values are in Amperes (A)
- Voltage values are in Volts (V)
- Time values are in seconds unless otherwise specified
- Battery cycler automatically manages channel enable/disable during cycling
- Real-time data is available via WebSocket connections
- All battery cycling tests create both SQLite and CSV log files