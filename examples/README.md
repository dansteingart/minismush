# Battery Cycling Examples

This directory contains Python examples demonstrating the minismush battery cycler functionality with enhanced array-based processing and automatic data organization.

## Prerequisites

1. **Start the minismush server:**
   ```bash
   node nodeforwarder.js 3000 /dev/ttyUSB0 115200 10000
   ```

2. **Install Python dependencies:**
   ```bash
   pip install requests
   ```

## Python Library

### minismush_client.py (Root Directory)

**Complete Python library** for SMU control and battery cycling operations.

**Classes:**
- `SMUClient` - Full SMU device control (voltage, current, measurements, streaming, WiFi, etc.)
- `BatteryCycler` - Battery cycling with step creation helpers and monitoring
- Exception classes for proper error handling

**Usage:**
```python
from minismush_client import SMUClient, BatteryCycler

# SMU operations
smu = SMUClient("http://localhost:3000")
smu.enable_channel(1)
smu.set_voltage(1, 3.3)
voltage = smu.measure_voltage(1)

# Battery cycling
cycler = BatteryCycler("http://localhost:3000")
steps = cycler.create_cycle_steps(charge_current=0.01, discharge_current=-0.01)
cycler.start_test(channel=1, steps=steps, cycles=10)
```

### library_example.py

**Comprehensive library demonstration** showing all major features.

**Features:**
- SMU control examples
- Simple battery cycling
- Formation cycling (different current rates)
- Custom step creation
- Error handling examples

**Usage:**
```bash
python library_example.py
```

## Script Examples

### 1. battery_cycling_example.py

**20-cycle formation test setup** - demonstrates different current rates.

**Features:**
- Sets up a complete 20-cycle test (first cycle at 2 mA, remaining at 20 mA)
- Validates step definition with server
- Starts test and lets node server handle all cycling
- Includes metadata for comprehensive logging

**Usage:**
```bash
python battery_cycling_example.py
```

**What it does:**
- Validates test configuration
- Starts the test on the server
- Server handles all timing, control, and data logging
- Provides monitoring commands for manual use

### 2. simple_cycling_example.py

**Basic 3-cycle test setup** - simple example for getting started.

**Features:**
- Creates a simple 3-cycle test at 10 mA
- Shows minimal test configuration
- Server handles all execution
- Demonstrates new array-based monitoring

**Usage:**
```bash
python simple_cycling_example.py
```

**What it does:**
- Sets up basic test parameters
- Validates and starts test
- Node server manages the complete cycling process
- Shows new enhanced monitoring endpoints

### 3. array_based_cycling.py ⭐ NEW

**Enhanced array-based cycling demonstration** - showcases new analysis features.

**Features:**
- Demonstrates array-based data processing
- Real-time step analysis using accumulated data
- Enhanced cutoff logic with trend analysis
- Direct access to ch1/ch2 data arrays
- Performance metrics with energy calculations

**Usage:**
```bash
python array_based_cycling.py
```

**What it showcases:**
- Voltage trend analysis for better step endings
- Current stability assessment
- Array-based performance metrics
- Direct data array access via REST API
- Enhanced monitoring with multiple analysis endpoints

## Battery Cycle Definition

Both examples use a standard 4-step battery cycle:

```json
[
  {"cycle": "start"},
  
  {"mode": "cc", "current": 0.002, "cutoff_V": 4.2, "cutoff_time_s": 7200},
  {"mode": "cv", "voltage": 4.2, "cutoff_A": 0.001, "cutoff_time_s": 3600},
  {"mode": "cc", "current": -0.002, "cutoff_V": 3.0, "cutoff_time_s": 7200},
  {"mode": "cv", "voltage": 3.0, "cutoff_A": -0.001, "cutoff_time_s": 1800},
  
  {"cycle": "end"}
]
```

### Step Explanation:

1. **CC Charge**: Constant current charge at specified rate until 4.2V
2. **CV Charge**: Constant voltage hold at 4.2V until current drops to 1 mA
3. **CC Discharge**: Constant current discharge at specified rate until 3.0V  
4. **CV Discharge**: Constant voltage hold at 3.0V for 30 minutes

### Current Rates:

- **First cycle**: 2 mA (±0.002 A)
- **Remaining cycles**: 20 mA (±0.020 A)

## API Endpoints Used

### Core Cycling Endpoints
- `POST /cycler/validate` - Validate step definitions
- `POST /cycler/start` - Start cycling with step definition
- `GET /cycler/status` - Monitor progress and metrics
- `POST /cycler/stop` - Stop cycling
- `POST /cycler/pause` - Pause cycling
- `POST /cycler/resume` - Resume paused cycling

### Enhanced Array-Based Endpoints ⭐ NEW
- `GET /cycler/step_analysis` - Real-time step analysis with array data
- `GET /cycler/performance_metrics` - Performance metrics with energy calculations
- `POST /cycler/process_arrays` - Force manual array processing
- `GET /data/ch1?limit=100` - Access ch1 data array
- `GET /data/ch2?limit=100` - Access ch2 data array
- `GET /data/analysis?channel=1` - Comprehensive data analysis

## Data Logging

When cycling starts with `enableLogging: true`, the system automatically creates **both SQLite and CSV files** in organized directories:

### Automatic Directory Structure ⭐ NEW
```
/data/
├── battery/                          # Battery cycling logs
│   ├── battery_test_TIMESTAMP.db     # SQLite database  
│   └── battery_test_TIMESTAMP.csv    # CSV export
└── other_data.csv                    # General data logs
```

### SQLite Database (Primary Format)
```
/data/battery/battery_test_2024-01-15T10-30-45-123Z.db
```

**Schema:**
- **`metadata` table**: Test configuration and parameters
  - `test_name`, `test_type`, `operator`, `battery_id`
  - `battery_type`, `capacity_ah`, `temperature_c`
  - `start_time`, `end_time`, `total_cycles`
  - `step_definition` (JSON), `software_version`

- **`data` table**: Time-series measurement data
  - `timestamp`, `unix_timestamp`, `cycle`, `step`
  - `step_type`, `step_time_s`, `total_time_s`
  - `voltage_v`, `current_a`, `step_ah`, `cycle_ah`, `total_ah`
  - `temperature_c`, `notes`

### CSV File (Compatibility)
```
battery_test_2024-01-15T10-30-45-123Z.csv
```
Same data as SQLite `data` table but in CSV format for Excel/analysis tools.

### Metadata Example
Tests can include custom metadata:
```python
metadata = {
    'testName': 'Formation Cycling Test',
    'operator': 'john_doe',
    'batteryId': 'CELL_001',
    'batteryType': 'LiFePO4',
    'capacityAh': '3.2',
    'temperatureC': '25',
    'notes': 'Initial formation cycles at C/10 rate'
}
```

## Manual Testing

You can also test the cycler using curl commands:

```bash
# Start cycling
curl -X POST http://localhost:3000/cycler/start \
  -H "Content-Type: application/json" \
  -d '{"channel":1,"steps":[...],"cycles":20}'

# Check status  
curl http://localhost:3000/cycler/status

# Stop cycling
curl -X POST http://localhost:3000/cycler/stop
```

## Error Handling

Both examples include error handling for:
- Server connection failures
- Invalid step definitions
- Cycler start/stop errors
- Network timeouts

Check console output for detailed error messages and troubleshooting information.

## Data Analysis

### 3. analyze_battery_data.py

**SQLite data analysis tool** for examining test results.

**Usage:**
```bash
python analyze_battery_data.py battery_test_*.db
```

**Features:**
- Complete test metadata display
- Cycle-by-cycle capacity summary
- Step-by-step breakdown analysis
- Capacity fade tracking over cycles
- CSV export for external analysis

**Example output:**
```
📋 TEST METADATA
==================================================
Battery Id          : CELL_001
Battery Type        : Li-ion
Test Name          : Formation Cycling Test
Total Cycles       : 20
Start Time         : 2024-01-15 10:30:45 UTC

🔄 CYCLE SUMMARY
================================================================================
Cycle  Points   Min V   Max V   Charge    Discharge  Time (h)  
--------------------------------------------------------------------------------
1      1250     3.000   4.200   0.9980    0.9850     8.5      
2      1180     3.000   4.200   0.9950    0.9820     4.2      
3      1165     3.000   4.200   0.9930    0.9800     4.1      
```

### SQLite Query Examples

Direct database queries for custom analysis:

```sql
-- View all metadata
SELECT * FROM metadata;

-- Capacity by cycle
SELECT cycle, 
       SUM(CASE WHEN current_a > 0 THEN step_ah ELSE 0 END) as charge_ah,
       SUM(CASE WHEN current_a < 0 THEN ABS(step_ah) ELSE 0 END) as discharge_ah
FROM data GROUP BY cycle;

-- Voltage vs time for cycle 1
SELECT step_time_s, voltage_v, current_a 
FROM data 
WHERE cycle = 1 
ORDER BY step_time_s;

-- Step duration analysis
SELECT cycle, step_type, MAX(step_time_s) as duration_s
FROM data 
GROUP BY cycle, step_type;
```