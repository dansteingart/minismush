/* 
minimush: an minismu to http proxy driven by ghetto get calls (ht )
requirements 
   -- serialport -> npm install serialport
   -- express -> npm install express
   -- sleep -> npm install sleep
   -- socket.io -> npm install socket.io
   -- cors -> npm install cors

to start: node nodeforwader.js [HTTP PORT] [SERIAL PORT] [BAUD] [BUFFER LENGTH]
to read: http://[yourip]:[spec'd port]/read/  -> returns the last [BUFFER LENGTH] bytes from the serial port as a string
to write: http://[yourip]:[spec'd port]/write/[YOUR STRING HERE]

what will probably create farts/list of things to deal with later if I need to:
- returning characters that html has issues with
- spaces in the url

TODO as of 2021-10-16:

[x] Update Parser and buffer handling
[x] POST calls
[x] check working with python-socketio (big yes!)
[ ] Add parsing options to inteface?


*/

parts = process.argv

if (parts.length < 2)
{
	console.log("usage: node nodeforwader.js [HTTP PORT] [SERIAL PORT (optional)] [BAUD (optional)] [BUFFER LENGTH (optional)]")
	process.exit(1);
}

else
{
	console.log(parts);
	hp = parts[2]
	try{sp = parts[3]}             catch(e){sp = undefined} 
	try{baud = parseInt(parts[4])} catch(e){baud = undefined}
	try{blen = parseInt(parts[5])} catch(e){blen = 10000}
}


var bodyParser = require('body-parser');
var express = require('express')
var app = express();
var fs = require('fs');
var cors = require('cors')
const server = require('http').createServer(app);
var io = require('socket.io')(server,{cors:{methods: ["GET", "POST"]}});

const SerialPort = require('serialport');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const sqlite3 = require('sqlite3').verbose();

server.listen(hp);

function msleep(n) {
	Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, n);
  }
  function sleep(n) {
	msleep(n*1000);
  }

  var lh = 0;



  let serialPort;
  let currentPath = '/dev/tty-usbserial1'; // Default path
  
  function initializeSerialPort(path,baud) {
	  if (serialPort && serialPort.isOpen) {
		  console.log('Closing current serial port...');
		  serialPort.close((err) => {
			  if (err) {
				  console.error('Error closing serial port:', err.message);
			  } else {
				  console.log('Serial port closed successfully.');
				  createNewPort(path,baud);
			  }
		  });
	  } else {
		  createNewPort(path,baud);
	  }
  }
  
  function parseSMUStream(s)
  {
    p = s.split(",");
    out = {}
    out['channel']   = parseInt(p[0])
    //out['time_ms']   = parseInt(p[1])
    out['time_ms']   = Date.now()
    out['voltage_V'] = parseFloat(p[2])
    out['current_A'] = -parseFloat(p[3].replace("e-0","e-"))
    return out

  }

  function createNewPort(path,baud) {
	  console.log(`Initializing serial port with path: ${path}`);
	  serialPort = new SerialPort(path, { baudRate: baud });
  
	  // Attach event listeners
	  serialPort.on('open', () => {
		  console.log('Serial port opened:', path);
	  });
  
		//last heard
		serialPort.on('data', function(data) {
		
		
		buf += data.toString('binary') 
		lh = new Date().getTime()
		if (buf.length > blen) buf = buf.substr(buf.length-blen,buf.length) 
		io.emit('data', data.toString('utf8'));
		
		// Handle logging if active
		if (loggingState.isLogging) {
			const dataString = data.toString('utf8').trim();
			if (dataString) {
				handleDataLogging(dataString);
			}
		}
		
    //Parsing last line
    const lines = buf.split('\n');
    const lastLine = lines[lines.length - 2].trim();
    console.log(lastLine)
    if (lastLine.search("1,") == 0)      {ch1.push(parseSMUStream(lastLine)); io.emit('ch1',parseSMUStream(lastLine));}
    else if (lastLine.search("2,") == 0) {ch2.push(parseSMUStream(lastLine)); io.emit('ch2',parseSMUStream(lastLine))}
    else                                 {otm.push(lastLine);                io.emit('otm',lastLine)}

    //FIFO on blen
    if (ch1.length > blen) ch1.shift();
    if (ch2.length > blen) ch2.shift();
    if (otm.length > blen) otm.shift();


		// Handle cycler data processing if cycler is running
		if (cyclerState.isRunning && !cyclerState.isPaused) {
			const dataString = data.toString('utf8').trim();
			if (dataString) { parseCyclerStreamingData(dataString);
			}
		}
		
		});
  
	  serialPort.on('error', (err) => {
		  console.error('Serial port error:', err.message);
	  });
  
	  serialPort.on('close', () => {
		  console.log('Serial port closed');
	  });
  
	  currentPath = path; // Update the current path
  }
  
  // API to change the path dynamically
  function changeSerialPortPath(newPath) {
	  console.log(`Changing serial port path from ${currentPath} to ${newPath}`);
	  initializeSerialPort(newPath);
  }
  


if (sp != undefined) initializeSerialPort(sp,baud)

//On Data fill a circular buf of the specified length
buf = ""
ch1 = []
ch2 = []
otm = []

// Logging state management
let loggingState = {
  isLogging: false,
  type: null, // 'csv' or 'sqlite'
  filename: null,
  tableName: null,
  columns: [],
  schemaDetected: false,
  csvWriter: null,
  db: null,
  insertStmt: null
};

// Helper function to detect schema from first data row
function detectSchema(dataString) {
  try {
    const data = JSON.parse(dataString);
    if (Array.isArray(data)) {
      return data.map((_, index) => `col_${String(index + 1).padStart(2, '0')}`);
    } else if (typeof data === 'object') {
      return Object.keys(data);
    }
  } catch (e) {
    // If not JSON, try to split by common delimiters
    const parts = dataString.trim().split(/[,\t|;]/);
    return parts.map((_, index) => `col_${String(index + 1).padStart(2, '0')}`);
  }
  return ['col_01']; // Fallback for single value
}

// Helper function to parse incoming data into object
function parseDataToObject(dataString, columns) {
  try {
    const data = JSON.parse(dataString);
    if (Array.isArray(data)) {
      const obj = {};
      data.forEach((value, index) => {
        if (index < columns.length) {
          obj[columns[index]] = value;
        }
      });
      return obj;
    } else if (typeof data === 'object') {
      return data;
    }
  } catch (e) {
    // If not JSON, try to split by common delimiters
    const parts = dataString.trim().split(/[,\t|;]/);
    const obj = {};
    parts.forEach((value, index) => {
      if (index < columns.length) {
        obj[columns[index]] = value.trim();
      }
    });
    return obj;
  }
  // Single value fallback
  return { [columns[0]]: dataString.trim() };
}

// Handle data logging to CSV or SQLite
function handleDataLogging(dataString) {
  try {
    // Clean up the data string - remove line breaks and extra whitespace
    const cleanedData = dataString.replace(/[\r\n]+/g, '').trim();
    
    // Skip empty or invalid data
    if (!cleanedData) return;
    
    // Detect schema from first data row if not already detected
    if (!loggingState.schemaDetected) {
      if (loggingState.columns.length === 0) {
        loggingState.columns = detectSchema(cleanedData);
      }
      
      if (loggingState.type === 'csv') {
        initializeCsvLogging();
      } else if (loggingState.type === 'sqlite') {
        initializeSqliteLogging();
      }
      
      loggingState.schemaDetected = true;
    }
    
    // Parse data and log it
    const dataObj = parseDataToObject(cleanedData, loggingState.columns);
    
    if (loggingState.type === 'csv' && loggingState.csvWriter) {
      loggingState.csvWriter.writeRecords([dataObj]).catch(err => {
        console.error('CSV write error:', err);
      });
    } else if (loggingState.type === 'sqlite' && loggingState.insertStmt) {
      const values = loggingState.columns.map(col => dataObj[col] || null);
      loggingState.insertStmt.run(values, (err) => {
        if (err) console.error('SQLite insert error:', err);
      });
    }
  } catch (error) {
    console.error('Data logging error:', error);
  }
}

// Initialize CSV logging
function initializeCsvLogging() {
  const csvHeaders = loggingState.columns.map(col => ({ id: col, title: col }));
  
  loggingState.csvWriter = createCsvWriter({
    path: loggingState.filename,
    header: csvHeaders,
    append: fs.existsSync(loggingState.filename)
  });
}

// Initialize SQLite logging
function initializeSqliteLogging() {
  loggingState.db = new sqlite3.Database(loggingState.filename);
  
  // Create table if it doesn't exist
  const columnDefs = loggingState.columns.map(col => `${col} TEXT`).join(', ');
  const createTableQuery = `CREATE TABLE IF NOT EXISTS ${loggingState.tableName} (${columnDefs})`;
  
  loggingState.db.run(createTableQuery, (err) => {
    if (err) {
      console.error('SQLite table creation error:', err);
      return;
    }
    
    // Prepare insert statement
    const placeholders = loggingState.columns.map(() => '?').join(', ');
    const insertQuery = `INSERT INTO ${loggingState.tableName} (${loggingState.columns.join(', ')}) VALUES (${placeholders})`;
    
    loggingState.insertStmt = loggingState.db.prepare(insertQuery);
  });
}


//Enable Cross Site Scripting
app.use(cors())
app.use('/static',express.static(__dirname + '/static'))

//Allows us to rip out data
app.use(bodyParser.urlencoded({extended:true})); //post forms
app.use(bodyParser.json()) // json forms (e.g. axios)
app.use(express.json());
app.use(express.urlencoded({ extended: true })); // For URL-encoded data, if necessary

//Write to serial port
app.get('/write/*',function(req,res){	
	toSend = req.originalUrl.replace("/write/","")
	toSend = decodeURIComponent(toSend);
	console.log(toSend)
	writeout(toSend)
	res.send(toSend)
});

massage = undefined

  // Attempt to reconnect the serial port
app.get('/reconnect', async (req, res) => {initializeSerialPort(sp,baud); res.send("foo") });

app.get('/disconnect', async (req, res) => {try{serialPort.close()} catch(e){console.log(e)}; res.send("foo")});

app.post('/reconnect',async (req, res) => {x=req.body;initializeSerialPort(x['sp'],parseInt(['baud'])); res.send("foo") })
  
app.get("/list_ports", async(req,res)=>{res.send(await SerialPort.list())});

app.get('/writecf/*',function(req,res){	
	toSend = req.originalUrl.replace("/writecf/","")
	toSend = decodeURIComponent(toSend);
	console.log(toSend)
	writeout(toSend,le="\r\n")
	res.send(toSend)
});

//#expects data to be in {'payload':data} format
app.post('/write',function(req,res){    
	x = req.body
	toSend = x['payload']
	console.log(toSend)
	writeout(toSend)
	res.send(toSend)
});


app.get("/connect",(req,res)=>{

	res.sendFile(__dirname + '/connect.html');

})

//Show Last Updated
app.get('/lastread/',function(req,res){	
	lhs = lh.toString();
	console.log(lhs)
	res.send(lhs)
});


//read buffer
app.get('/read/', function(req, res){
	res.send(buf)
});


//default interface
app.get('/', function(req, res){ res.sendFile(__dirname + '/console.html'); });
app.get('/console', function(req, res){ res.sendFile(__dirname + '/console.html'); });

//virtual front panel
app.get('/vfp', function(req, res){ res.sendFile(__dirname + '/vfp.html'); });


// Start CSV logging
app.post('/start_csv_log', function(req, res) {
  try {
    const { filename, columns } = req.body;
    
    if (!filename) {
      return res.status(400).json({ error: 'Filename is required' });
    }
    
    // Stop any current logging
    stopLogging();
    
    // Initialize CSV logging state
    loggingState.isLogging = true;
    loggingState.type = 'csv';
    loggingState.filename = filename;
    loggingState.columns = columns || [];
    loggingState.schemaDetected = false;
    loggingState.csvWriter = null;
    
    console.log(`Started CSV logging to: ${filename}`);
    res.json({ 
      success: true, 
      message: `CSV logging started to ${filename}`,
      columns: loggingState.columns 
    });
  } catch (error) {
    console.error('Error starting CSV logging:', error);
    res.status(500).json({ error: 'Failed to start CSV logging' });
  }
});

// Start SQLite logging
app.post('/start_sqlite_log', function(req, res) {
  try {
    const { filename, table, columns } = req.body;
    
    if (!filename || !table) {
      return res.status(400).json({ error: 'Filename and table name are required' });
    }
    
    // Stop any current logging
    stopLogging();
    
    // Initialize SQLite logging state
    loggingState.isLogging = true;
    loggingState.type = 'sqlite';
    loggingState.filename = filename;
    loggingState.tableName = table;
    loggingState.columns = columns || [];
    loggingState.schemaDetected = false;
    loggingState.db = null;
    loggingState.insertStmt = null;
    
    console.log(`Started SQLite logging to: ${filename}, table: ${table}`);
    res.json({ 
      success: true, 
      message: `SQLite logging started to ${filename}, table: ${table}`,
      columns: loggingState.columns 
    });
  } catch (error) {
    console.error('Error starting SQLite logging:', error);
    res.status(500).json({ error: 'Failed to start SQLite logging' });
  }
});

// Stop logging
app.post('/stop_log', function(req, res) {
  try {
    stopLogging();
    res.json({ success: true, message: 'Logging stopped' });
  } catch (error) {
    console.error('Error stopping logging:', error);
    res.status(500).json({ error: 'Failed to stop logging' });
  }
});

// Get logging status
app.get('/log_status', function(req, res) {
  res.json({
    isLogging: loggingState.isLogging,
    type: loggingState.type,
    filename: loggingState.filename,
    tableName: loggingState.tableName,
    columns: loggingState.columns,
    schemaDetected: loggingState.schemaDetected
  });
});

// Helper function to stop logging and clean up resources
function stopLogging() {
  if (loggingState.insertStmt) {
    loggingState.insertStmt.finalize();
    loggingState.insertStmt = null;
  }
  
  if (loggingState.db) {
    loggingState.db.close();
    loggingState.db = null;
  }
  
  loggingState.isLogging = false;
  loggingState.type = null;
  loggingState.filename = null;
  loggingState.tableName = null;
  loggingState.columns = [];
  loggingState.schemaDetected = false;
  loggingState.csvWriter = null;
  
  console.log('Logging stopped and resources cleaned up');
}

//sockets
io.on('connection', function(socket){
  io.emit('data',buf)
  socket.on('input', function(msg){
   //console.log('message: ' + msg);
	writeout(msg,le="\r\n")
	
  });
});

// Enhanced socket handling for cycler streaming data
io.on('connection', function(socket){
  // WebSocket connection established
});

// Parse streaming data from serial buffer for battery cycler
function parseCyclerStreamingData(dataString) {
  if (!cyclerState.isRunning || cyclerState.isPaused) return;
  
  try {
    // Filter out non-measurement data
    // Skip timestamps (contain : or large numbers like unix timestamps)
    if (dataString.includes(':') || /^\d{10,}$/.test(dataString.trim())) {
      return; // Skip timestamp data
    }
    
    // Skip command responses and status messages
    if (dataString.includes('OK') || dataString.includes('ERROR') || 
        dataString.includes('MEAS') || dataString.includes('SOUR') ||
        dataString.includes('OUTP') || dataString.length > 50) {
      return; // Skip command acknowledgments and long messages
    }
    
    let voltage = null;
    let current = null;
    
    // Check if data looks like voltage,current format (e.g., "3.345,0.0123" or "3.836209,9.659207e-10")
    if (dataString.includes(',')) {
      const parts = dataString.split(',');
      if (parts.length === 2) {
        const v = parseFloat(parts[0].trim());
        const i = parseFloat(parts[1].trim());
        
        // Validate reasonable ranges for battery measurements
        if (!isNaN(v) && !isNaN(i) && 
            Math.abs(v) >= 0.1 && Math.abs(v) <= 50 && // Voltage range 0.1V to 50V
            Math.abs(i) <= 100) { // Current range up to 100A
          voltage = v;
          current = i;
        }
      }
    }
    // Check if data looks like a single voltage value (for OCV/REST)
    else {
      const v = parseFloat(dataString.trim());
      if (!isNaN(v) && v >= 0.1 && v <= 50) { // Reasonable voltage range for batteries
        voltage = v;
        current = 0; // Assume zero current for voltage-only measurements
      }
    }
    
    // If we got valid measurement data, process it
    if (voltage !== null) {
      // Store the latest streaming data
      cyclerState.lastStreamingData = {
        voltage: voltage,
        current: current,
        timestamp: Date.now()
      };
      
      console.log(`Cycler measurement: ${voltage.toFixed(6)}V, ${current.toExponential(6)}A`);
      
      // Process the data for logging and cutoff checking
      processCyclerData(voltage, current);
    }
    
  } catch (error) {
    // Ignore parsing errors - not all serial data is measurement data
    console.log(`Skipping unparseable data: "${dataString}"`);
  }
}


// Process cycler data from streaming
function processCyclerData(voltage, current) {
  const now = Date.now();
  const stepTime = (now - cyclerState.stepStartTime) / 1000;
  const totalTime = (now - cyclerState.startTime) / 1000;
  
  // Update Ah integration
  updateAhIntegration(current, now);
  
  // Create data point
  const dataPoint = {
    timestamp: new Date().toISOString(),
    cycle: cyclerState.currentCycle,
    step: cyclerState.currentStepIndex,
    step_type: cyclerState.currentStep ? cyclerState.currentStep.mode : 'unknown',
    step_time: stepTime,
    total_time: totalTime,
    voltage: voltage,
    current: current,
    step_ah: cyclerState.stepAh,
    cycle_ah: cyclerState.cycleAh,
    total_ah: cyclerState.totalAh
  };
  
  cyclerState.stepData.push(dataPoint);
  
  // Write to SQLite database if logging enabled
  if (cyclerState.cyclerDataStmt) {
    try {
      cyclerState.cyclerDataStmt.run(
        dataPoint.timestamp,
        now,
        dataPoint.cycle,
        dataPoint.step,
        dataPoint.step_type,
        dataPoint.step_time,
        dataPoint.total_time,
        dataPoint.voltage,
        dataPoint.current,
        dataPoint.step_ah,
        dataPoint.cycle_ah,
        dataPoint.total_ah,
        null, // temperature_c
        null  // notes
      );
    } catch (err) {
      console.error('Cycler SQLite write error:', err);
    }
  }
  
  // Also write to CSV for compatibility
  if (cyclerState.cyclerCsvWriter) {
    cyclerState.cyclerCsvWriter.writeRecords([dataPoint]).catch(err => {
      console.error('Cycler CSV write error:', err);
    });
  }
  
  // Emit real-time data
  io.emit('cycler_data', dataPoint);
  
  // Check cutoff conditions
  if (cyclerState.currentStep && checkStepCutoffs(voltage, current, stepTime)) {
    advanceToNextStep();
  }
}


//smu helpder functions
function writeout(s,le="\r\n")
{
  //console.log(`[SERIAL OUT] ${s}`);
  serialPort.write(s+le);
}


// SMU State Management
const smuState = {
  channels: {
    1: {
      potential: 0,
      current: 0,
      enabled: false,
      streaming: false,
      sampleRate: 1000,
      mode: null // 'FVMI' for voltage control, 'FIMV' for current control
    },
    2: {
      potential: 0,
      current: 0,
      enabled: false,
      streaming: false,
      sampleRate: 1000,
      mode: null
    }
  },
  ledBrightness: 50,
  identity: null,
  temperatures: null
};

smu_mode = undefined;
function response(res) { 
  setTimeout(()=>{
    ress = buf.split("\n").slice(-2)[0]
    res.send({'result':ress})
  },200);
}

function get_identity(){ writeout("*IDN?") }

app.get('/smu/get_identity', (req,res)=>
  {
     get_identity();
     response(res);
  });

function set_mode(ch,mode) {
  writeout(`SOUR${ch}:${mode} ENA`);
  smuState.channels[ch].mode = mode;
}

function set_current(ch,cur)
{
  if (smuState.channels[ch].mode !=  "FIMV") set_mode(ch,'FIMV');
  writeout(`SOUR${ch}:CURR ${cur}`);
  smuState.channels[ch].current = cur;
}

function set_potential(ch,pot)
{
  if (smuState.channels[ch].mode !=  "FVMI") set_mode(ch,'FVMI');
  writeout(`SOUR${ch}:VOLT ${pot}`);
  smuState.channels[ch].potential = pot;
}

// Measurement Functions
function measure_voltage(ch) { writeout(`MEAS${ch}:VOLT?`) }
function measure_current(ch) { writeout(`MEAS${ch}:CURR?`) }
function measure_voltage_and_current(ch) { writeout(`MEAS${ch}:VOLT:CURR?`) }

// Channel Control Functions
function enable_channel(ch) { 
  writeout(`OUTP${ch} ON`); 
  smuState.channels[ch].enabled = true;
}
function disable_channel(ch) { 
  writeout(`OUTP${ch} OFF`);
  smuState.channels[ch].enabled = false;
}
function set_voltage_range(ch, range) { writeout(`SOUR${ch}:VOLT:RANGE ${range}`) }
function reset_device() { 
  writeout("*RST");
  // Reset state
  Object.keys(smuState.channels).forEach(ch => {
    smuState.channels[ch] = {
      potential: 0,
      current: 0,
      enabled: false,
      streaming: false,
      sampleRate: 1000,
      mode: null
    };
  });
}

// Data Streaming Functions
function start_streaming(ch) { 
  writeout(`SOUR${ch}:DATA:STREAM ON`);
  smuState.channels[ch].streaming = true;
}
function stop_streaming(ch) { 
  writeout(`SOUR${ch}:DATA:STREAM OFF`);
  smuState.channels[ch].streaming = false;
}
function set_sample_rate(ch, rate) { 
  writeout(`SOUR${ch}:DATA:SRATE ${rate}`);
  smuState.channels[ch].sampleRate = rate;
}

// System Functions
function set_led_brightness(brightness) { 
  writeout(`SYST:LED ${brightness}`);
  smuState.ledBrightness = brightness;
}
function get_led_brightness() { writeout("SYST:LED?") }
function get_temperatures() { writeout("SYST:TEMP?") }
function set_time(timestamp) { writeout(`SYST:TIME ${timestamp}`) }

// WiFi Functions
function wifi_scan() { writeout("SYST:WIFI:SCAN?") }
function get_wifi_status() { writeout("SYST:WIFI?") }
function set_wifi_credentials(ssid, password) { 
  writeout(`SYST:WIFI:SSID "${ssid}"`)
  writeout(`SYST:WIFI:PASS "${password}"`)
}
function enable_wifi() { writeout("SYST:WIFI ENA") }
function disable_wifi() { writeout("SYST:WIFI DIS") }

app.post("/smu/set_potential",(req,res) => {
  try {
    const { channel, potential } = req.body;
    
    if (channel === undefined || potential === undefined) {
      return res.status(400).json({ error: 'Channel and potential are required' });
    }
    
    set_potential(channel, potential);
    response(res);
  } catch (error) {
    console.error('Error setting potential:', error);
    res.status(500).json({ error: 'Failed to set potential' });
  }
})

app.post("/smu/set_current",(req,res) => {
  try {
    const { channel, current } = req.body;
    
    if (channel === undefined || current === undefined) {
      return res.status(400).json({ error: 'Channel and current are required' });
    }
    
    set_current(channel, current);
    response(res);
  } catch (error) {
    console.error('Error setting current:', error);
    res.status(500).json({ error: 'Failed to set current' });
  }
})

app.post("/smu/set_mode",(req,res) => {
  try {
    const { channel, mode } = req.body;
    
    if (channel === undefined || mode === undefined) {
      return res.status(400).json({ error: 'Channel and mode are required' });
    }
    
    if (mode !== 'FVMI' && mode !== 'FIMV') {
      return res.status(400).json({ error: 'Mode must be FVMI or FIMV' });
    }
    
    set_mode(channel, mode);
    response(res);
  } catch (error) {
    console.error('Error setting mode:', error);
    res.status(500).json({ error: 'Failed to set mode' });
  }
})

// Measurement Routes
app.post("/smu/measure_voltage", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    measure_voltage(channel);
    response(res);
  } catch (error) {
    console.error('Error measuring voltage:', error);
    res.status(500).json({ error: 'Failed to measure voltage' });
  }
})

app.post("/smu/measure_current", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    measure_current(channel);
    response(res);
  } catch (error) {
    console.error('Error measuring current:', error);
    res.status(500).json({ error: 'Failed to measure current' });
  }
})

app.post("/smu/measure_voltage_and_current", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    measure_voltage_and_current(channel);
    response(res);
  } catch (error) {
    console.error('Error measuring voltage and current:', error);
    res.status(500).json({ error: 'Failed to measure voltage and current' });
  }
})

// Channel Control Routes
app.post("/smu/enable_channel", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    enable_channel(channel);
    response(res);
  } catch (error) {
    console.error('Error enabling channel:', error);
    res.status(500).json({ error: 'Failed to enable channel' });
  }
})

app.post("/smu/disable_channel", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    disable_channel(channel);
    response(res);
  } catch (error) {
    console.error('Error disabling channel:', error);
    res.status(500).json({ error: 'Failed to disable channel' });
  }
})

app.post("/smu/set_voltage_range", (req,res) => {
  try {
    const { channel, range } = req.body;
    if (channel === undefined || range === undefined) {
      return res.status(400).json({ error: 'Channel and range are required' });
    }
    if (!['AUTO', 'LOW', 'HIGH'].includes(range)) {
      return res.status(400).json({ error: 'Range must be AUTO, LOW, or HIGH' });
    }
    set_voltage_range(channel, range);
    response(res);
  } catch (error) {
    console.error('Error setting voltage range:', error);
    res.status(500).json({ error: 'Failed to set voltage range' });
  }
})

app.post("/smu/reset", (req,res) => {
  try {
    reset_device();
    response(res);
  } catch (error) {
    console.error('Error resetting device:', error);
    res.status(500).json({ error: 'Failed to reset device' });
  }
})

// Data Streaming Routes
app.post("/smu/start_streaming", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    start_streaming(channel);
    response(res);
  } catch (error) {
    console.error('Error starting streaming:', error);
    res.status(500).json({ error: 'Failed to start streaming' });
  }
})

app.post("/smu/stop_streaming", (req,res) => {
  try {
    const { channel } = req.body;
    if (channel === undefined) {
      return res.status(400).json({ error: 'Channel is required' });
    }
    stop_streaming(channel);
    response(res);
  } catch (error) {
    console.error('Error stopping streaming:', error);
    res.status(500).json({ error: 'Failed to stop streaming' });
  }
})

app.post("/smu/set_sample_rate", (req,res) => {
  try {
    const { channel, rate } = req.body;
    if (channel === undefined || rate === undefined) {
      return res.status(400).json({ error: 'Channel and rate are required' });
    }
    set_sample_rate(channel, rate);
    response(res);
  } catch (error) {
    console.error('Error setting sample rate:', error);
    res.status(500).json({ error: 'Failed to set sample rate' });
  }
})

// System Routes
app.post("/smu/set_led_brightness", (req,res) => {
  try {
    const { brightness } = req.body;
    if (brightness === undefined) {
      return res.status(400).json({ error: 'Brightness is required' });
    }
    if (brightness < 0 || brightness > 100) {
      return res.status(400).json({ error: 'Brightness must be between 0 and 100' });
    }
    set_led_brightness(brightness);
    response(res);
  } catch (error) {
    console.error('Error setting LED brightness:', error);
    res.status(500).json({ error: 'Failed to set LED brightness' });
  }
})

app.get("/smu/get_led_brightness", (req,res) => {
  try {
    get_led_brightness();
    response(res);
  } catch (error) {
    console.error('Error getting LED brightness:', error);
    res.status(500).json({ error: 'Failed to get LED brightness' });
  }
})

app.get("/smu/get_temperatures", (req,res) => {
  try {
    get_temperatures();
    response(res);
  } catch (error) {
    console.error('Error getting temperatures:', error);
    res.status(500).json({ error: 'Failed to get temperatures' });
  }
})

app.post("/smu/set_time", (req,res) => {
  try {
    const { timestamp } = req.body;
    if (timestamp === undefined) {
      return res.status(400).json({ error: 'Timestamp is required' });
    }
    set_time(timestamp);
    response(res);
  } catch (error) {
    console.error('Error setting time:', error);
    res.status(500).json({ error: 'Failed to set time' });
  }
})

// WiFi Routes
app.get("/smu/wifi_scan", (req,res) => {
  try {
    wifi_scan();
    response(res);
  } catch (error) {
    console.error('Error scanning WiFi:', error);
    res.status(500).json({ error: 'Failed to scan WiFi' });
  }
})

app.get("/smu/get_wifi_status", (req,res) => {
  try {
    get_wifi_status();
    response(res);
  } catch (error) {
    console.error('Error getting WiFi status:', error);
    res.status(500).json({ error: 'Failed to get WiFi status' });
  }
})

app.post("/smu/set_wifi_credentials", (req,res) => {
  try {
    const { ssid, password } = req.body;
    if (ssid === undefined || password === undefined) {
      return res.status(400).json({ error: 'SSID and password are required' });
    }
    set_wifi_credentials(ssid, password);
    response(res);
  } catch (error) {
    console.error('Error setting WiFi credentials:', error);
    res.status(500).json({ error: 'Failed to set WiFi credentials' });
  }
})

app.post("/smu/enable_wifi", (req,res) => {
  try {
    enable_wifi();
    response(res);
  } catch (error) {
    console.error('Error enabling WiFi:', error);
    res.status(500).json({ error: 'Failed to enable WiFi' });
  }
})

app.post("/smu/disable_wifi", (req,res) => {
  try {
    disable_wifi();
    response(res);
  } catch (error) {
    console.error('Error disabling WiFi:', error);
    res.status(500).json({ error: 'Failed to disable WiFi' });
  }
})

// SMU State Management Endpoints
app.get("/smu/state", (req,res) => {
  try {
    res.json(smuState);
  } catch (error) {
    console.error('Error getting SMU state:', error);
    res.status(500).json({ error: 'Failed to get SMU state' });
  }
})

// ============================================================================
// SMU DOCUMENTATION WEB INTERFACE
// ============================================================================

const marked = require('marked');
const path = require('path');

// SMU documentation page
app.get('/smu', (req, res) => {
  try {
    const markdownPath = path.join(__dirname, 'static', 'smu_documentation.md');
    const markdownContent = fs.readFileSync(markdownPath, 'utf8');
    
    // Configure marked options for better rendering
    marked.setOptions({
      breaks: true,
      gfm: true,
      tables: true,
      sanitize: false
    });
    
    const htmlContent = marked.parse(markdownContent);
    
    // Create a complete HTML page with styling
    const fullHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMU API Documentation - minismush</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 30px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 25px;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }
        pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }
        pre code {
            background: none;
            padding: 0;
            color: inherit;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .endpoint {
            background-color: #e8f5e8;
            padding: 10px;
            border-left: 4px solid #27ae60;
            margin: 10px 0;
        }
        .method {
            font-weight: bold;
            color: #e74c3c;
        }
        .nav {
            background-color: #34495e;
            padding: 15px;
            margin: -30px -30px 30px -30px;
            border-radius: 8px 8px 0 0;
        }
        .nav h1 {
            color: white;
            margin: 0;
            border: none;
            padding: 0;
        }
        .nav p {
            color: #bdc3c7;
            margin: 5px 0 0 0;
        }
        .back-link {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .back-link:hover {
            background-color: #2980b9;
        }
        ul li {
            margin: 8px 0;
        }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <h1>🔋 minismush SMU API</h1>
            <p>Complete API reference for Source Measure Unit control and battery cycling</p>
        </div>
        
        <a href="/" class="back-link">← Back to Console</a>
        
        ${htmlContent}
        
        <hr style="margin: 40px 0; border: none; border-top: 1px solid #ecf0f1;">
        <p style="text-align: center; color: #7f8c8d; font-size: 0.9em;">
            Generated from <code>static/smu_documentation.md</code> • 
            <a href="/console" style="color: #3498db;">Console Interface</a> • 
            <a href="/connect" style="color: #3498db;">Connection Manager</a>
        </p>
    </div>
</body>
</html>`;
    
    res.send(fullHtml);
    
  } catch (error) {
    console.error('Error rendering SMU documentation:', error);
    res.status(500).send(`
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h1>Error Loading Documentation</h1>
          <p>Could not load SMU API documentation. Error: ${error.message}</p>
          <p><a href="/">← Back to Console</a></p>
        </body>
      </html>
    `);
  }
});

// ============================================================================
// BATTERY CYCLER FUNCTIONALITY
// ============================================================================

// Battery Cycler State Management
let cyclerState = {
  isRunning: false,
  isPaused: false,
  channel: null,
  steps: [],
  currentStepIndex: 0,
  currentCycle: 0,
  totalCycles: 0,
  startTime: null,
  stepStartTime: null,
  lastMeasurementTime: null,
  
  // Integrators and counters
  totalAh: 0,           // Total Ah since start
  stepAh: 0,            // Ah for current step
  cycleAh: 0,           // Ah for current cycle
  lastCurrent: 0,       // Last measured current for integration
  
  // Current step data
  currentStep: null,
  stepData: [],         // Data points for current step
  
  // Logging
  cyclerLogFile: null,
  cyclerCsvFile: null,
  cyclerCsvWriter: null,
  cyclerDb: null,
  cyclerDataStmt: null,
  
  // Streaming data
  lastStreamingData: null
};

// Amp-hour integrator using trapezoidal rule
function updateAhIntegration(current, timestamp) {
  if (cyclerState.lastMeasurementTime === null) {
    cyclerState.lastMeasurementTime = timestamp;
    cyclerState.lastCurrent = current;
    return;
  }
  
  const deltaTimeHours = (timestamp - cyclerState.lastMeasurementTime) / (1000 * 3600);
  const avgCurrent = (current + cyclerState.lastCurrent) / 2;
  const deltaAh = avgCurrent * deltaTimeHours;
  
  cyclerState.totalAh += deltaAh;
  cyclerState.stepAh += deltaAh;
  cyclerState.cycleAh += deltaAh;
  
  cyclerState.lastMeasurementTime = timestamp;
  cyclerState.lastCurrent = current;
}

// Step validation and parsing
function validateCyclerSteps(steps) {
  if (!Array.isArray(steps)) {
    throw new Error('Steps must be an array');
  }
  
  let cycleStartFound = false;
  let cycleEndFound = false;
  
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    
    if (step.cycle === 'start') {
      cycleStartFound = true;
      continue;
    }
    
    if (step.cycle === 'end') {
      cycleEndFound = true;
      continue;
    }
    
    // Validate step modes
    if (!['cc', 'cv', 'ocv', 'rest'].includes(step.mode)) {
      throw new Error(`Invalid step mode: ${step.mode} at step ${i}`);
    }
    
    // Validate cutoff conditions
    if (step.mode === 'cc') {
      if (step.current === undefined) {
        throw new Error(`CC step missing current at step ${i}`);
      }
    }
    
    if (step.mode === 'cv') {
      if (step.voltage === undefined) {
        throw new Error(`CV step missing voltage at step ${i}`);
      }
    }
  }
  
  if (!cycleStartFound) {
    throw new Error('Cycle definition must include {"cycle":"start"}');
  }
  
  if (!cycleEndFound) {
    throw new Error('Cycle definition must include {"cycle":"end"}');
  }
  
  return true;
}

// Initialize cycler logging with SQLite database
function initializeCyclerLogging(testMetadata = {}) {
  if (cyclerState.cyclerLogFile) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const sqliteFilename = `battery_test_${timestamp}.db`;
    const csvFilename = `battery_test_${timestamp}.csv`;
    
    // Create SQLite database
    cyclerState.cyclerDb = new sqlite3.Database(sqliteFilename);
    
    // Use serialize to ensure tables are created before proceeding
    cyclerState.cyclerDb.serialize(() => {
      // Create metadata table
      cyclerState.cyclerDb.run(`
        CREATE TABLE IF NOT EXISTS metadata (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          key TEXT UNIQUE NOT NULL,
          value TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // Create data table
      cyclerState.cyclerDb.run(`
        CREATE TABLE IF NOT EXISTS data (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          timestamp DATETIME NOT NULL,
          unix_timestamp INTEGER NOT NULL,
          cycle INTEGER NOT NULL,
          step INTEGER NOT NULL,
          step_type TEXT NOT NULL,
          step_time_s REAL NOT NULL,
          total_time_s REAL NOT NULL,
          voltage_v REAL,
          current_a REAL,
          step_ah REAL NOT NULL,
          cycle_ah REAL NOT NULL,
          total_ah REAL NOT NULL,
          temperature_c REAL,
          notes TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // Insert test metadata (after tables are created)
      const defaultMetadata = {
        test_name: testMetadata.testName || 'Battery Cycling Test',
        test_type: testMetadata.testType || 'cycling',
        channel: cyclerState.channel.toString(),
        total_cycles: cyclerState.totalCycles.toString(),
        start_time: new Date().toISOString(),
        operator: testMetadata.operator || 'system',
        battery_id: testMetadata.batteryId || 'unknown',
        battery_type: testMetadata.batteryType || 'unknown',
        capacity_ah: testMetadata.capacityAh ? testMetadata.capacityAh.toString() : 'unknown',
        temperature_c: testMetadata.temperatureC ? testMetadata.temperatureC.toString() : 'ambient',
        notes: testMetadata.notes || '',
        step_definition: JSON.stringify(cyclerState.steps),
        software_version: 'minismush-1.0',
        data_format_version: '1.0'
      };
      
      // Insert metadata
      const metadataStmt = cyclerState.cyclerDb.prepare('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)');
      for (const [key, value] of Object.entries(defaultMetadata)) {
        metadataStmt.run(key, value);
      }
      metadataStmt.finalize();
      
      // Prepare data insert statement (after tables are created)
      cyclerState.cyclerDataStmt = cyclerState.cyclerDb.prepare(`
        INSERT INTO data (
          timestamp, unix_timestamp, cycle, step, step_type, step_time_s, total_time_s,
          voltage_v, current_a, step_ah, cycle_ah, total_ah, temperature_c, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
    });
    
    // Also maintain CSV logging for compatibility
    const csvHeaders = [
      { id: 'timestamp', title: 'Timestamp' },
      { id: 'cycle', title: 'Cycle' },
      { id: 'step', title: 'Step' },
      { id: 'step_type', title: 'Step_Type' },
      { id: 'step_time', title: 'Step_Time_s' },
      { id: 'total_time', title: 'Total_Time_s' },
      { id: 'voltage', title: 'Voltage_V' },
      { id: 'current', title: 'Current_A' },
      { id: 'step_ah', title: 'Step_Ah' },
      { id: 'cycle_ah', title: 'Cycle_Ah' },
      { id: 'total_ah', title: 'Total_Ah' }
    ];
    
    cyclerState.cyclerCsvWriter = createCsvWriter({
      path: csvFilename,
      header: csvHeaders,
      append: false
    });
    
    cyclerState.cyclerLogFile = sqliteFilename;
    cyclerState.cyclerCsvFile = csvFilename;
    
    console.log(`Battery test logging initialized:`);
    console.log(`  SQLite: ${sqliteFilename}`);
    console.log(`  CSV: ${csvFilename}`);
  }
}

// Determine the expected current direction for CV steps based on voltage and historical data
function determineCVDirection(stepVoltage, currentVoltage, initialCurrent) {
  // If we have an initial current measurement, use its sign as the primary indicator
  if (initialCurrent !== undefined && initialCurrent !== 0) {
    return Math.sign(initialCurrent);
  }
  
  // Otherwise, predict based on voltage difference
  // If step voltage > current voltage, expect positive current (charging)
  // If step voltage < current voltage, expect negative current (discharging)
  if (stepVoltage > currentVoltage) {
    return 1; // Charging (positive current expected)
  } else if (stepVoltage < currentVoltage) {
    return -1; // Discharging (negative current expected)
  }
  
  // If voltages are equal, assume maintenance (could be either direction)
  return 0;
}

// Check if current step cutoff conditions are met
function checkStepCutoffs(voltage, current, stepTime) {
  const step = cyclerState.currentStep;
  if (!step) return false;
  
  // Voltage cutoffs (same for all modes)
  if (step.cutoff_V !== undefined) {
    if (step.mode === 'cc') {
      // CC mode: directional voltage cutoffs
      if ((step.current > 0 && voltage >= step.cutoff_V) ||
          (step.current < 0 && voltage <= step.cutoff_V)) {
        console.log(`CC voltage cutoff reached: ${voltage}V (target: ${step.cutoff_V}V)`);
        return true;
      }
    } else if (step.mode === 'cv') {
      // CV mode: voltage should be held constant, cutoff_V acts as tolerance check
      if (Math.abs(voltage - step.voltage) > Math.abs(step.cutoff_V)) {
        console.log(`CV voltage tolerance exceeded: ${voltage}V (target: ${step.voltage}V, tolerance: ${step.cutoff_V}V)`);
        return true;
      }
    }
  }
  
  if (step.cutoff_V_min !== undefined && voltage <= step.cutoff_V_min) {
    console.log(`Minimum voltage cutoff reached: ${voltage}V (min: ${step.cutoff_V_min}V)`);
    return true;
  }
  
  if (step.cutoff_V_max !== undefined && voltage >= step.cutoff_V_max) {
    console.log(`Maximum voltage cutoff reached: ${voltage}V (max: ${step.cutoff_V_max}V)`);
    return true;
  }
  
  // Current cutoffs with directional logic
  if (step.cutoff_A !== undefined) {
    if (step.mode === 'cc') {
      // CC mode: simple absolute value check
      if (Math.abs(current) <= Math.abs(step.cutoff_A)) {
        console.log(`CC current cutoff reached: ${current}A (target: ${step.cutoff_A}A)`);
        return true;
      }
    } else if (step.mode === 'cv') {
      // CV mode: directional current cutoff
      // Determine expected current direction for this CV step
      const expectedDirection = determineCVDirection(step.voltage, voltage, cyclerState.stepData.length > 0 ? cyclerState.stepData[0].current : undefined);
      
      if (expectedDirection !== 0) {
        // Check if current has dropped below cutoff in the expected direction
        if (expectedDirection > 0) {
          // Charging CV: check if positive current dropped below positive cutoff
          if (step.cutoff_A > 0 && current <= step.cutoff_A && current >= 0) {
            console.log(`CV charging current cutoff reached: ${current}A (cutoff: ${step.cutoff_A}A, charging)`);
            return true;
          }
          // Or if current became negative (direction change)
          if (current < 0) {
            console.log(`CV charging direction change: ${current}A (was charging, now discharging)`);
            return true;
          }
        } else {
          // Discharging CV: check if negative current dropped below negative cutoff
          if (step.cutoff_A < 0 && current >= step.cutoff_A && current <= 0) {
            console.log(`CV discharging current cutoff reached: ${current}A (cutoff: ${step.cutoff_A}A, discharging)`);
            return true;
          }
          // Or if current became positive (direction change)
          if (current > 0) {
            console.log(`CV discharging direction change: ${current}A (was discharging, now charging)`);
            return true;
          }
        }
      } else {
        // Bidirectional or maintenance CV: check absolute value
        if (Math.abs(current) <= Math.abs(step.cutoff_A)) {
          console.log(`CV maintenance current cutoff reached: ${current}A (target: ${step.cutoff_A}A)`);
          return true;
        }
      }
    }
  }
  
  // Ah cutoffs with directional logic
  if (step.cutoff_Ah !== undefined) {
    if (step.mode === 'cc') {
      // CC mode: use absolute value for capacity-based cutoffs
      if (Math.abs(cyclerState.stepAh) >= Math.abs(step.cutoff_Ah)) {
        console.log(`CC capacity cutoff reached: ${cyclerState.stepAh}Ah (target: ${step.cutoff_Ah}Ah)`);
        return true;
      }
    } else if (step.mode === 'cv') {
      // CV mode: directional capacity cutoff
      const expectedDirection = determineCVDirection(step.voltage, voltage, cyclerState.stepData.length > 0 ? cyclerState.stepData[0].current : undefined);
      
      if (expectedDirection > 0) {
        // Charging CV: check positive Ah accumulation
        if (step.cutoff_Ah > 0 && cyclerState.stepAh >= step.cutoff_Ah) {
          console.log(`CV charging capacity cutoff reached: ${cyclerState.stepAh}Ah (target: ${step.cutoff_Ah}Ah)`);
          return true;
        }
      } else if (expectedDirection < 0) {
        // Discharging CV: check negative Ah accumulation
        if (step.cutoff_Ah < 0 && cyclerState.stepAh <= step.cutoff_Ah) {
          console.log(`CV discharging capacity cutoff reached: ${cyclerState.stepAh}Ah (target: ${step.cutoff_Ah}Ah)`);
          return true;
        }
      } else {
        // Bidirectional: use absolute value
        if (Math.abs(cyclerState.stepAh) >= Math.abs(step.cutoff_Ah)) {
          console.log(`CV bidirectional capacity cutoff reached: ${cyclerState.stepAh}Ah (target: ${step.cutoff_Ah}Ah)`);
          return true;
        }
      }
    }
  }
  
  // Time cutoffs (same for all modes)
  if (step.cutoff_time_s !== undefined && stepTime >= step.cutoff_time_s) {
    console.log(`Time cutoff reached: ${stepTime}s (target: ${step.cutoff_time_s}s)`);
    return true;
  }
  
  return false;
}

// Execute current step - simplified to only set SMU mode, measurements come from streaming
async function executeCurrentStep() {
  if (!cyclerState.isRunning || cyclerState.isPaused) {
    console.log(`Step execution skipped - running: ${cyclerState.isRunning}, paused: ${cyclerState.isPaused}`);
    return;
  }
  
  const step = cyclerState.currentStep;
  if (!step) {
    console.log(`No current step defined - currentStep:`, step);
    return;
  }
  
  console.log(`Setting SMU for step ${cyclerState.currentStepIndex}: ${step.mode}`);
  
  try {
    // Set SMU based on step mode - measurements will come from streaming
    switch (step.mode) {
      case 'cc':
        console.log(`Setting CC mode: ${step.current}A on channel ${cyclerState.channel}`);
        console.log(`Calling enable_channel(${cyclerState.channel})`);
        enable_channel(cyclerState.channel);
        console.log(`Calling set_current(${cyclerState.channel}, ${step.current})`);
        set_current(cyclerState.channel, step.current);
        console.log(`Channel ${cyclerState.channel} enabled for CC step - commands sent`);
        break;
        
      case 'cv':
        console.log(`Setting CV mode: ${step.voltage}V on channel ${cyclerState.channel}`);
        console.log(`Calling enable_channel(${cyclerState.channel})`);
        enable_channel(cyclerState.channel);
        console.log(`Calling set_potential(${cyclerState.channel}, ${step.voltage})`);
        set_potential(cyclerState.channel, step.voltage);
        console.log(`Channel ${cyclerState.channel} enabled for CV step - commands sent`);
        break;
        
      case 'ocv':
      case 'rest':
        console.log(`Setting ${step.mode.toUpperCase()} mode on channel ${cyclerState.channel}`);
        console.log(`Calling set_current(${cyclerState.channel}, 0) for ${step.mode}`);
        // For OCV/REST, set current to zero (high impedance) but keep channel enabled for voltage measurement
        set_current(cyclerState.channel, 0);
        console.log(`Calling enable_channel(${cyclerState.channel})`);
        enable_channel(cyclerState.channel);
        console.log(`Channel ${cyclerState.channel} enabled for ${step.mode.toUpperCase()} step - commands sent`);
        break;
        
      default:
        console.log(`Unknown step mode: ${step.mode}`);
        break;
    }
    
    
  } catch (error) {
    console.error('Step execution error:', error);
    stopCycler();
  }
}

// Advance to next step
function advanceToNextStep() {
  console.log(`Completing step ${cyclerState.currentStepIndex}: ${cyclerState.currentStep.mode}`);
  
  // Reset step counters
  cyclerState.stepAh = 0;
  cyclerState.stepStartTime = Date.now();
  cyclerState.stepData = [];
  
  // Find next step
  cyclerState.currentStepIndex++;
  
  while (cyclerState.currentStepIndex < cyclerState.steps.length) {
    const nextStep = cyclerState.steps[cyclerState.currentStepIndex];
    
    if (nextStep.cycle === 'end') {
      // End of cycle - check if we should repeat
      cyclerState.currentCycle++;
      console.log(`Cycle ${cyclerState.currentCycle} completed`);
      
      // Reset cycle counters
      cyclerState.cycleAh = 0;
      
      if (cyclerState.totalCycles === 0 || cyclerState.currentCycle < cyclerState.totalCycles) {
        // Start next cycle
        cyclerState.currentStepIndex = 0;
        while (cyclerState.currentStepIndex < cyclerState.steps.length && 
               cyclerState.steps[cyclerState.currentStepIndex].cycle !== 'start') {
          cyclerState.currentStepIndex++;
        }
        cyclerState.currentStepIndex++; // Move past cycle start
        continue;
      } else {
        // All cycles completed
        console.log('All cycles completed');
        stopCycler();
        return;
      }
    }
    
    if (nextStep.cycle === 'start') {
      cyclerState.currentStepIndex++;
      continue;
    }
    
    // Valid step found
    cyclerState.currentStep = nextStep;
    console.log(`Starting step ${cyclerState.currentStepIndex}: ${nextStep.mode}`);
    return;
  }
  
  // No more steps
  console.log('Cycler sequence completed');
  stopCycler();
}

// Start cycler
function startCycler(channel, steps, cycles = 0, enableLogging = true, testMetadata = {}) {
  if (cyclerState.isRunning) {
    throw new Error('Cycler is already running');
  }
  
  // Validate inputs
  validateCyclerSteps(steps);
  
  // Initialize state
  cyclerState.isRunning = true;
  cyclerState.isPaused = false;
  cyclerState.channel = channel;
  cyclerState.steps = steps;
  cyclerState.totalCycles = cycles;
  cyclerState.currentCycle = 1;
  cyclerState.currentStepIndex = 0;
  cyclerState.startTime = Date.now();
  cyclerState.stepStartTime = Date.now();
  cyclerState.lastMeasurementTime = null;
  
  // Reset counters
  cyclerState.totalAh = 0;
  cyclerState.stepAh = 0;
  cyclerState.cycleAh = 0;
  cyclerState.lastCurrent = 0;
  cyclerState.stepData = [];
  
  // Initialize logging
  if (enableLogging) {
    cyclerState.cyclerLogFile = true;
    initializeCyclerLogging(testMetadata);
  }
  
  // Find first actual step (skip cycle start)
  while (cyclerState.currentStepIndex < steps.length && 
         steps[cyclerState.currentStepIndex].cycle === 'start') {
    cyclerState.currentStepIndex++;
  }
  
  if (cyclerState.currentStepIndex >= steps.length) {
    throw new Error('No valid steps found in cycle definition');
  }
  
  cyclerState.currentStep = steps[cyclerState.currentStepIndex];
  
  console.log(`Cycler started on channel ${channel}, ${cycles || 'infinite'} cycles`);
  console.log(`Found ${steps.length} total steps`);
  console.log(`Starting at step index: ${cyclerState.currentStepIndex}`);
  console.log(`Current step:`, cyclerState.currentStep);
  console.log(`First step: ${cyclerState.currentStep ? cyclerState.currentStep.mode : 'UNDEFINED'}`);
  
  // Execute first step first to set up SMU mode
  executeCurrentStep();
  
  // Then start data streaming after SMU is configured
  setTimeout(() => {
    start_streaming(channel);
    console.log(`Started data streaming on channel ${channel}`);
  }, 1000);
}

// Pause cycler
function pauseCycler() {
  if (!cyclerState.isRunning) {
    throw new Error('Cycler is not running');
  }
  cyclerState.isPaused = true;
  console.log('Cycler paused');
}

// Resume cycler
function resumeCycler() {
  if (!cyclerState.isRunning || !cyclerState.isPaused) {
    throw new Error('Cycler is not paused');
  }
  cyclerState.isPaused = false;
  console.log('Cycler resumed');
}

// Stop cycler
function stopCycler() {
  
  // Stop data streaming
  if (cyclerState.channel) {
    try {
      stop_streaming(cyclerState.channel);
      console.log(`Stopped data streaming on channel ${cyclerState.channel}`);
      disable_channel(cyclerState.channel);
    } catch (error) {
      console.error('Error stopping streaming/disabling channel during cycler stop:', error);
    }
  }
  
  // Close database connections
  if (cyclerState.cyclerDataStmt) {
    cyclerState.cyclerDataStmt.finalize();
    cyclerState.cyclerDataStmt = null;
  }
  
  if (cyclerState.cyclerDb) {
    // Update metadata with end time and completion status
    try {
      cyclerState.cyclerDb.run('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
        'end_time', new Date().toISOString());
      cyclerState.cyclerDb.run('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
        'test_status', 'completed');
      cyclerState.cyclerDb.run('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
        'final_cycle_count', cyclerState.currentCycle.toString());
      cyclerState.cyclerDb.run('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
        'total_test_time_s', cyclerState.startTime ? ((Date.now() - cyclerState.startTime) / 1000).toString() : '0');
    } catch (error) {
      console.error('Error updating final metadata:', error);
    }
    
    cyclerState.cyclerDb.close();
    cyclerState.cyclerDb = null;
  }
  
  cyclerState.isRunning = false;
  cyclerState.isPaused = false;
  
  console.log('Cycler stopped and database closed');
  io.emit('cycler_status', { status: 'stopped' });
}

// Pause/Resume cycler
function pauseCycler() {
  cyclerState.isPaused = true;
  console.log('Cycler paused');
  io.emit('cycler_status', { status: 'paused' });
}

function resumeCycler() {
  cyclerState.isPaused = false;
  console.log('Cycler resumed');
  io.emit('cycler_status', { status: 'running' });
}

// ============================================================================
// BATTERY CYCLER REST API ENDPOINTS
// ============================================================================

// Start cycler
app.post('/cycler/start', (req, res) => {
  try {
    const { channel, steps, cycles, enableLogging, metadata } = req.body;
    
    if (!channel || !steps) {
      return res.status(400).json({ error: 'Channel and steps are required' });
    }
    
    startCycler(channel, steps, cycles || 0, enableLogging !== false, metadata || {});
    
    res.json({
      success: true,
      message: 'Cycler started successfully',
      channel: channel,
      totalSteps: steps.length,
      cycles: cycles || 'infinite'
    });
    
  } catch (error) {
    console.error('Error starting cycler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Stop cycler
app.post('/cycler/stop', (req, res) => {
  try {
    stopCycler();
    res.json({ success: true, message: 'Cycler stopped' });
  } catch (error) {
    console.error('Error stopping cycler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Pause cycler
app.post('/cycler/pause', (req, res) => {
  try {
    if (!cyclerState.isRunning) {
      return res.status(400).json({ error: 'Cycler is not running' });
    }
    pauseCycler();
    res.json({ success: true, message: 'Cycler paused' });
  } catch (error) {
    console.error('Error pausing cycler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Resume cycler
app.post('/cycler/resume', (req, res) => {
  try {
    if (!cyclerState.isRunning || !cyclerState.isPaused) {
      return res.status(400).json({ error: 'Cycler is not paused' });
    }
    resumeCycler();
    res.json({ success: true, message: 'Cycler resumed' });
  } catch (error) {
    console.error('Error resuming cycler:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get cycler status
app.get('/cycler/status', (req, res) => {
  try {
    const stepTime = cyclerState.stepStartTime ? 
      (Date.now() - cyclerState.stepStartTime) / 1000 : 0;
    const totalTime = cyclerState.startTime ? 
      (Date.now() - cyclerState.startTime) / 1000 : 0;
    
    res.json({
      isRunning: cyclerState.isRunning,
      isPaused: cyclerState.isPaused,
      channel: cyclerState.channel,
      currentCycle: cyclerState.currentCycle,
      totalCycles: cyclerState.totalCycles,
      currentStepIndex: cyclerState.currentStepIndex,
      currentStep: cyclerState.currentStep,
      stepTime: stepTime,
      totalTime: totalTime,
      totalAh: cyclerState.totalAh,
      stepAh: cyclerState.stepAh,
      cycleAh: cyclerState.cycleAh,
      logFile: cyclerState.cyclerLogFile,
      totalSteps: cyclerState.steps.length
    });
  } catch (error) {
    console.error('Error getting cycler status:', error);
    res.status(500).json({ error: error.message });
  }
});

// Validate step definition
app.post('/cycler/validate', (req, res) => {
  try {
    const { steps } = req.body;
    
    if (!steps) {
      return res.status(400).json({ error: 'Steps array is required' });
    }
    
    validateCyclerSteps(steps);
    
    res.json({
      success: true,
      message: 'Step definition is valid',
      totalSteps: steps.length
    });
    
  } catch (error) {
    console.error('Step validation error:', error);
    res.status(400).json({ error: error.message });
  }
});

console.log('Battery cycler functionality loaded successfully');