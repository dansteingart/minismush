# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**minismush** is a Node.js-based serial communication and data logging platform for electrochemistry applications using Source Measure Units (SMUs). It provides HTTP API wrapper for SMU devices, combining serial-to-HTTP bridge functionality with advanced SMU control and real-time data logging capabilities.

## Architecture

The project consists of a single-layer Node.js application with the following components:

### Core Application
- **Entry Point**: `nodeforwarder.js` - Main server providing both basic serial bridge and SMU-specific functionality
- **SMU Python Interface**: `smu.py` - Reference Python implementation of SMU command protocol
- **Web Interfaces**: `connect.html`, `console.html` - Basic terminal-style interfaces

### Key Features
- **Serial-to-HTTP Bridge**: Core nodeforwarder functionality for generic serial communication
- **SMU Control System**: Complete SCPI command implementation with voltage/current control
- **Data Logging**: Auto-schema detection with CSV and SQLite support
- **Real-time Streaming**: WebSocket support for live data visualization
- **System Management**: LED control, temperature monitoring, WiFi configuration

## Development Commands

### Installation and Setup
```bash
npm install
```

### Running the Application
```bash
node nodeforwarder.js [HTTP_PORT] [SERIAL_PORT] [BAUD_RATE] [BUFFER_SIZE]

# Example:
node nodeforwarder.js 3000 /dev/ttyUSB0 115200 10000
```

### Environment Variables
- `PORT`: HTTP server port (default from first argument)
- `SERIAL_PORT`: Serial device path (e.g., /dev/ttyUSB0)
- `BAUD_RATE`: Serial communication baud rate (default: 115200)

## Code Architecture

### Main Server (`nodeforwarder.js`)
The single main file contains multiple functional layers:

1. **Serial Port Management** (`lines 71-137`): Handles dynamic serial port connection/reconnection with proper error handling
2. **Data Logging System** (`lines 142-276`): Auto-schema detection supporting both CSV and SQLite backends
3. **Basic HTTP Endpoints** (`lines 288-355`): Generic serial read/write operations inherited from nodeforwarder
4. **SMU Command Functions** (`lines 479-537`): SCPI command implementations for device control
5. **SMU REST API** (`lines 538-817`): Complete HTTP API with proper error handling and validation

### Key Design Patterns
- **Unified Buffer Management**: Single circular buffer (`buf`) for all serial data with configurable length
- **Auto-Schema Detection**: Automatic column detection from first data row supporting JSON, delimited, and raw formats
- **Response Pattern**: Consistent 200ms delay response pattern for SMU commands to allow device processing
- **Error Handling**: Comprehensive try-catch blocks with proper HTTP status codes

### Data Flow
```
SMU Device → Serial Port → Circular Buffer → [HTTP API | WebSocket | Data Logger] → [Client | CSV/SQLite]
```

## REST API Structure

### Core Serial Communication
- `GET /read/` - Read buffer contents
- `GET /write/{payload}` - Write to serial port
- `GET /writecf/{payload}` - Write with CRLF
- `POST /write` - JSON payload writing
- `GET /reconnect` - Reconnect serial port
- `GET /list_ports` - Available serial ports

### SMU Control API Patterns
All SMU endpoints follow consistent patterns:
- **Device Control**: `/smu/get_identity`, `/smu/reset`
- **Channel Operations**: `/smu/set_potential`, `/smu/measure_voltage`, `/smu/enable_channel`
- **System Management**: `/smu/set_led_brightness`, `/smu/get_temperatures`
- **WiFi Configuration**: `/smu/wifi_scan`, `/smu/set_wifi_credentials`
- **Data Streaming**: `/smu/start_streaming`, `/smu/set_sample_rate`

### Data Logging API
- `POST /start_csv_log` - Start CSV logging with optional column specification
- `POST /start_sqlite_log` - Start SQLite logging with table specification
- `POST /stop_log` - Stop active logging
- `GET /log_status` - Get current logging status

## Development Notes

### Dependencies
- `serialport`: Hardware serial communication
- `express`: Web server and REST API framework
- `socket.io`: Real-time WebSocket communication
- `csv-writer`: CSV file generation with append support
- `sqlite3`: SQLite database operations
- `body-parser`: HTTP request parsing
- `cors`: Cross-origin resource sharing

### Code Conventions
- Snake_case for SMU command functions (matches SCPI convention)
- CamelCase for JavaScript variables and functions
- Consistent error handling with try-catch blocks
- 200ms response delay for SMU commands (`response()` function)
- Auto-resource cleanup for logging operations

### Testing and Validation
The project includes comprehensive input validation:
- Channel number validation for SMU operations
- Range validation for LED brightness (0-100)
- SSID/password validation for WiFi operations
- Automatic parameter presence checks with meaningful error messages

### WebSocket Integration
Real-time data streaming through Socket.io:
- Automatic buffer broadcast on connection
- Input commands via `socket.on('input')`
- Data streaming via `io.emit('data')`