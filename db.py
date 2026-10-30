"""
SkyFlow ATCMS - Database Connectivity and Operations Module
Supports both PostgreSQL (production) and SQLite (demonstration/offline fallback)
Provides transactional integrity, safety trigger enforcement, and Member 3 queries.
"""

import os
import sqlite3
from datetime import datetime
import pandas as pd

# Optional psycopg2 import
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skyflow.db")
DATABASE_URL = os.environ.get("DATABASE_URL", None)


def is_postgres():
    """Determine if a valid PostgreSQL connection should be used."""
    return bool(DATABASE_URL and PSYCOPG2_AVAILABLE)


def get_connection():
    """Establish and return database connection."""
    if is_postgres():
        conn = psycopg2.connect(DATABASE_URL)
        return conn, "postgres"
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        # Enable foreign key support in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn, "sqlite"


def init_database():
    """Initialize database tables, constraints, triggers, and seed data."""
    conn, engine = get_connection()
    cur = conn.cursor()

    if engine == "postgres":
        # Run PostgreSQL schema and seed if tables don't exist
        schema_file = os.path.join(os.path.dirname(__file__), "schema_and_seed.sql")
        if os.path.exists(schema_file):
            with open(schema_file, "r") as f:
                cur.execute(f.read())
            conn.commit()
        conn.close()
        return

    # SQLite Setup (matching PostgreSQL schema and triggers 1-to-1)
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS AIRPORT (
        airport_code VARCHAR(4) PRIMARY KEY,
        airport_name VARCHAR(100) NOT NULL,
        city VARCHAR(50) NOT NULL,
        country VARCHAR(50) NOT NULL DEFAULT 'India',
        latitude DECIMAL(9, 6) NOT NULL,
        longitude DECIMAL(9, 6) NOT NULL,
        elevation_ft INT CHECK (elevation_ft >= -1500 AND elevation_ft <= 15000)
    );

    CREATE TABLE IF NOT EXISTS AIRLINE (
        airline_id INTEGER PRIMARY KEY AUTOINCREMENT,
        airline_name VARCHAR(100) NOT NULL UNIQUE,
        callsign_prefix VARCHAR(10) NOT NULL UNIQUE,
        country_of_origin VARCHAR(50) NOT NULL,
        contact_email VARCHAR(100) NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS AIRCRAFT (
        aircraft_reg_no VARCHAR(12) PRIMARY KEY,
        model VARCHAR(50) NOT NULL,
        manufacturer VARCHAR(50) NOT NULL,
        passenger_capacity INT NOT NULL CHECK (passenger_capacity > 0),
        max_altitude_ft INT NOT NULL CHECK (max_altitude_ft > 0),
        cruising_speed_knots INT NOT NULL CHECK (cruising_speed_knots > 0),
        airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS RUNWAY (
        runway_id INTEGER PRIMARY KEY AUTOINCREMENT,
        airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
        runway_designator VARCHAR(10) NOT NULL,
        length_meters INT NOT NULL CHECK (length_meters >= 1000),
        surface_type VARCHAR(30) NOT NULL DEFAULT 'ASPHALT',
        current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
            CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED')),
        UNIQUE (airport_code, runway_designator)
    );

    CREATE TABLE IF NOT EXISTS GATE (
        gate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
        terminal_number VARCHAR(10) NOT NULL,
        gate_number VARCHAR(10) NOT NULL,
        gate_category VARCHAR(20) NOT NULL DEFAULT 'DOMESTIC'
            CHECK (gate_category IN ('DOMESTIC', 'INTERNATIONAL')),
        current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
            CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
        UNIQUE (airport_code, terminal_number, gate_number)
    );

    -- Member 3 Owned Tables:
    CREATE TABLE IF NOT EXISTS AIRSPACE_SECTOR (
        sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sector_name VARCHAR(50) NOT NULL UNIQUE,
        floor_altitude_ft INT NOT NULL CHECK (floor_altitude_ft >= 0),
        ceiling_altitude_ft INT NOT NULL CHECK (ceiling_altitude_ft > floor_altitude_ft),
        max_capacity INT NOT NULL CHECK (max_capacity > 0)
    );

    CREATE TABLE IF NOT EXISTS CONTROLLER (
        controller_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        license_number VARCHAR(30) NOT NULL UNIQUE,
        certification_level VARCHAR(20) NOT NULL 
            CHECK (certification_level IN ('GROUND', 'TOWER', 'APPROACH', 'EN_ROUTE')),
        shift_start TIME NOT NULL,
        shift_end TIME NOT NULL,
        assigned_sector_id INT REFERENCES AIRSPACE_SECTOR(sector_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS FLIGHT (
        flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_number VARCHAR(10) NOT NULL,
        flight_date DATE NOT NULL,
        airline_id INT NOT NULL REFERENCES AIRLINE(airline_id),
        aircraft_reg_no VARCHAR(12) NOT NULL REFERENCES AIRCRAFT(aircraft_reg_no),
        origin_airport VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code),
        dest_airport VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code),
        scheduled_departure TIMESTAMP NOT NULL,
        scheduled_arrival TIMESTAMP NOT NULL,
        actual_departure TIMESTAMP,
        actual_arrival TIMESTAMP,
        current_status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
            CHECK (current_status IN ('SCHEDULED', 'BOARDING', 'TAXIING', 'AIRBORNE', 'LANDED', 'DIVERTED', 'CANCELLED')),
        UNIQUE (flight_number, flight_date),
        CHECK (origin_airport <> dest_airport),
        CHECK (scheduled_arrival > scheduled_departure)
    );

    CREATE TABLE IF NOT EXISTS GATE_ASSIGNMENT (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
        gate_id INT NOT NULL REFERENCES GATE(gate_id) ON DELETE CASCADE,
        assigned_from TIMESTAMP NOT NULL,
        assigned_until TIMESTAMP NOT NULL,
        assignment_type VARCHAR(10) NOT NULL CHECK (assignment_type IN ('ARRIVAL', 'DEPARTURE')),
        CHECK (assigned_until > assigned_from)
    );

    CREATE TABLE IF NOT EXISTS FLIGHT_CLEARANCE (
        clearance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
        controller_id INT NOT NULL REFERENCES CONTROLLER(controller_id),
        runway_id INT REFERENCES RUNWAY(runway_id),
        clearance_type VARCHAR(30) NOT NULL 
            CHECK (clearance_type IN ('PUSHBACK', 'TAXI', 'TAKEOFF', 'ALTITUDE_CHANGE', 'HEADING', 'LANDING')),
        issued_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        assigned_altitude_ft INT CHECK (assigned_altitude_ft >= 0 AND assigned_altitude_ft <= 60000),
        assigned_heading_deg INT CHECK (assigned_heading_deg >= 0 AND assigned_heading_deg <= 360)
    );

    CREATE TABLE IF NOT EXISTS INCIDENT_LOG (
        incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INT REFERENCES FLIGHT(flight_id) ON DELETE SET NULL,
        reported_by INT NOT NULL REFERENCES CONTROLLER(controller_id),
        incident_type VARCHAR(30) NOT NULL 
            CHECK (incident_type IN ('NEAR_MISS', 'RUNWAY_INCURSION', 'ALTITUDE_BUST', 'BIRD_STRIKE', 'WEATHER_DIVERT')),
        severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        incident_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        description TEXT NOT NULL
    );

    -- Safety Triggers in SQLite:
    DROP TRIGGER IF EXISTS trg_runway_clearance_safety_abort;
    CREATE TRIGGER trg_runway_clearance_safety_abort
    BEFORE INSERT ON FLIGHT_CLEARANCE
    WHEN NEW.runway_id IS NOT NULL AND NEW.clearance_type IN ('TAKEOFF', 'LANDING')
    BEGIN
        SELECT CASE 
            WHEN (SELECT current_status FROM RUNWAY WHERE runway_id = NEW.runway_id) != 'AVAILABLE' THEN
                RAISE(ABORT, 'Runway Safety Violation: Runway is currently OCCUPIED or CLOSED!')
        END;
    END;

    DROP TRIGGER IF EXISTS trg_runway_clearance_occupy;
    CREATE TRIGGER trg_runway_clearance_occupy
    AFTER INSERT ON FLIGHT_CLEARANCE
    WHEN NEW.runway_id IS NOT NULL AND NEW.clearance_type IN ('TAKEOFF', 'LANDING')
    BEGIN
        UPDATE RUNWAY SET current_status = 'OCCUPIED' WHERE runway_id = NEW.runway_id;
    END;

    DROP TRIGGER IF EXISTS trg_flight_status_takeoff;
    CREATE TRIGGER trg_flight_status_takeoff
    AFTER INSERT ON FLIGHT_CLEARANCE
    WHEN NEW.clearance_type = 'TAKEOFF'
    BEGIN
        UPDATE FLIGHT 
        SET current_status = 'AIRBORNE',
            actual_departure = COALESCE(actual_departure, CURRENT_TIMESTAMP)
        WHERE flight_id = NEW.flight_id;
    END;

    DROP TRIGGER IF EXISTS trg_flight_status_landing;
    CREATE TRIGGER trg_flight_status_landing
    AFTER INSERT ON FLIGHT_CLEARANCE
    WHEN NEW.clearance_type = 'LANDING'
    BEGIN
        UPDATE FLIGHT 
        SET current_status = 'LANDED',
            actual_arrival = CURRENT_TIMESTAMP
        WHERE flight_id = NEW.flight_id;
    END;
    """)

    # Populate seed data if empty
    cur.execute("SELECT COUNT(*) FROM AIRPORT;")
    if cur.fetchone()[0] == 0:
        _populate_seed_data(cur)

    conn.commit()
    conn.close()


def _populate_seed_data(cur):
    """Seed base Indian aviation data matching schema_and_seed.sql."""
    # Airports
    airports = [
        ('DEL', 'Indira Gandhi International Airport', 'New Delhi', 'India', 28.556200, 77.100000, 777),
        ('BOM', 'Chhatrapati Shivaji Maharaj Int Airport', 'Mumbai', 'India', 19.089600, 72.865600, 39),
        ('BLR', 'Kempegowda International Airport', 'Bengaluru', 'India', 13.198600, 77.706600, 3000),
        ('MAA', 'Chennai International Airport', 'Chennai', 'India', 12.994100, 80.170900, 52),
        ('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad', 'India', 17.240300, 78.429400, 2024),
        ('CCU', 'Netaji Subhash Chandra Bose Int Airport', 'Kolkata', 'India', 22.654700, 88.446700, 16)
    ]
    cur.executemany("INSERT INTO AIRPORT VALUES (?,?,?,?,?,?,?);", airports)

    # Airlines
    airlines = [
        (1, 'IndiGo', 'IGO', 'India', 'operations@goindigo.in'),
        (2, 'Air India', 'AIC', 'India', 'dispatch@airindia.com'),
        (3, 'SpiceJet', 'SEJ', 'India', 'ops@spicejet.com'),
        (4, 'Akasa Air', 'AKJ', 'India', 'atc@akasaair.com')
    ]
    cur.executemany("INSERT INTO AIRLINE VALUES (?,?,?,?,?);", airlines)

    # Aircraft Fleet
    aircraft = [
        ('VT-ISN', 'A320neo', 'Airbus', 186, 39000, 450, 1),
        ('VT-IFP', 'A321neo', 'Airbus', 222, 39000, 460, 1),
        ('VT-EXF', 'B787-8 Dreamliner', 'Boeing', 256, 43000, 490, 2),
        ('VT-CIO', 'A320neo', 'Airbus', 180, 39000, 450, 2),
        ('VT-SLA', 'B737-800', 'Boeing', 189, 41000, 455, 3),
        ('VT-YAA', 'B737-MAX8', 'Boeing', 189, 41000, 460, 4)
    ]
    cur.executemany("INSERT INTO AIRCRAFT VALUES (?,?,?,?,?,?,?);", aircraft)

    # Runways
    runways = [
        (1, 'DEL', '09/27', 3810, 'ASPHALT', 'AVAILABLE'),
        (2, 'DEL', '10/28', 3810, 'ASPHALT', 'AVAILABLE'),
        (3, 'DEL', '11/29', 4430, 'ASPHALT', 'AVAILABLE'),
        (4, 'BOM', '09/27', 3445, 'ASPHALT', 'AVAILABLE'),
        (5, 'BOM', '14/32', 2925, 'ASPHALT', 'AVAILABLE'),
        (6, 'MAA', '07/25', 3658, 'ASPHALT', 'AVAILABLE'),
        (7, 'BLR', '09L/27R', 4000, 'ASPHALT', 'AVAILABLE')
    ]
    cur.executemany("INSERT INTO RUNWAY VALUES (?,?,?,?,?,?);", runways)

    # Gates
    gates = [
        (1, 'DEL', 'T3', '01A', 'DOMESTIC', 'AVAILABLE'),
        (2, 'DEL', 'T3', '02B', 'DOMESTIC', 'AVAILABLE'),
        (3, 'DEL', 'T3', '14A', 'INTERNATIONAL', 'AVAILABLE'),
        (4, 'BOM', 'T2', '45', 'DOMESTIC', 'AVAILABLE'),
        (5, 'MAA', 'T1', '04', 'DOMESTIC', 'AVAILABLE'),
        (6, 'BLR', 'T1', '08', 'DOMESTIC', 'AVAILABLE')
    ]
    cur.executemany("INSERT INTO GATE VALUES (?,?,?,?,?,?);", gates)

    # Airspace Sectors
    sectors = [
        (1, 'Delhi FIR - North (VIDF-N)', 0, 46000, 60),
        (2, 'Mumbai FIR - West (VABF)', 0, 46000, 55),
        (3, 'Chennai FIR - South (VOMF)', 0, 46000, 50),
        (4, 'Kolkata FIR - East (VECF)', 0, 46000, 45),
        (5, 'Delhi TMA (DEL-TMA)', 0, 15000, 30)
    ]
    cur.executemany("INSERT INTO AIRSPACE_SECTOR VALUES (?,?,?,?,?);", sectors)

    # Controllers
    controllers = [
        (1, 'Vikram', 'Rathore', 'AAI-ATCO-1092', 'TOWER', '06:00:00', '14:00:00', 1),
        (2, 'Ananya', 'Sharma', 'AAI-ATCO-2234', 'EN_ROUTE', '06:00:00', '14:00:00', 1),
        (3, 'Karthik', 'Ramanathan', 'AAI-ATCO-3310', 'TOWER', '14:00:00', '22:00:00', 3),
        (4, 'Siddharth', 'Nair', 'AAI-ATCO-4491', 'APPROACH', '14:00:00', '22:00:00', 3),
        (5, 'Neha', 'Deshmukh', 'AAI-ATCO-5582', 'TOWER', '06:00:00', '14:00:00', 2),
        (6, 'Rajesh', 'Verma', 'AAI-ATCO-6719', 'GROUND', '06:00:00', '14:00:00', 1),
        (7, 'Pooja', 'Menon', 'AAI-ATCO-7840', 'EN_ROUTE', '14:00:00', '22:00:00', 2)
    ]
    cur.executemany("INSERT INTO CONTROLLER VALUES (?,?,?,?,?,?,?,?);", controllers)

    # Flights
    today = datetime.now().strftime("%Y-%m-%d")
    flights = [
        (1, '6E-204', today, 1, 'VT-ISN', 'DEL', 'MAA', f"{today} 07:00:00", f"{today} 09:45:00", f"{today} 07:05:00", None, 'AIRBORNE'),
        (2, 'AI-101', today, 2, 'VT-EXF', 'BOM', 'DEL', f"{today} 08:30:00", f"{today} 10:40:00", None, None, 'BOARDING'),
        (3, '6E-532', today, 1, 'VT-IFP', 'BLR', 'DEL', f"{today} 09:15:00", f"{today} 12:00:00", None, None, 'SCHEDULED'),
        (4, 'QP-1102', today, 4, 'VT-YAA', 'BOM', 'BLR', f"{today} 10:00:00", f"{today} 11:45:00", None, None, 'SCHEDULED'),
        (5, 'SG-8169', today, 3, 'VT-SLA', 'DEL', 'CCU', f"{today} 11:00:00", f"{today} 13:10:00", None, None, 'SCHEDULED')
    ]
    cur.executemany("INSERT INTO FLIGHT VALUES (?,?,?,?,?,?,?,?,?,?,?,?);", flights)

    # Initial Clearances
    clearances = [
        (1, 1, 6, None, 'PUSHBACK', f"{today} 06:45:00", None, None),
        (2, 1, 6, None, 'TAXI', f"{today} 06:55:00", None, None),
        (3, 1, 1, 1, 'TAKEOFF', f"{today} 07:05:00", 5000, 90),
        (4, 1, 2, None, 'ALTITUDE_CHANGE', f"{today} 07:20:00", 36000, 175),
        (5, 1, 2, None, 'HEADING', f"{today} 07:35:00", 36000, 180),
        (6, 2, 5, None, 'PUSHBACK', f"{today} 08:15:00", None, None),
        (7, 2, 5, None, 'TAXI', f"{today} 08:22:00", None, None)
    ]
    cur.executemany("INSERT INTO FLIGHT_CLEARANCE VALUES (?,?,?,?,?,?,?,?);", clearances)

    # Set runway 1 to OCCUPIED as per the takeoff clearance
    cur.execute("UPDATE RUNWAY SET current_status = 'OCCUPIED' WHERE runway_id = 1;")

    # Initial Incidents
    incidents = [
        (1, 1, 2, 'ALTITUDE_BUST', 'MEDIUM', f"{today} 07:25:00", 'Aircraft climbed 400 ft above FL360 due to turbulence over Bhopal sector.'),
        (2, None, 1, 'BIRD_STRIKE', 'LOW', f"{today} 05:40:00", 'Patrol bird scaring team deployed at threshold of Runway 10/28 DEL.'),
        (3, 2, 5, 'RUNWAY_INCURSION', 'HIGH', f"{today} 08:25:00", 'Tug vehicle crossed intermediate holding point near taxiway Mike.')
    ]
    cur.executemany("INSERT INTO INCIDENT_LOG VALUES (?,?,?,?,?,?,?);", incidents)


# ----------------------------------------------------------------------------
# Member 3 Operations API
# ----------------------------------------------------------------------------

def get_active_flights():
    """Retrieve all flights that can receive clearances."""
    conn, _ = get_connection()
    query = """
    SELECT 
        f.flight_id, 
        f.flight_number, 
        f.origin_airport, 
        f.dest_airport, 
        f.current_status,
        al.airline_name, 
        f.aircraft_reg_no
    FROM FLIGHT f
    JOIN AIRLINE al ON f.airline_id = al.airline_id
    WHERE f.current_status NOT IN ('LANDED', 'CANCELLED')
    ORDER BY f.flight_id;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_all_flights():
    """Retrieve all flights for dropdown selections."""
    conn, _ = get_connection()
    query = """
    SELECT 
        f.flight_id, 
        f.flight_number, 
        f.origin_airport, 
        f.dest_airport, 
        f.current_status,
        al.airline_name
    FROM FLIGHT f
    JOIN AIRLINE al ON f.airline_id = al.airline_id
    ORDER BY f.flight_id DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_controllers():
    """Retrieve list of licensed controllers."""
    conn, _ = get_connection()
    query = """
    SELECT 
        c.controller_id, 
        c.first_name || ' ' || c.last_name AS full_name,
        c.license_number,
        c.certification_level,
        c.shift_start || ' - ' || c.shift_end AS shift_hours,
        sec.sector_name
    FROM CONTROLLER c
    LEFT JOIN AIRSPACE_SECTOR sec ON c.assigned_sector_id = sec.sector_id
    ORDER BY c.certification_level, c.last_name;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_runways(airport_code=None):
    """Retrieve runways with status."""
    conn, _ = get_connection()
    if airport_code:
        query = "SELECT * FROM RUNWAY WHERE airport_code = ? ORDER BY runway_designator;"
        df = pd.read_sql_query(query, conn, params=[airport_code])
    else:
        query = "SELECT * FROM RUNWAY ORDER BY airport_code, runway_designator;"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def set_runway_status(runway_id, new_status):
    """Update runway status (e.g. mark AVAILABLE or OCCUPIED)."""
    conn, _ = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE RUNWAY SET current_status = ? WHERE runway_id = ?;", (new_status, runway_id))
    conn.commit()
    conn.close()


def issue_clearance(flight_id, controller_id, clearance_type, runway_id=None, altitude=None, heading=None):
    """
    Issue an ATC clearance with transactional safety.
    Triggers runway safety check and raises error if runway is occupied/closed.
    """
    conn, _ = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO FLIGHT_CLEARANCE (
                flight_id, controller_id, runway_id, clearance_type, 
                issued_timestamp, assigned_altitude_ft, assigned_heading_deg
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?);
        """, (flight_id, controller_id, runway_id, clearance_type, altitude, heading))
        
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return True, f"Clearance #{last_id} issued successfully ({clearance_type})."
    except Exception as e:
        conn.rollback()
        conn.close()
        err_msg = str(e)
        if "Runway Safety Violation" in err_msg or "ABORT" in err_msg:
            return False, f"⚠️ SAFETY INTERLOCK TRIGGERED: Runway is currently OCCUPIED or CLOSED! Clearance rejected to prevent runway incursion."
        return False, f"Database Error: {err_msg}"


def file_incident(flight_id, reported_by, incident_type, severity, description):
    """File a safety incident report into INCIDENT_LOG."""
    conn, _ = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO INCIDENT_LOG (
                flight_id, reported_by, incident_type, severity, incident_time, description
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?);
        """, (flight_id if flight_id else None, reported_by, incident_type, severity, description))
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return True, f"Incident Report #{last_id} filed successfully under Severity {severity}."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Failed to log incident: {str(e)}"


def get_recent_clearances(limit=20):
    """Retrieve the live black-box clearance audit trail."""
    conn, _ = get_connection()
    query = f"""
    SELECT 
        fc.clearance_id,
        fc.issued_timestamp,
        f.flight_number,
        al.callsign_prefix,
        fc.clearance_type,
        r.airport_code || ' ' || r.runway_designator AS runway,
        fc.assigned_altitude_ft,
        fc.assigned_heading_deg,
        c.first_name || ' ' || c.last_name AS controller,
        c.certification_level
    FROM FLIGHT_CLEARANCE fc
    JOIN FLIGHT f ON fc.flight_id = f.flight_id
    JOIN AIRLINE al ON f.airline_id = al.airline_id
    JOIN CONTROLLER c ON fc.controller_id = c.controller_id
    LEFT JOIN RUNWAY r ON fc.runway_id = r.runway_id
    ORDER BY fc.issued_timestamp DESC
    LIMIT {limit};
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_incident_logs():
    """Retrieve safety incident reports."""
    conn, _ = get_connection()
    query = """
    SELECT 
        inc.incident_id,
        inc.incident_time,
        inc.incident_type,
        inc.severity,
        COALESCE(f.flight_number, 'Ground / Airport Wide') AS flight_number,
        c.first_name || ' ' || c.last_name AS reported_by_controller,
        c.certification_level,
        inc.description
    FROM INCIDENT_LOG inc
    JOIN CONTROLLER c ON inc.reported_by = c.controller_id
    LEFT JOIN FLIGHT f ON inc.flight_id = f.flight_id
    ORDER BY inc.incident_time DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_controller_workload():
    """Demonstrates Query 2: Aggregate Analysis with GROUP BY & HAVING."""
    conn, _ = get_connection()
    query = """
    SELECT 
        c.controller_id,
        c.first_name || ' ' || c.last_name AS controller_name,
        c.license_number,
        c.certification_level,
        COALESCE(sec.sector_name, 'Surface / Ground') AS sector_name,
        COUNT(fc.clearance_id) AS total_clearances_issued,
        COUNT(DISTINCT fc.flight_id) AS distinct_aircraft_handled
    FROM CONTROLLER c
    LEFT JOIN FLIGHT_CLEARANCE fc ON c.controller_id = fc.controller_id
    LEFT JOIN AIRSPACE_SECTOR sec ON c.assigned_sector_id = sec.sector_id
    GROUP BY c.controller_id, c.first_name, c.last_name, c.license_number, c.certification_level, sec.sector_name
    HAVING COUNT(fc.clearance_id) > 0
    ORDER BY total_clearances_issued DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_airborne_radar_flights():
    """Demonstrates Query 1: Multi-Table Join with Dynamic Clearance Subquery."""
    conn, _ = get_connection()
    query = """
    SELECT 
        f.flight_id,
        f.flight_number,
        al.airline_name,
        al.callsign_prefix,
        f.aircraft_reg_no,
        ac.model AS aircraft_model,
        f.origin_airport || ' -> ' || f.dest_airport AS route,
        f.actual_departure,
        fc.clearance_type AS latest_instruction,
        fc.assigned_altitude_ft,
        fc.assigned_heading_deg,
        fc.issued_timestamp AS clearance_time,
        c.first_name || ' ' || c.last_name AS authorizing_controller
    FROM FLIGHT f
    JOIN AIRLINE al ON f.airline_id = al.airline_id
    JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
    JOIN FLIGHT_CLEARANCE fc ON f.flight_id = fc.flight_id
    JOIN CONTROLLER c ON fc.controller_id = c.controller_id
    WHERE f.current_status = 'AIRBORNE'
      AND fc.clearance_id = (
          SELECT MAX(sub_fc.clearance_id)
          FROM FLIGHT_CLEARANCE sub_fc
          WHERE sub_fc.flight_id = f.flight_id
      )
    ORDER BY fc.issued_timestamp DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_sector_utilization():
    """Demonstrates Query 4: Airspace Sector Capacity and Controller Count."""
    conn, _ = get_connection()
    query = """
    SELECT 
        sec.sector_id,
        sec.sector_name,
        sec.floor_altitude_ft,
        sec.ceiling_altitude_ft,
        sec.max_capacity,
        COUNT(DISTINCT c.controller_id) AS active_controllers_assigned
    FROM AIRSPACE_SECTOR sec
    LEFT JOIN CONTROLLER c ON sec.sector_id = c.assigned_sector_id
    GROUP BY sec.sector_id, sec.sector_name, sec.floor_altitude_ft, sec.ceiling_altitude_ft, sec.max_capacity
    ORDER BY sec.sector_id ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
