#!/usr/bin/env python3
"""
Battery Data Analysis Tool

This script demonstrates how to analyze battery test data from the SQLite databases
created by the minismush battery cycler.

Usage:
    python analyze_battery_data.py battery_test_*.db

Requirements:
    - Standard Python libraries (sqlite3, matplotlib, pandas optional)
"""

import sqlite3
import sys
import os
from datetime import datetime

def connect_database(db_path):
    """Connect to SQLite database and return connection"""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def print_test_metadata(conn):
    """Print test metadata in a formatted table"""
    print("📋 TEST METADATA")
    print("=" * 50)
    
    cursor = conn.execute("SELECT key, value FROM metadata ORDER BY key")
    
    for row in cursor:
        key = row['key'].replace('_', ' ').title()
        value = row['value']
        
        # Format specific fields
        if 'time' in row['key']:
            try:
                # Try to parse ISO timestamp
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                value = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                pass
        
        print(f"{key:20}: {value}")
    
    print()

def analyze_cycle_summary(conn):
    """Analyze and print cycle-by-cycle summary"""
    print("🔄 CYCLE SUMMARY")
    print("=" * 80)
    
    query = """
    SELECT 
        cycle,
        COUNT(*) as data_points,
        MIN(voltage_v) as min_voltage,
        MAX(voltage_v) as max_voltage,
        SUM(CASE WHEN current_a > 0 THEN step_ah ELSE 0 END) as charge_ah,
        SUM(CASE WHEN current_a < 0 THEN ABS(step_ah) ELSE 0 END) as discharge_ah,
        MAX(total_time_s) as cycle_end_time_s
    FROM data 
    GROUP BY cycle 
    ORDER BY cycle
    """
    
    cursor = conn.execute(query)
    
    print(f"{'Cycle':<6} {'Points':<8} {'Min V':<7} {'Max V':<7} {'Charge':<9} {'Discharge':<10} {'Time (h)':<10}")
    print("-" * 80)
    
    for row in cursor:
        cycle = row['cycle']
        points = row['data_points']
        min_v = f"{row['min_voltage']:.3f}" if row['min_voltage'] else "N/A"
        max_v = f"{row['max_voltage']:.3f}" if row['max_voltage'] else "N/A"
        charge = f"{row['charge_ah']:.4f}" if row['charge_ah'] else "0.0000"
        discharge = f"{row['discharge_ah']:.4f}" if row['discharge_ah'] else "0.0000"
        time_h = f"{row['cycle_end_time_s']/3600:.2f}" if row['cycle_end_time_s'] else "N/A"
        
        print(f"{cycle:<6} {points:<8} {min_v:<7} {max_v:<7} {charge:<9} {discharge:<10} {time_h:<10}")
    
    print()

def analyze_step_breakdown(conn, cycle_num=1):
    """Analyze step breakdown for a specific cycle"""
    print(f"⚡ STEP BREAKDOWN - CYCLE {cycle_num}")
    print("=" * 70)
    
    query = """
    SELECT 
        step,
        step_type,
        COUNT(*) as data_points,
        MAX(step_time_s) as duration_s,
        MIN(voltage_v) as min_voltage,
        MAX(voltage_v) as max_voltage,
        AVG(current_a) as avg_current,
        MAX(step_ah) as total_ah
    FROM data 
    WHERE cycle = ?
    GROUP BY step, step_type
    ORDER BY step
    """
    
    cursor = conn.execute(query, (cycle_num,))
    
    print(f"{'Step':<5} {'Type':<5} {'Points':<8} {'Duration':<10} {'V Range':<12} {'Avg I (mA)':<12} {'Ah':<10}")
    print("-" * 70)
    
    for row in cursor:
        step = row['step']
        step_type = row['step_type'].upper()
        points = row['data_points']
        duration = f"{row['duration_s']:.0f}s" if row['duration_s'] else "N/A"
        v_range = f"{row['min_voltage']:.3f}-{row['max_voltage']:.3f}" if row['min_voltage'] and row['max_voltage'] else "N/A"
        avg_i_ma = f"{row['avg_current']*1000:.1f}" if row['avg_current'] else "N/A"
        ah = f"{row['total_ah']:.4f}" if row['total_ah'] else "N/A"
        
        print(f"{step:<5} {step_type:<5} {points:<8} {duration:<10} {v_range:<12} {avg_i_ma:<12} {ah:<10}")
    
    print()

def analyze_capacity_fade(conn):
    """Analyze capacity fade over cycles"""
    print("📉 CAPACITY FADE ANALYSIS")
    print("=" * 50)
    
    query = """
    SELECT 
        cycle,
        SUM(CASE WHEN current_a > 0 THEN step_ah ELSE 0 END) as charge_capacity,
        SUM(CASE WHEN current_a < 0 THEN ABS(step_ah) ELSE 0 END) as discharge_capacity
    FROM data 
    GROUP BY cycle 
    ORDER BY cycle
    """
    
    cursor = conn.execute(query)
    
    capacities = []
    for row in cursor:
        charge_cap = row['charge_capacity'] or 0
        discharge_cap = row['discharge_capacity'] or 0
        capacities.append({
            'cycle': row['cycle'],
            'charge': charge_cap,
            'discharge': discharge_cap
        })
    
    if len(capacities) > 1:
        initial_discharge = capacities[0]['discharge']
        if initial_discharge > 0:
            print(f"Initial discharge capacity: {initial_discharge:.4f} Ah")
            print(f"{'Cycle':<6} {'Discharge (Ah)':<15} {'Retention (%)':<15}")
            print("-" * 40)
            
            for cap in capacities:
                retention = (cap['discharge'] / initial_discharge) * 100 if initial_discharge > 0 else 0
                print(f"{cap['cycle']:<6} {cap['discharge']:<15.4f} {retention:<15.1f}")
        else:
            print("No discharge data found for capacity analysis")
    else:
        print("Not enough cycle data for capacity fade analysis")
    
    print()

def export_csv_summary(conn, output_file):
    """Export cycle summary to CSV"""
    query = """
    SELECT 
        cycle,
        SUM(CASE WHEN current_a > 0 THEN step_ah ELSE 0 END) as charge_ah,
        SUM(CASE WHEN current_a < 0 THEN ABS(step_ah) ELSE 0 END) as discharge_ah,
        MAX(total_time_s) as total_time_s,
        AVG(voltage_v) as avg_voltage,
        MIN(voltage_v) as min_voltage,
        MAX(voltage_v) as max_voltage
    FROM data 
    GROUP BY cycle 
    ORDER BY cycle
    """
    
    cursor = conn.execute(query)
    
    with open(output_file, 'w') as f:
        f.write("cycle,charge_ah,discharge_ah,total_time_s,avg_voltage,min_voltage,max_voltage\n")
        for row in cursor:
            f.write(f"{row['cycle']},{row['charge_ah']},{row['discharge_ah']},{row['total_time_s']},{row['avg_voltage']},{row['min_voltage']},{row['max_voltage']}\n")
    
    print(f"📊 Cycle summary exported to: {output_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_battery_data.py <database_file.db>")
        print("\nExample:")
        print("  python analyze_battery_data.py battery_test_2024-01-15T10-30-45-123Z.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print(f"🔋 Battery Data Analysis")
    print(f"Database: {db_path}")
    print("=" * 60)
    
    conn = connect_database(db_path)
    if not conn:
        sys.exit(1)
    
    try:
        # Print test metadata
        print_test_metadata(conn)
        
        # Analyze cycle summary
        analyze_cycle_summary(conn)
        
        # Analyze first cycle in detail
        analyze_step_breakdown(conn, cycle_num=1)
        
        # Capacity fade analysis
        analyze_capacity_fade(conn)
        
        # Export summary
        csv_output = db_path.replace('.db', '_summary.csv')
        export_csv_summary(conn, csv_output)
        
    except sqlite3.Error as e:
        print(f"❌ Database query error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()