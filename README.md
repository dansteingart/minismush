# minismush

**A Node.js-based serial communication and data logging platform for electrochemistry applications using the miniSMU S01.**

*Forked from the [nodeforwarder](https://github.com/original/nodeforwarder) to be used with the fantastic Undalogic [miniSMU MS01](https://www.undalogic.com/minismu), 

## Overview

minismush provides a complete HTTP API wrapper for SMU (Source Measure Unit) devices, combining the core serial-to-HTTP bridge functionality of nodeforwarder with advanced electrochemistry features including:

- **Complete SMU Control**: Voltage/current setting, measurement, channel control
- **Real-time Data Logging**: CSV and SQLite logging with auto-schema detection  
- **Streaming Data Capture**: Live data streaming with configurable sample rates
- **System Management**: LED control, temperature monitoring, WiFi configuration
- **WebSocket Support**: Real-time bidirectional communication for live data

## Architecture

### Core Serial Bridge (inherited from nodeforwarder)
- **Entry Point**: `nodeforwarder.js`
- **Purpose**: Serial-to-HTTP bridge with buffer management
- **Web Interfaces**: `connect.html`, `console.html` (basic terminal-style)

### SMU-Specific Extensions  
- **SCPI Command Interface**: Full SMU command protocol implementation
- **Data Logging System**: Session-based CSV/SQLite logging with metadata
- **Real-time Streaming**: WebSocket-based live data visualization
- **Multi-format Support**: JSON, CSV, and delimited data parsing

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
# CSV Logging
POST /start_csv_log           {"filename": "data.csv", "columns": ["voltage", "current"]}

# SQLite Logging  
POST /start_sqlite_log        {"filename": "data.db", "table": "readings", "columns": [...]}

# Logging Control
POST /stop_log                
GET  /log_status              
```

## Data Logging Features

### Auto-Schema Detection
- Automatically detects column structure from first data row
- Supports JSON arrays, objects, and delimited strings  
- Falls back to generic column names (`col_01`, `col_02`, etc.)

### Auto-Append Functionality
- Restarting logging with same filename/table continues from last position
- No data duplication or overwrites

### Flexible Data Formats
- **CSV**: Human-readable, Excel-compatible
- **SQLite**: Structured database with full query capabilities
- **Real-time**: WebSocket streaming for live visualization

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
└── CLAUDE.md           # Development documentation
```

## Example Usage

### Set Voltage and Log Data
```bash
# Start CSV logging
curl -X POST http://localhost:3000/start_csv_log \
  -H "Content-Type: application/json" \
  -d '{"filename": "experiment.csv", "columns": ["channel", "timestamp", "voltage", "current", "status"]}'

# Set channel 1 to 3.3V
curl -X POST http://localhost:3000/smu/set_potential \
  -H "Content-Type: application/json" \
  -d '{"channel": 1, "potential": 3.3}'

# Measure voltage
curl -X POST http://localhost:3000/smu/measure_voltage \
  -H "Content-Type: application/json" \
  -d '{"channel": 1}'

# Stop logging
curl -X POST http://localhost:3000/stop_log
```

### WebSocket Data Streaming
```javascript
const socket = io('http://localhost:3000');
socket.on('data', (data) => {
  console.log('Real-time data:', data);
});
```


