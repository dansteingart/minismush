# Curl Command Examples for minismush Battery Cycler

This file contains practical curl commands for testing all major features of the minismush battery cycler system.

## Prerequisites

1. **Start the minismush server:**
   ```bash
   node nodeforwarder.js 3000 /dev/ttyUSB0 115200
   ```

2. **Set base URL variable for convenience:**
   ```bash
   export BASE_URL="http://localhost:3000"
   ```

## Basic SMU Commands

### Device Identity and Status
```bash
# Get SMU device identity
curl -X GET "$BASE_URL/smu/get_identity"

# Get available serial ports
curl -X GET "$BASE_URL/list_ports"

# Get current data buffer
curl -X GET "$BASE_URL/read/"
```

### Channel Control
```bash
# Enable channel 1
curl -X POST "$BASE_URL/smu/enable_channel" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Disable channel 1
curl -X POST "$BASE_URL/smu/disable_channel" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Set voltage range to AUTO
curl -X POST "$BASE_URL/smu/set_voltage_range" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "range": "AUTO"}'
```

### Basic Measurements
```bash
# Set 3.3V on channel 1
curl -X POST "$BASE_URL/smu/set_potential" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "potential": 3.3}'

# Set 10mA current on channel 1
curl -X POST "$BASE_URL/smu/set_current" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "current": 0.010}'

# Measure voltage on channel 1
curl -X POST "$BASE_URL/smu/measure_voltage" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Measure current on channel 1
curl -X POST "$BASE_URL/smu/measure_current" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Measure both voltage and current
curl -X POST "$BASE_URL/smu/measure_voltage_and_current" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'
```

## Battery Cycler Commands

**Note**: The battery cycler automatically handles channel enable/disable operations during cycling. CC and CV steps enable the channel, while OCV and REST steps disable it. Manual channel control is not needed during cycling operations.

### Step Definition Validation
```bash
# Validate a simple 2-step cycle definition
curl -X POST "$BASE_URL/cycler/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.010, "cutoff_V": 4.2, "cutoff_time_s": 3600},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 1800},
      {"cycle": "end"}
    ]
  }'
```

### Simple Battery Cycle Test
```bash
# Start a basic 3-cycle battery test
# Note: Channel enable/disable is handled automatically by the cycler
curl -X POST "$BASE_URL/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 3,
    "enableLogging": true,
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.020, "cutoff_V": 4.2, "cutoff_time_s": 7200},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 3600},
      {"mode": "cc", "current": -0.020, "cutoff_V": 3.0, "cutoff_time_s": 7200},
      {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.001, "cutoff_time_s": 1800},
      {"cycle": "end"}
    ]
  }'
```

### Advanced Test with Metadata
```bash
# Start a test with comprehensive metadata
curl -X POST "$BASE_URL/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 5,
    "enableLogging": true,
    "metadata": {
      "testName": "Formation Cycling Test",
      "testType": "formation",
      "operator": "lab_technician",
      "batteryId": "CELL_001",
      "batteryType": "LiFePO4",
      "capacityAh": "3.2",
      "temperatureC": "25",
      "notes": "Initial formation cycles at C/10 rate"
    },
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.320, "cutoff_V": 3.6, "cutoff_time_s": 14400},
      {"mode": "cv", "voltage": 3.6, "cutoff_A": 0.032, "cutoff_time_s": 7200},
      {"mode": "cc", "current": -0.320, "cutoff_V": 2.5, "cutoff_time_s": 14400},
      {"mode": "cv", "voltage": 2.5, "cutoff_A": -0.032, "cutoff_time_s": 3600},
      {"cycle": "end"}
    ]
  }'
```

### Multi-Step Complex Cycle
```bash
# Advanced cycle with multiple charge/discharge steps
curl -X POST "$BASE_URL/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 2,
    "enableLogging": true,
    "metadata": {
      "testName": "Multi-Step Capacity Test",
      "batteryId": "CELL_002",
      "notes": "CC-CV charge, rest, pulse discharge, CV discharge"
    },
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.050, "cutoff_V": 4.2, "cutoff_time_s": 5400},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.005, "cutoff_time_s": 3600},
      {"mode": "rest", "cutoff_time_s": 1800},
      {"mode": "cc", "current": -0.100, "cutoff_V": 3.5, "cutoff_time_s": 1800},
      {"mode": "rest", "cutoff_time_s": 900},
      {"mode": "cc", "current": -0.050, "cutoff_V": 3.0, "cutoff_time_s": 7200},
      {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.005, "cutoff_time_s": 3600},
      {"cycle": "end"}
    ]
  }'
```

### Cycler Control Commands
```bash
# Get current cycler status
curl -X GET "$BASE_URL/cycler/status"

# Pause the running cycler
curl -X POST "$BASE_URL/cycler/pause"

# Resume the paused cycler
curl -X POST "$BASE_URL/cycler/resume"

# Stop the cycler
curl -X POST "$BASE_URL/cycler/stop"
```

## Data Streaming and System Management

### Data Streaming Control
```bash
# Start data streaming on channel 1
curl -X POST "$BASE_URL/smu/start_streaming" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Set sample rate to 1 Hz
curl -X POST "$BASE_URL/smu/set_sample_rate" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "rate": 1}'

# Stop data streaming
curl -X POST "$BASE_URL/smu/stop_streaming" \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'
```

### System Management
```bash
# Set LED brightness to 75%
curl -X POST "$BASE_URL/smu/set_led_brightness" \
  -H "Content-Type: application/json" \
  -d '{"brightness": 75}'

# Get LED brightness
curl -X GET "$BASE_URL/smu/get_led_brightness"

# Get system temperatures
curl -X GET "$BASE_URL/smu/get_temperatures"

# Reset SMU device
curl -X POST "$BASE_URL/smu/reset"
```

### WiFi Configuration
```bash
# Scan for WiFi networks
curl -X GET "$BASE_URL/smu/wifi_scan"

# Get WiFi status
curl -X GET "$BASE_URL/smu/get_wifi_status"

# Set WiFi credentials
curl -X POST "$BASE_URL/smu/set_wifi_credentials" \
  -H "Content-Type: application/json" \
  -d '{"ssid": "LabNetwork", "password": "password123"}'

# Enable WiFi
curl -X POST "$BASE_URL/smu/enable_wifi"

# Disable WiFi
curl -X POST "$BASE_URL/smu/disable_wifi"
```

## Data Logging Commands

### Manual Data Logging (Non-Cycler)
```bash
# Start CSV logging
curl -X POST "$BASE_URL/start_csv_log" \
  -H "Content-Type: application/json" \
  -d '{"filename": "manual_test.csv", "columns": ["timestamp", "voltage", "current", "notes"]}'

# Start SQLite logging
curl -X POST "$BASE_URL/start_sqlite_log" \
  -H "Content-Type: application/json" \
  -d '{"filename": "manual_test.db", "table": "measurements", "columns": ["timestamp", "voltage", "current"]}'

# Get logging status
curl -X GET "$BASE_URL/log_status"

# Stop logging
curl -X POST "$BASE_URL/stop_log"
```

## Real-World Test Scenarios

**Note**: All battery cycling tests automatically manage channel states. No manual channel enabling is required.

### 1. Quick Battery Health Check
```bash
# 30-minute capacity test
curl -X POST "$BASE_URL/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 1,
    "enableLogging": true,
    "metadata": {
      "testName": "Quick Health Check",
      "batteryId": "UNKNOWN",
      "notes": "30-minute capacity assessment"
    },
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.100, "cutoff_V": 4.2, "cutoff_time_s": 1800},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.010, "cutoff_time_s": 900},
      {"mode": "cc", "current": -0.100, "cutoff_V": 3.0, "cutoff_time_s": 1800},
      {"cycle": "end"}
    ]
  }'
```

### 2. Formation Cycling (Low Rate)
```bash
# Formation cycling at C/20 rate
curl -X POST "$BASE_URL/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 3,
    "enableLogging": true,
    "metadata": {
      "testName": "Formation Cycling",
      "testType": "formation",
      "batteryId": "NEW_CELL_001",
      "capacityAh": "2.0",
      "notes": "Initial formation at C/20"
    },
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 0.100, "cutoff_V": 4.2, "cutoff_time_s": 28800},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.005, "cutoff_time_s": 7200},
      {"mode": "cc", "current": -0.100, "cutoff_V": 3.0, "cutoff_time_s": 28800},
      {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.005, "cutoff_time_s": 3600},
      {"cycle": "end"}
    ]
  }'
```

### 3. High-Rate Performance Test
```bash
# High-rate discharge test
curl -X POST "$BASE_URL/cycler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": 1,
    "cycles": 5,
    "enableLogging": true,
    "metadata": {
      "testName": "High Rate Performance",
      "testType": "performance",
      "batteryId": "PERF_001",
      "notes": "1C charge, 2C discharge test"
    },
    "steps": [
      {"cycle": "start"},
      {"mode": "cc", "current": 1.000, "cutoff_V": 4.2, "cutoff_time_s": 5400},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.050, "cutoff_time_s": 3600},
      {"mode": "rest", "cutoff_time_s": 1800},
      {"mode": "cc", "current": -2.000, "cutoff_V": 3.0, "cutoff_time_s": 3600},
      {"mode": "rest", "cutoff_time_s": 1800},
      {"cycle": "end"}
    ]
  }'
```

## Response Examples

### Successful Cycler Start Response
```json
{
  "success": true,
  "message": "Cycler started successfully",
  "channel": 1,
  "totalSteps": 5,
  "cycles": 10
}
```

### Cycler Status Response
```json
{
  "isRunning": true,
  "isPaused": false,
  "channel": 1,
  "currentCycle": 3,
  "totalCycles": 10,
  "currentStepIndex": 2,
  "currentStep": {
    "mode": "cv",
    "voltage": 4.2,
    "cutoff_A": 0.001,
    "cutoff_time_s": 3600
  },
  "stepTime": 1245.6,
  "totalTime": 12847.3,
  "totalAh": 0.8234,
  "stepAh": 0.0156,
  "cycleAh": 0.2341,
  "logFile": "battery_test_2024-01-15T10-30-45-123Z.db"
}
```

### Error Response Example
```json
{
  "error": "Channel and steps are required"
}
```

## Tips for Testing

1. **Use jq for pretty JSON output:**
   ```bash
   curl -X GET "$BASE_URL/cycler/status" | jq
   ```

2. **Save responses to files:**
   ```bash
   curl -X GET "$BASE_URL/cycler/status" > status.json
   ```

3. **Monitor real-time with watch:**
   ```bash
   watch -n 5 'curl -s "$BASE_URL/cycler/status" | jq ".currentCycle, .stepTime, .totalAh"'
   ```

4. **Check logs for errors:**
   ```bash
   tail -f /path/to/minismush/logs
   ```

5. **Test server connectivity:**
   ```bash
   curl -X GET "$BASE_URL/read/" --connect-timeout 5
   ```