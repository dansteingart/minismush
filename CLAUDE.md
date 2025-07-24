# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**minismush** is a Node.js-based serial communication and data logging platform for electrochemistry applications using Source Measure Units (SMUs). It provides web-based interfaces for controlling SMU devices via serial communication, with real-time data logging and visualization.

## Architecture

The project has a **layered architecture** with multiple independent but related components:

### 1. Root Level - Basic NodeForwarder
- **Entry Point**: `nodeforwarder.js`
- **Purpose**: Core serial-to-HTTP bridge utility
- **Web Interfaces**: `connect.html`, `console.html` (basic terminal-style)

### 2. Main SMU Application - Enhanced Features
- **Location**: `mush/` directory
- **Entry Point**: `mush/server.js`
- **Purpose**: Advanced electrochemistry data logging and control system

### 3. Key Classes and Components
- **SMU Class** (`mush/smu.js`): Hardware abstraction layer for SMU communication with SCPI-like command protocol
- **DataLogger Class** (`mush/dataLogger.js`): Session-based CSV logging with JSON metadata and statistical analysis
- **Web Interface** (`mush/public/`): Modern HTML5 frontend with Plotly.js visualization
- **NodeForwarder** (`mush/nodeforwarder/`): Standalone serial bridge with SMUSH SMU-specific interface

## Development Commands

### Root NodeForwarder
```bash
npm install
node nodeforwarder.js [HTTP_PORT] [SERIAL_PORT] [BAUD_RATE] [BUFFER_SIZE]
# Example: node nodeforwarder.js 9000 /dev/ttyUSB0 115200 10000
```

### Main SMU Application
```bash
cd mush/
npm install
npm start  # or node server.js
```

### Environment Variables (SMU Application)
- `PORT`: HTTP server port (default: 3000)
- `SERIAL_PORT`: Serial device path (e.g., /dev/ttyUSB0)
- `BAUD_RATE`: Serial communication baud rate (default: 115200)

## Data Flow

```
Hardware SMU Device → SMU/NodeForwarder Classes → Express.js REST API → Web Interface + Socket.io → DataLogger → CSV/JSON Files
```

## REST API Structure

### NodeForwarder Endpoints
- `GET /read/` - Read current buffer contents
- `GET /write/{payload}` - Write data to serial port
- `GET /writecf/{payload}` - Write with CRLF
- `POST /write` - JSON payload writing
- `GET /reconnect` - Reconnect serial port
- `GET /list_ports` - Available serial ports

### SMU Application Features
- Complete SCPI command implementation for SMU control
- Multi-channel voltage/current control and measurement
- Session-based data logging with CSV export
- Real-time WebSocket streaming for live data
- Statistical analysis and historical data retrieval

## Key Dependencies
- `serialport`: Hardware serial communication
- `express`: Web server and REST API
- `socket.io`: Real-time bidirectional communication
- `cors`: Cross-origin resource sharing
- `body-parser`: HTTP request parsing
- `plotly.js`: Frontend data visualization (web interfaces)
- `csv-writer`: Data export functionality

## Directory Structure Notes
- `data/`: Generated data sessions (CSV and JSON files)
- `mush/mush/`: Duplicate copy of main SMU application
- `static/`: jQuery library for basic interfaces
- Multiple nested package.json files - each component has independent dependencies

## Development Notes
- The project supports multi-platform serial communication (Linux, macOS, Windows)
- Web interfaces use both basic terminal-style and modern responsive designs
- Real-time data visualization with configurable sample rates
- Session management allows loading and analyzing historical experiments
- CORS enabled for cross-origin API access