"""
SkyFlow ATCMS - Database Operations & Connection Manager (db.py)
Domain: Commercial Fleet & Flight Operations (Member 2 Subsystem)

Features:
- Dual Engine Support: PostgreSQL (via psycopg2/SQLAlchemy if available) or
  standalone zero-dependency SQLite (skyflow_atc.db).
- Automatic Schema Migration & Indian Aviation Dataset Seeding.
- Thread-safe parameterized query execution with full transaction rollback.
- Complete Member 2 CRUD API: Flight dispatch, status transition, delay calculation,
  OTP metrics, route density, and fleet capacity reports.
"""

import os
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skyflow_atc.db")
PG_URL = os.environ.get("DATABASE_URL") or os.environ.get("PG_CONNECTION_STRING")

# Detect PostgreSQL or SQLite mode
USE_POSTGRES = False
pg_module = None

if PG_URL:
    try:
        import psycopg2
        import psycopg2.extras
        pg_module = psycopg2
        USE_POSTGRES = True
    except ImportError:
        USE_POSTGRES = False


def get_connection():
    """Returns a connection to the active database (PostgreSQL or SQLite)."""
    if USE_POSTGRES and pg_module:
        conn = pg_module.connect(PG_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


def init_database(force_reseed: bool = False):
    """
    Initializes database tables, views, and seeds baseline Indian aviation records
    if tables do not exist or force_reseed is True.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if not USE_POSTGRES:
            # Check if FLIGHT table already exists in SQLite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FLIGHT';")
            exists = cursor.fetchone()

            if not exists or force_reseed:
                # Execute full schema and seed in SQLite
                cursor.executescript(_SQLITE_SCHEMA_AND_SEED)
                conn.commit()
        else:
            # For PostgreSQL, tables are created via schema_and_seed.sql
            pass
    finally:
        cursor.close()
        conn.close()


# ----------------------------------------------------------------------------
# MEMBER 2 DATA ACCESS API (CRUD & ANALYTICAL OPERATIONS)
# ----------------------------------------------------------------------------

def get_database_status() -> Dict[str, Any]:
    """Returns system status, engine type, and entity counts."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        counts = {}
        for table in ["AIRPORT", "AIRLINE", "AIRCRAFT", "FLIGHT", "RUNWAY", "GATE", "AIRSPACE_SECTOR", "CONTROLLER"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row = cursor.fetchone()
                counts[table] = row[0]
            except Exception:
                counts[table] = 0

        return {
            "engine": "PostgreSQL" if USE_POSTGRES else "SQLite (Built-in / Local Zero-Config)",
            "db_path": PG_URL if USE_POSTGRES else DB_PATH,
            "connected": True,
            "counts": counts
        }
    finally:
        cursor.close()
        conn.close()


def get_airlines() -> List[Dict[str, Any]]:
    """Retrieves all registered operating carriers."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT airline_id, airline_name, callsign_prefix, country_of_origin, contact_email FROM AIRLINE ORDER BY airline_name ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_aircraft(airline_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves aircraft, optionally filtered by operating airline."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if airline_id:
            cursor.execute("""
                SELECT ac.*, al.airline_name, al.callsign_prefix
                FROM AIRCRAFT ac
                JOIN AIRLINE al ON ac.airline_id = al.airline_id
                WHERE ac.airline_id = ?
                ORDER BY ac.aircraft_reg_no ASC
            """ if not USE_POSTGRES else """
                SELECT ac.*, al.airline_name, al.callsign_prefix
                FROM AIRCRAFT ac
                JOIN AIRLINE al ON ac.airline_id = al.airline_id
                WHERE ac.airline_id = %s
                ORDER BY ac.aircraft_reg_no ASC
            """, (airline_id,))
        else:
            cursor.execute("""
                SELECT ac.*, al.airline_name, al.callsign_prefix
                FROM AIRCRAFT ac
                JOIN AIRLINE al ON ac.airline_id = al.airline_id
                ORDER BY al.airline_name, ac.aircraft_reg_no ASC
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_airports() -> List[Dict[str, Any]]:
    """Retrieves all 12 Indian master hubs."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT airport_code, airport_name, city, country, latitude, longitude, elevation_ft FROM AIRPORT ORDER BY city ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_flights(
    search: Optional[str] = None,
    status: Optional[str] = None,
    origin: Optional[str] = None,
    dest: Optional[str] = None,
    airline_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Searches and retrieves flights with full relational joins,
    supporting multi-criteria filtering.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # SQLite / Postgres dialect query
        sql = """
            SELECT 
                f.flight_id,
                f.flight_number,
                f.flight_date,
                al.airline_id,
                al.airline_name,
                al.callsign_prefix,
                f.aircraft_reg_no,
                ac.model AS aircraft_model,
                ac.passenger_capacity,
                f.origin_airport,
                orig.city AS origin_city,
                orig.airport_name AS origin_airport_name,
                f.dest_airport,
                dest.city AS dest_city,
                dest.airport_name AS dest_airport_name,
                f.scheduled_departure,
                f.scheduled_arrival,
                f.actual_departure,
                f.actual_arrival,
                f.current_status,
                CASE 
                    WHEN f.actual_departure IS NOT NULL AND f.actual_departure > f.scheduled_departure THEN
                        ROUND((strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) / 60)
                    ELSE 0
                END AS departure_delay_minutes
            FROM FLIGHT f
            JOIN AIRLINE al ON f.airline_id = al.airline_id
            JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
            JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
            JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
            WHERE 1=1
        """ if not USE_POSTGRES else """
            SELECT 
                f.flight_id,
                f.flight_number,
                f.flight_date,
                al.airline_id,
                al.airline_name,
                al.callsign_prefix,
                f.aircraft_reg_no,
                ac.model AS aircraft_model,
                ac.passenger_capacity,
                f.origin_airport,
                orig.city AS origin_city,
                orig.airport_name AS origin_airport_name,
                f.dest_airport,
                dest.city AS dest_city,
                dest.airport_name AS dest_airport_name,
                f.scheduled_departure,
                f.scheduled_arrival,
                f.actual_departure,
                f.actual_arrival,
                f.current_status,
                CASE 
                    WHEN f.actual_departure IS NOT NULL AND f.actual_departure > f.scheduled_departure THEN
                        ROUND(EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60)
                    ELSE 0
                END AS departure_delay_minutes
            FROM FLIGHT f
            JOIN AIRLINE al ON f.airline_id = al.airline_id
            JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
            JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
            JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
            WHERE 1=1
        """
        params = []
        placeholder = "%s" if USE_POSTGRES else "?"

        if search:
            search_param = f"%{search.strip().upper()}%"
            sql += f" AND (UPPER(f.flight_number) LIKE {placeholder} OR UPPER(f.aircraft_reg_no) LIKE {placeholder})"
            params.extend([search_param, search_param])

        if status and status != "ALL":
            sql += f" AND f.current_status = {placeholder}"
            params.append(status)

        if origin and origin != "ALL":
            sql += f" AND f.origin_airport = {placeholder}"
            params.append(origin)

        if dest and dest != "ALL":
            sql += f" AND f.dest_airport = {placeholder}"
            params.append(dest)

        if airline_id and airline_id != 0:
            sql += f" AND f.airline_id = {placeholder}"
            params.append(airline_id)

        sql += " ORDER BY f.scheduled_departure ASC"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_flight_by_id(flight_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves full flight details for a single leg."""
    flights = get_flights()
    for f in flights:
        if f["flight_id"] == flight_id:
            return f
    return None


def add_flight(
    flight_number: str,
    flight_date_val: str,
    airline_id: int,
    aircraft_reg_no: str,
    origin_airport: str,
    dest_airport: str,
    scheduled_departure: str,
    scheduled_arrival: str,
    current_status: str = "SCHEDULED"
) -> Tuple[bool, str]:
    """
    Schedules a new flight leg (INSERT operation) with database-level constraint enforcement.
    Validates origin <> dest and scheduled_arrival > scheduled_departure.
    """
    flight_number = flight_number.strip().upper()
    origin_airport = origin_airport.strip().upper()
    dest_airport = dest_airport.strip().upper()
    aircraft_reg_no = aircraft_reg_no.strip().upper()

    # Pre-validation (mirrors DB check constraints)
    if origin_airport == dest_airport:
        return False, f"Constraint Violation: Origin airport ({origin_airport}) and Destination ({dest_airport}) cannot be the same aerodrome!"

    if scheduled_arrival <= scheduled_departure:
        return False, "Constraint Violation: Scheduled arrival timestamp must be strictly after scheduled departure timestamp!"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        placeholder = "%s" if USE_POSTGRES else "?"
        sql = f"""
            INSERT INTO FLIGHT (
                flight_number, flight_date, airline_id, aircraft_reg_no,
                origin_airport, dest_airport, scheduled_departure, scheduled_arrival,
                current_status
            ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """
        cursor.execute(sql, (
            flight_number, flight_date_val, airline_id, aircraft_reg_no,
            origin_airport, dest_airport, scheduled_departure, scheduled_arrival,
            current_status
        ))
        conn.commit()
        return True, f"Flight {flight_number} successfully scheduled for {flight_date_val} ({origin_airport} -> {dest_airport})!"
    except Exception as e:
        conn.rollback()
        err_msg = str(e)
        if "UNIQUE" in err_msg.upper():
            return False, f"Database Integrity Error: Flight {flight_number} is already scheduled on date {flight_date_val} (Unique constraint violation)!"
        elif "CHECK" in err_msg.upper():
            return False, f"Database Check Constraint Failed: {err_msg}"
        elif "FOREIGN KEY" in err_msg.upper():
            return False, f"Referential Integrity Error: Invalid foreign key reference (Airline, Aircraft or Airport)! Details: {err_msg}"
        return False, f"Database Error: {err_msg}"
    finally:
        cursor.close()
        conn.close()


def update_flight_status(
    flight_id: int,
    new_status: str,
    actual_departure: Optional[str] = None,
    actual_arrival: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Updates the operational state of a flight (UPDATE operation).
    Transitions: SCHEDULED -> BOARDING -> TAXIING -> AIRBORNE -> LANDED or DIVERTED / CANCELLED.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        placeholder = "%s" if USE_POSTGRES else "?"
        
        sql = f"""
            UPDATE FLIGHT
            SET current_status = {placeholder},
                actual_departure = COALESCE({placeholder}, actual_departure),
                actual_arrival = COALESCE({placeholder}, actual_arrival)
            WHERE flight_id = {placeholder}
        """
        cursor.execute(sql, (new_status, actual_departure, actual_arrival, flight_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, f"Flight ID {flight_id} status updated to '{new_status}' successfully."
        return False, f"Flight ID {flight_id} not found."
    except Exception as e:
        conn.rollback()
        return False, f"Database Update Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def apply_departure_delay(flight_id: int, delay_minutes: int) -> Tuple[bool, str]:
    """
    Logs an operational departure delay for a flight.
    Sets actual_departure = scheduled_departure + delay_minutes.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Fetch flight details
        placeholder = "%s" if USE_POSTGRES else "?"
        cursor.execute(f"SELECT scheduled_departure, scheduled_arrival FROM FLIGHT WHERE flight_id = {placeholder}", (flight_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Flight ID {flight_id} not found."

        sched_dep = row[0]
        # Parse datetime
        if isinstance(sched_dep, str):
            sched_dt = datetime.fromisoformat(sched_dep.replace(" ", "T"))
        else:
            sched_dt = sched_dep

        actual_dep_dt = sched_dt + timedelta(minutes=delay_minutes)
        actual_dep_str = actual_dep_dt.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(f"""
            UPDATE FLIGHT 
            SET actual_departure = {placeholder},
                current_status = CASE WHEN current_status = 'SCHEDULED' THEN 'BOARDING' ELSE current_status END
            WHERE flight_id = {placeholder}
        """, (actual_dep_str, flight_id))
        conn.commit()
        return True, f"Logged {delay_minutes} min delay for Flight ID {flight_id}. New actual departure: {actual_dep_str}."
    except Exception as e:
        conn.rollback()
        return False, f"Error applying delay: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def cancel_or_delete_flight(flight_id: int, hard_delete: bool = False) -> Tuple[bool, str]:
    """
    Cancels or removes a flight (DELETE or status update to 'CANCELLED').
    Protects referential integrity against foreign key conflicts in GATE_ASSIGNMENT or FLIGHT_CLEARANCE.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        placeholder = "%s" if USE_POSTGRES else "?"
        if not hard_delete:
            cursor.execute(f"UPDATE FLIGHT SET current_status = 'CANCELLED' WHERE flight_id = {placeholder}", (flight_id,))
            conn.commit()
            return True, f"Flight ID {flight_id} marked as CANCELLED."
        else:
            # Check for dependent records
            cursor.execute(f"DELETE FROM FLIGHT WHERE flight_id = {placeholder}", (flight_id,))
            conn.commit()
            return True, f"Flight ID {flight_id} permanently deleted from database."
    except Exception as e:
        conn.rollback()
        err_msg = str(e)
        if "FOREIGN KEY" in err_msg.upper():
            return False, "Cannot delete flight: Active gate assignments or ATC clearance records depend on this flight! Mark as 'CANCELLED' instead to preserve audit logs."
        return False, f"Error deleting flight: {err_msg}"
    finally:
        cursor.close()
        conn.close()


# ----------------------------------------------------------------------------
# ANALYTICS & COMPLEX SQL QUERY EXECUTORS
# ----------------------------------------------------------------------------

def get_otp_analytics() -> List[Dict[str, Any]]:
    """
    Query 1: Airline On-Time Performance (OTP) summary.
    Computes scheduled count, departed count, on-time departures (within 15 min buffer),
    delayed departures, OTP rate %, and average delay minutes.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not USE_POSTGRES:
            sql = """
                SELECT 
                    al.airline_id,
                    al.airline_name,
                    al.callsign_prefix,
                    COUNT(f.flight_id) AS scheduled_legs,
                    COUNT(f.actual_departure) AS departed_legs,
                    SUM(CASE 
                        WHEN f.actual_departure IS NOT NULL AND 
                             (strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) <= 900
                        THEN 1 ELSE 0 
                    END) AS on_time_count,
                    SUM(CASE 
                        WHEN f.actual_departure IS NOT NULL AND 
                             (strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) > 900
                        THEN 1 ELSE 0 
                    END) AS delayed_count,
                    CASE 
                        WHEN COUNT(f.actual_departure) > 0 
                        THEN ROUND(
                            (SUM(CASE WHEN (strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) <= 900 THEN 1.0 ELSE 0.0 END) / COUNT(f.actual_departure)) * 100.0, 
                            2
                        )
                        ELSE 0.00 
                    END AS otp_rate_percentage,
                    ROUND(
                        COALESCE(AVG(CASE WHEN (strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) > 0 THEN (strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) / 60.0 ELSE 0 END), 0.0), 
                        1
                    ) AS avg_delay_mins
                FROM AIRLINE al
                LEFT JOIN FLIGHT f ON al.airline_id = f.airline_id
                GROUP BY al.airline_id, al.airline_name, al.callsign_prefix
                ORDER BY otp_rate_percentage DESC, scheduled_legs DESC;
            """
        else:
            sql = """
                SELECT 
                    al.airline_id,
                    al.airline_name,
                    al.callsign_prefix,
                    COUNT(f.flight_id) AS scheduled_legs,
                    COUNT(f.actual_departure) AS departed_legs,
                    SUM(CASE 
                        WHEN f.actual_departure IS NOT NULL AND f.actual_departure <= (f.scheduled_departure + INTERVAL '15 minutes') 
                        THEN 1 ELSE 0 
                    END) AS on_time_count,
                    SUM(CASE 
                        WHEN f.actual_departure IS NOT NULL AND f.actual_departure > (f.scheduled_departure + INTERVAL '15 minutes') 
                        THEN 1 ELSE 0 
                    END) AS delayed_count,
                    CASE 
                        WHEN COUNT(f.actual_departure) > 0 
                        THEN ROUND(
                            (SUM(CASE WHEN f.actual_departure <= (f.scheduled_departure + INTERVAL '15 minutes') THEN 1.0 ELSE 0.0 END) / COUNT(f.actual_departure)) * 100.0, 
                            2
                        )
                        ELSE 0.00 
                    END AS otp_rate_percentage,
                    ROUND(
                        COALESCE(AVG(CASE WHEN f.actual_departure > f.scheduled_departure THEN EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60.0 ELSE 0 END), 0.0), 
                        1
                    ) AS avg_delay_mins
                FROM AIRLINE al
                LEFT JOIN FLIGHT f ON al.airline_id = f.airline_id
                GROUP BY al.airline_id, al.airline_name, al.callsign_prefix
                ORDER BY otp_rate_percentage DESC, scheduled_legs DESC;
            """
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_route_density_analytics(min_flights: int = 1) -> List[Dict[str, Any]]:
    """
    Query 2: High-Density Flight Corridors & Bottlenecks.
    Demonstrates GROUP BY, HAVING, and multi-table joins.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        placeholder = "%s" if USE_POSTGRES else "?"
        sql = f"""
            SELECT 
                (f.origin_airport || ' -> ' || f.dest_airport) AS route_corridor,
                orig.city AS origin_city,
                dest.city AS dest_city,
                COUNT(f.flight_id) AS total_scheduled_flights,
                COUNT(DISTINCT f.airline_id) AS competing_airlines_count,
                COUNT(DISTINCT f.aircraft_reg_no) AS distinct_aircraft_assigned,
                MIN(f.scheduled_departure) AS earliest_departure,
                MAX(f.scheduled_departure) AS latest_departure
            FROM FLIGHT f
            JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
            JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
            GROUP BY f.origin_airport, f.dest_airport, orig.city, dest.city
            HAVING COUNT(f.flight_id) >= {placeholder}
            ORDER BY total_scheduled_flights DESC, route_corridor ASC
        """
        cursor.execute(sql, (min_flights,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_excessive_delays(threshold_minutes: int = 30) -> List[Dict[str, Any]]:
    """
    Query 3: Excessive Delays Investigation (Correlated Subquery Demonstration).
    Finds flights delayed past threshold with carrier dispatch contact information.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        placeholder = "%s" if USE_POSTGRES else "?"
        if not USE_POSTGRES:
            threshold_seconds = threshold_minutes * 60
            sql = f"""
                SELECT 
                    f.flight_id,
                    f.flight_number,
                    f.flight_date,
                    al.airline_name,
                    al.contact_email AS dispatch_alert_email,
                    f.aircraft_reg_no,
                    ac.model AS aircraft_type,
                    (f.origin_airport || ' -> ' || f.dest_airport) AS corridor,
                    f.scheduled_departure,
                    f.actual_departure,
                    ROUND((strftime('%s', f.actual_departure) - strftime('%s', f.scheduled_departure)) / 60) AS delay_minutes,
                    f.current_status
                FROM FLIGHT f
                JOIN AIRLINE al ON f.airline_id = al.airline_id
                JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
                WHERE f.actual_departure IS NOT NULL
                  AND f.flight_id IN (
                      SELECT sub_f.flight_id 
                      FROM FLIGHT sub_f 
                      WHERE (strftime('%s', sub_f.actual_departure) - strftime('%s', sub_f.scheduled_departure)) > {placeholder}
                  )
                ORDER BY delay_minutes DESC;
            """
            cursor.execute(sql, (threshold_seconds,))
        else:
            sql = f"""
                SELECT 
                    f.flight_id,
                    f.flight_number,
                    f.flight_date,
                    al.airline_name,
                    al.contact_email AS dispatch_alert_email,
                    f.aircraft_reg_no,
                    ac.model AS aircraft_type,
                    (f.origin_airport || ' -> ' || f.dest_airport) AS corridor,
                    f.scheduled_departure,
                    f.actual_departure,
                    ROUND(EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60) AS delay_minutes,
                    f.current_status
                FROM FLIGHT f
                JOIN AIRLINE al ON f.airline_id = al.airline_id
                JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
                WHERE f.actual_departure IS NOT NULL
                  AND f.flight_id IN (
                      SELECT sub_f.flight_id 
                      FROM FLIGHT sub_f 
                      WHERE sub_f.actual_departure > (sub_f.scheduled_departure + ({placeholder} || ' minutes')::INTERVAL)
                  )
                ORDER BY delay_minutes DESC;
            """
            cursor.execute(sql, (threshold_minutes,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_fleet_capacity_report() -> List[Dict[str, Any]]:
    """
    Query 4: Aircraft Fleet Utilization vs Industry Average (Scalar Subquery).
    Finds aircraft exceeding average passenger capacity.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT 
                ac.aircraft_reg_no,
                ac.model,
                ac.manufacturer,
                ac.passenger_capacity,
                al.airline_name,
                ROUND((ac.passenger_capacity - (SELECT AVG(passenger_capacity) FROM AIRCRAFT)), 1) AS seats_above_fleet_avg,
                COUNT(f.flight_id) AS total_assigned_flights
            FROM AIRCRAFT ac
            JOIN AIRLINE al ON ac.airline_id = al.airline_id
            LEFT JOIN FLIGHT f ON ac.aircraft_reg_no = f.aircraft_reg_no
            WHERE ac.passenger_capacity > (SELECT AVG(passenger_capacity) FROM AIRCRAFT)
            GROUP BY ac.aircraft_reg_no, ac.model, ac.manufacturer, ac.passenger_capacity, al.airline_name
            ORDER BY ac.passenger_capacity DESC
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def execute_raw_sql(sql_query: str) -> Tuple[bool, Any]:
    """Executes a custom SELECT or DML query for live course evaluator demonstration."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        if sql_query.strip().upper().startswith("SELECT"):
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return True, {"columns": columns, "data": [dict(zip(columns, row)) for row in rows]}
        else:
            conn.commit()
            return True, f"Statement executed successfully. Rows affected: {cursor.rowcount}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


# ----------------------------------------------------------------------------
# EMBEDDED SQLITE SCHEMA & SEED FOR ZERO-CONFIGURATION EXECUTION
# ----------------------------------------------------------------------------
_SQLITE_SCHEMA_AND_SEED = """
-- 1. Airports
CREATE TABLE IF NOT EXISTS AIRPORT (
    airport_code VARCHAR(4) PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    elevation_ft INT CHECK (elevation_ft >= -1500 AND elevation_ft <= 15000)
);

-- 2. Airlines (Member 2 Owned)
CREATE TABLE IF NOT EXISTS AIRLINE (
    airline_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    callsign_prefix VARCHAR(10) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50) NOT NULL DEFAULT 'India',
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

-- 3. Aircraft (Member 2 Owned)
CREATE TABLE IF NOT EXISTS AIRCRAFT (
    aircraft_reg_no VARCHAR(12) PRIMARY KEY,
    model VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    passenger_capacity INT CHECK (passenger_capacity > 0),
    max_altitude_ft INT CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000),
    cruising_speed_knots INT CHECK (cruising_speed_knots > 0),
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE CASCADE
);

-- 4. Runways (Member 1 Owned)
CREATE TABLE IF NOT EXISTS RUNWAY (
    runway_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    runway_designator VARCHAR(10) NOT NULL,
    length_meters INT NOT NULL CHECK (length_meters >= 1000),
    surface_type VARCHAR(30) DEFAULT 'ASPHALT',
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE' CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED')),
    UNIQUE (airport_code, runway_designator)
);

-- 5. Gates (Member 1 Owned)
CREATE TABLE IF NOT EXISTS GATE (
    gate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    terminal_number VARCHAR(10) NOT NULL,
    gate_number VARCHAR(10) NOT NULL,
    gate_category VARCHAR(20) NOT NULL DEFAULT 'DOMESTIC' CHECK (gate_category IN ('DOMESTIC', 'INTERNATIONAL')),
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE' CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    UNIQUE (airport_code, terminal_number, gate_number)
);

-- 6. Airspace Sectors (Member 3 Owned)
CREATE TABLE IF NOT EXISTS AIRSPACE_SECTOR (
    sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name VARCHAR(50) NOT NULL UNIQUE,
    floor_altitude_ft INT NOT NULL CHECK (floor_altitude_ft >= 0),
    ceiling_altitude_ft INT NOT NULL CHECK (ceiling_altitude_ft > floor_altitude_ft),
    max_capacity INT NOT NULL CHECK (max_capacity > 0)
);

-- 7. Controllers (Member 3 Owned)
CREATE TABLE IF NOT EXISTS CONTROLLER (
    controller_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    license_number VARCHAR(30) NOT NULL UNIQUE,
    certification_level VARCHAR(20) NOT NULL CHECK (certification_level IN ('GROUND', 'TOWER', 'APPROACH', 'EN_ROUTE')),
    shift_start TIME NOT NULL,
    shift_end TIME NOT NULL,
    assigned_sector_id INT REFERENCES AIRSPACE_SECTOR(sector_id) ON DELETE SET NULL
);

-- 8. Flights (Member 2 Owned)
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

-- 9. Gate Assignments (Member 1 Owned)
CREATE TABLE IF NOT EXISTS GATE_ASSIGNMENT (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
    gate_id INT NOT NULL REFERENCES GATE(gate_id) ON DELETE CASCADE,
    assigned_from TIMESTAMP NOT NULL,
    assigned_until TIMESTAMP NOT NULL,
    assignment_type VARCHAR(10) NOT NULL CHECK (assignment_type IN ('ARRIVAL', 'DEPARTURE')),
    CHECK (assigned_until > assigned_from)
);

-- 10. Flight Clearances (Member 3 Owned)
CREATE TABLE IF NOT EXISTS FLIGHT_CLEARANCE (
    clearance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
    controller_id INT NOT NULL REFERENCES CONTROLLER(controller_id),
    runway_id INT REFERENCES RUNWAY(runway_id),
    clearance_type VARCHAR(30) NOT NULL CHECK (clearance_type IN ('PUSHBACK', 'TAXI', 'TAKEOFF', 'ALTITUDE_CHANGE', 'HEADING', 'LANDING')),
    issued_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_altitude_ft INT CHECK (assigned_altitude_ft >= 0 AND assigned_altitude_ft <= 60000),
    assigned_heading_deg INT CHECK (assigned_heading_deg >= 0 AND assigned_heading_deg <= 360)
);

-- 11. Incident Log (Member 3 Owned)
CREATE TABLE IF NOT EXISTS INCIDENT_LOG (
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INT REFERENCES FLIGHT(flight_id) ON DELETE SET NULL,
    reported_by INT NOT NULL REFERENCES CONTROLLER(controller_id),
    incident_type VARCHAR(30) NOT NULL CHECK (incident_type IN ('NEAR_MISS', 'RUNWAY_INCURSION', 'ALTITUDE_BUST', 'BIRD_STRIKE', 'WEATHER_DIVERT')),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    incident_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_flight_dates ON FLIGHT(flight_date, origin_airport, dest_airport);
CREATE INDEX IF NOT EXISTS idx_flight_status ON FLIGHT(current_status);
CREATE INDEX IF NOT EXISTS idx_flight_carrier ON FLIGHT(airline_id);
CREATE INDEX IF NOT EXISTS idx_flight_aircraft ON FLIGHT(aircraft_reg_no);

-- Populate Airports
INSERT OR IGNORE INTO AIRPORT (airport_code, airport_name, city, country, latitude, longitude, elevation_ft) VALUES
('DEL', 'Indira Gandhi International Airport', 'New Delhi', 'India', 28.556200, 77.100000, 777),
('BOM', 'Chhatrapati Shivaji Maharaj Int Airport', 'Mumbai', 'India', 19.089600, 72.865600, 39),
('BLR', 'Kempegowda International Airport', 'Bengaluru', 'India', 13.198600, 77.706600, 3000),
('MAA', 'Chennai International Airport', 'Chennai', 'India', 12.994100, 80.170900, 52),
('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad', 'India', 17.240300, 78.429400, 2024),
('CCU', 'Netaji Subhash Chandra Bose Int Airport', 'Kolkata', 'India', 22.654700, 88.446700, 16),
('AMD', 'Sardar Vallabhbhai Patel Int Airport', 'Ahmedabad', 'India', 23.077200, 72.634700, 189),
('COK', 'Cochin International Airport', 'Kochi', 'India', 10.152000, 76.401900, 30),
('PNQ', 'Pune Airport', 'Pune', 'India', 18.582200, 73.919700, 1942),
('GOX', 'Manohar International Airport', 'Mopa, Goa', 'India', 15.766700, 73.866700, 558),
('JAI', 'Jaipur International Airport', 'Jaipur', 'India', 26.824200, 75.812200, 1263),
('GAU', 'Lokpriya Gopinath Bordoloi Int Airport', 'Guwahati', 'India', 26.106100, 91.585900, 162);

-- Populate Airlines (Member 2)
INSERT OR IGNORE INTO AIRLINE (airline_id, airline_name, callsign_prefix, country_of_origin, contact_email) VALUES
(1, 'IndiGo', 'IGO', 'India', 'operations@goindigo.in'),
(2, 'Air India', 'AIC', 'India', 'dispatch@airindia.com'),
(3, 'SpiceJet', 'SEJ', 'India', 'ops@spicejet.com'),
(4, 'Akasa Air', 'AKJ', 'India', 'atc@akasaair.com'),
(5, 'Vistara', 'VTI', 'India', 'dispatch@airvistara.com'),
(6, 'AIX Connect', 'IAD', 'India', 'ops@aixconnect.in');

-- Populate Aircraft Fleet (Member 2)
INSERT OR IGNORE INTO AIRCRAFT (aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft, cruising_speed_knots, airline_id) VALUES
('VT-ISN', 'A320neo', 'Airbus', 186, 39000, 450, 1),
('VT-IFP', 'A321neo', 'Airbus', 222, 39000, 460, 1),
('VT-IMR', 'A320neo', 'Airbus', 186, 39000, 450, 1),
('VT-EXF', 'B787-8 Dreamliner', 'Boeing', 256, 43000, 490, 2),
('VT-CIO', 'A320neo', 'Airbus', 180, 39000, 450, 2),
('VT-ALQ', 'B777-300ER', 'Boeing', 342, 43100, 490, 2),
('VT-SLA', 'B737-800', 'Boeing', 189, 41000, 455, 3),
('VT-SGZ', 'B737-MAX8', 'Boeing', 189, 41000, 460, 3),
('VT-YAA', 'B737-MAX8', 'Boeing', 189, 41000, 460, 4),
('VT-YAE', 'B737-MAX8', 'Boeing', 189, 41000, 460, 4),
('VT-TVA', 'A320neo', 'Airbus', 164, 39000, 450, 5),
('VT-TTB', 'B787-9 Dreamliner', 'Boeing', 299, 43000, 490, 5),
('VT-IXC', 'A320-200', 'Airbus', 180, 39000, 445, 6);

-- Populate Runways
INSERT OR IGNORE INTO RUNWAY (runway_id, airport_code, runway_designator, length_meters, current_status) VALUES
(1, 'DEL', '09/27', 3810, 'AVAILABLE'),
(2, 'DEL', '10/28', 3810, 'AVAILABLE'),
(3, 'DEL', '11/29', 4430, 'AVAILABLE'),
(4, 'BOM', '09/27', 3445, 'AVAILABLE'),
(5, 'BOM', '14/32', 2925, 'AVAILABLE'),
(6, 'MAA', '07/25', 3658, 'AVAILABLE'),
(7, 'BLR', '09L/27R', 4000, 'AVAILABLE');

-- Populate Gates
INSERT OR IGNORE INTO GATE (gate_id, airport_code, terminal_number, gate_number, gate_category, current_status) VALUES
(1, 'DEL', 'T3', '01A', 'DOMESTIC', 'AVAILABLE'),
(2, 'DEL', 'T3', '02B', 'DOMESTIC', 'AVAILABLE'),
(3, 'DEL', 'T3', '14A', 'INTERNATIONAL', 'AVAILABLE'),
(4, 'BOM', 'T2', '45', 'DOMESTIC', 'AVAILABLE'),
(5, 'BLR', 'T1', '08', 'DOMESTIC', 'AVAILABLE'),
(6, 'MAA', 'T1', '04', 'DOMESTIC', 'AVAILABLE');

-- Populate Sectors
INSERT OR IGNORE INTO AIRSPACE_SECTOR (sector_id, sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity) VALUES
(1, 'Delhi FIR (VIDF)', 0, 46000, 60),
(2, 'Mumbai FIR (VABF)', 0, 46000, 55),
(3, 'Chennai FIR (VOMF)', 0, 46000, 50),
(4, 'Kolkata FIR (VECF)', 0, 46000, 45);

-- Populate Controllers
INSERT OR IGNORE INTO CONTROLLER (controller_id, first_name, last_name, license_number, certification_level, shift_start, shift_end, assigned_sector_id) VALUES
(1, 'Vikram', 'Rathore', 'AAI-ATCO-1092', 'TOWER', '06:00', '14:00', 1),
(2, 'Ananya', 'Sharma', 'AAI-ATCO-2234', 'EN_ROUTE', '06:00', '14:00', 1),
(3, 'Karthik', 'Ramanathan', 'AAI-ATCO-3310', 'TOWER', '14:00', '22:00', 3),
(4, 'Neha', 'Deshmukh', 'AAI-ATCO-5582', 'TOWER', '06:00', '14:00', 2);

-- Populate Scheduled Flights (Member 2)
INSERT OR IGNORE INTO FLIGHT (flight_id, flight_number, flight_date, airline_id, aircraft_reg_no, origin_airport, dest_airport, scheduled_departure, scheduled_arrival, actual_departure, actual_arrival, current_status) VALUES
(1, '6E-204', '2026-11-01', 1, 'VT-ISN', 'DEL', 'MAA', '2026-11-01 07:00:00', '2026-11-01 09:45:00', '2026-11-01 07:05:00', NULL, 'AIRBORNE'),
(2, 'AI-101', '2026-11-01', 2, 'VT-EXF', 'BOM', 'DEL', '2026-11-01 08:30:00', '2026-11-01 10:40:00', NULL, NULL, 'BOARDING'),
(3, '6E-532', '2026-11-01', 1, 'VT-IFP', 'BLR', 'DEL', '2026-11-01 09:15:00', '2026-11-01 12:00:00', NULL, NULL, 'SCHEDULED'),
(4, 'QP-1102', '2026-11-01', 4, 'VT-YAA', 'BOM', 'BLR', '2026-11-01 10:00:00', '2026-11-01 11:45:00', NULL, NULL, 'SCHEDULED'),
(5, 'SG-8169', '2026-11-01', 3, 'VT-SLA', 'DEL', 'AMD', '2026-11-01 11:00:00', '2026-11-01 12:35:00', NULL, NULL, 'SCHEDULED'),
(6, 'UK-871', '2026-11-01', 5, 'VT-TVA', 'DEL', 'BOM', '2026-11-01 06:00:00', '2026-11-01 08:10:00', '2026-11-01 06:03:00', '2026-11-01 08:08:00', 'LANDED'),
(7, 'AI-624', '2026-11-01', 2, 'VT-CIO', 'DEL', 'HYD', '2026-11-01 07:30:00', '2026-11-01 09:40:00', '2026-11-01 08:12:00', '2026-11-01 10:18:00', 'LANDED'),
(8, '6E-5011', '2026-11-01', 1, 'VT-IMR', 'BOM', 'DEL', '2026-11-01 12:00:00', '2026-11-01 14:15:00', NULL, NULL, 'SCHEDULED'),
(9, 'AI-805', '2026-11-01', 2, 'VT-ALQ', 'DEL', 'BOM', '2026-11-01 14:00:00', '2026-11-01 16:15:00', NULL, NULL, 'SCHEDULED'),
(10, 'QP-1314', '2026-11-01', 4, 'VT-YAE', 'BOM', 'GOX', '2026-11-01 13:30:00', '2026-11-01 14:45:00', NULL, NULL, 'SCHEDULED'),
(11, '6E-212', '2026-11-01', 1, 'VT-ISN', 'DEL', 'CCU', '2026-11-01 15:00:00', '2026-11-01 17:10:00', NULL, NULL, 'SCHEDULED'),
(12, 'I5-982', '2026-11-01', 6, 'VT-IXC', 'BLR', 'MAA', '2026-11-01 08:00:00', '2026-11-01 08:55:00', '2026-11-01 08:02:00', '2026-11-01 08:54:00', 'LANDED'),
(13, 'SG-103', '2026-11-01', 3, 'VT-SGZ', 'DEL', 'PNQ', '2026-11-01 06:45:00', '2026-11-01 08:50:00', '2026-11-01 07:35:00', '2026-11-01 09:38:00', 'LANDED'),
(14, 'UK-993', '2026-11-01', 5, 'VT-TTB', 'DEL', 'BLR', '2026-11-01 08:45:00', '2026-11-01 11:30:00', NULL, NULL, 'TAXIING');

-- Populate Gate Assignments
INSERT OR IGNORE INTO GATE_ASSIGNMENT (assignment_id, flight_id, gate_id, assigned_from, assigned_until, assignment_type) VALUES
(1, 1, 1, '2026-11-01 06:00:00', '2026-11-01 07:00:00', 'DEPARTURE'),
(2, 2, 4, '2026-11-01 07:30:00', '2026-11-01 08:30:00', 'DEPARTURE');

-- Populate Flight Clearances
INSERT OR IGNORE INTO FLIGHT_CLEARANCE (clearance_id, flight_id, controller_id, runway_id, clearance_type, issued_timestamp, assigned_altitude_ft, assigned_heading_deg) VALUES
(1, 1, 1, 1, 'TAKEOFF', '2026-11-01 07:02:00', 5000, 90),
(2, 1, 2, NULL, 'ALTITUDE_CHANGE', '2026-11-01 07:20:00', 36000, 175);
"""

# Automatically initialize database on module import
init_database()
