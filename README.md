# minismush

**A Node.js-based serial communication and data logging platform for electrochemistry applications using Source Measure Units (SMUs).**

## Overview

minismush provides a complete HTTP API wrapper for SMU (Source Measure Unit) devices, combining serial-to-HTTP bridge functionality with advanced SMU control and real-time data logging capabilities including:

- **SMU Control System**: Complete SCPI command implementation with voltage/current control
- **Battery Cycling**: Automated cycling with CC/CV/OCV modes and intelligent cutoff detection
- **Advanced Data Logging**: Dual logging system with structured data and command tracking
- **Array-Based Processing**: Real-time data processing with ch1/ch2 array access
- **Real-time Streaming**: WebSocket support for live data visualization
- **System Management**: LED control, temperature monitoring, WiFi configuration

## Architecture

The project consists of a single-layer Node.js application with the following components:

### Core Application
- **Entry Point**: `nodeforwarder.js` - Main server providing both basic serial bridge and SMU-specific functionality
- **SMU Python Interface**: `smu.py` - Reference Python implementation of SMU command protocol
- **Web Interfaces**: `connect.html`, `console.html` - Basic terminal-style interfaces

### Key Features
- **Serial-to-HTTP Bridge**: Core nodeforwarder functionality for generic serial communication
- **SMU Control System**: Complete SCPI command implementation with voltage/current control
- **Battery Cycling**: Automated cycling with step sequences and intelligent cutoff logic
- **Data Logging**: Auto-schema detection with CSV and SQLite support, dual logging system
- **Real-time Streaming**: WebSocket support for live data visualization with array-based processing
- **System Management**: LED control, temperature monitoring, WiFi configuration

## Quick Start

### Installation
```bash
npm install
```

### Basic Usage
```bash
node nodeforwarder.js [HTTP_PORT] [SERIAL_PORT] [BAUD_RATE] [BUFFER_SIZE]

# Example:
node nodeforwarder.js 3000 /dev/ttyUSB0 115200 10000
```

### Environment Variables
- `PORT`: HTTP server port (default: 3000)
- `SERIAL_PORT`: Serial device path (e.g., /dev/ttyUSB0)  
- `BAUD_RATE`: Serial communication baud rate (default: 115200)

## API Endpoints

### Core Serial Communication (from nodeforwarder)
```bash
GET  /read/                    # Read current buffer contents
GET  /write/{payload}          # Write data to serial port  
GET  /writecf/{payload}        # Write with CRLF
POST /write                    # JSON payload writing
GET  /reconnect                # Reconnect serial port
GET  /list_ports               # Available serial ports
```

### SMU Control APIs
```bash
# Device Identity & Control
GET  /smu/get_identity         # Get device identification
POST /smu/reset                # Reset device

# Voltage & Current Control  
POST /smu/set_potential        {"channel": 1, "potential": 3.3}
POST /smu/set_current          {"channel": 1, "current": 0.001}

# Measurements
POST /smu/measure_voltage      {"channel": 1}
POST /smu/measure_current      {"channel": 1}  
POST /smu/measure_voltage_and_current  {"channel": 1}

# Channel Management
POST /smu/enable_channel       {"channel": 1}
POST /smu/disable_channel      {"channel": 1}
POST /smu/set_voltage_range    {"channel": 1, "range": "AUTO"}
```

### Battery Cycling APIs
```bash
# Cycling Control
POST /cycler/start             {"steps": [...], "channel": 1}
POST /cycler/stop              # Stop active cycling
GET  /cycler/status            # Get current cycling status

# Data Access
GET  /cycler/get_ch1_data      # Get channel 1 array data
GET  /cycler/get_ch2_data      # Get channel 2 array data
POST /cycler/analyze_step      {"channel": 1, "step_type": "cc"}
```

### Data Streaming APIs
```bash
POST /smu/start_streaming      {"channel": 1}
POST /smu/stop_streaming       {"channel": 1}
POST /smu/set_sample_rate      {"channel": 1, "rate": 1000}
```

### System Management APIs
```bash
POST /smu/set_led_brightness   {"brightness": 50}
GET  /smu/get_led_brightness   
GET  /smu/get_temperatures     
POST /smu/set_time            {"timestamp": 1642086400000}
```

### WiFi Configuration APIs
```bash
GET  /smu/wifi_scan           
GET  /smu/get_wifi_status     
POST /smu/set_wifi_credentials {"ssid": "MyWiFi", "password": "secret"}
POST /smu/enable_wifi         
POST /smu/disable_wifi        
```

### Data Logging APIs
```bash
# Enhanced Logging (auto-creates /data/battery/ directory)
POST /start_csv_log           {"filename": "experiment_01", "channels": [1,2]}
POST /start_sqlite_log        {"filename": "experiment.db", "table": "readings"}

# Logging Control
POST /stop_log                # Stops both data and command logging
GET  /log_status              # Get current logging status

# Log Files Created:
# /data/battery/experiment_01.csv      - Structured channel data with SMU state
# /data/battery/experiment_01_cmd.csv  - Command log with Unix timestamps
```

## Data Logging Features

### Dual Logging System
- **Data Logs**: Structured channel data with SMU state and cycling context
- **Command Logs**: All SMU commands with Unix timestamps for debugging
- **Auto-Directory**: Creates `/data/battery/` structure automatically

### Enhanced Data Structure
- **Unix Timestamps**: Correlation between data and commands
- **SMU State**: Current voltage/current settings included in each log entry
- **Cycling Context**: Step information and cycling state when active
- **Channel-Specific**: Separate ch1/ch2 data streams with proper parsing

### Flexible Data Formats
- **CSV**: Human-readable, Excel-compatible with structured columns
- **SQLite**: Structured database with full query capabilities
- **Real-time**: WebSocket streaming for live visualization with array access

## Development

### Dependencies
```json
{
  "serialport": "^9.2.4",
  "express": "^4.17.1", 
  "socket.io": "^4.3.1",
  "csv-writer": "^1.6.0",
  "sqlite3": "^5.0.2",
  "body-parser": "^1.19.0"
}
```

### Directory Structure
```
minismush/
├── nodeforwarder.js      # Main server with SMU extensions
├── smu.py               # Python SMU interface reference
├── package.json         # Dependencies
├── connect.html         # Connection interface
├── console.html         # Terminal interface  
├── static/              # Frontend assets
├── examples/            # Example scripts and documentation
│   ├── simple_cycling_example.py
│   ├── battery_cycling_example.py
│   ├── array_based_cycling.py
│   ├── curl_examples.md
│   └── README.md
├── data/               # Auto-created logging directory
│   └── battery/        # Battery experiment logs
└── CLAUDE.md          # Development documentation
```

## Example Usage

### Battery Cycling with Logging
```bash
# Start enhanced logging
curl -X POST http://localhost:3000/start_csv_log \
  -H "Content-Type: application/json" \
  -d '{"filename": "battery_test_01", "channels": [1,2]}'

# Start battery cycling
curl -X POST http://localhost:3000/cycler/start \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"mode": "cc", "current": 0.001, "cutoff_V": 4.2, "cutoff_mAh": 100},
      {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.0001, "cutoff_min": 60},
      {"mode": "rest", "cutoff_min": 10}
    ],
    "channel": 1,
    "cycles": 5
  }'

# Monitor cycling status
curl http://localhost:3000/cycler/status

# Access real-time array data
curl http://localhost:3000/cycler/get_ch1_data

# Stop cycling and logging
curl -X POST http://localhost:3000/cycler/stop
curl -X POST http://localhost:3000/stop_log
```

### Real-time Data Access
```bash
# Get structured channel data arrays
curl http://localhost:3000/cycler/get_ch1_data
curl http://localhost:3000/cycler/get_ch2_data

# Analyze current step performance
curl -X POST http://localhost:3000/cycler/analyze_step \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "step_type": "cc"}'
```

### WebSocket Data Streaming
```javascript
const socket = io('http://localhost:3000');
socket.on('data', (data) => {
  console.log('Real-time data:', data);
});
```


