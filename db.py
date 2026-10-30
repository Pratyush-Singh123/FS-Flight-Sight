"""
SkyFlow ATCMS - Master Unified Database Layer (db.py)
Unifies Member 1 (Ground Hubs), Member 2 (Flight Ops), and Member 3 (ATC Tower & Safety).

Key Features:
- Dual Engine Architecture: Seamless PostgreSQL (production) with automatic zero-config SQLite fallback.
- Multi-Member Trigger Interlocks:
  * Member 1: Gate double-booking prevention trigger.
  * Member 3: Runway takeoff/landing collision prevention trigger.
  * Integration: Automatic flight status progression (Takeoff -> AIRBORNE, Landing -> LANDED)
    and automatic runway state updates (AVAILABLE -> OCCUPIED).
- Cross-Dialect SQL Execution Engine: Translates PostgreSQL syntax (date_trunc, intervals)
  transparently for SQLite, enabling identical analytical query execution across engines.
- Complete API for all 3 members + unified system telemetry.
"""

import os
import re
import sqlite3
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skyflow.db")
PG_URL = os.environ.get("DATABASE_URL") or os.environ.get("PG_CONNECTION_STRING")

# Detect PostgreSQL availability
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


def is_postgres() -> bool:
    """Check if PostgreSQL backend is currently active."""
    return USE_POSTGRES


def get_connection():
    """Returns an active database connection with row factory and custom SQL functions."""
    if USE_POSTGRES and pg_module:
        conn = pg_module.connect(PG_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Register custom SQLite functions to emulate PostgreSQL built-ins
        def _date_trunc(part, val):
            if not val:
                return None
            try:
                dt = datetime.fromisoformat(str(val).replace("Z", ""))
                if part == "hour":
                    return dt.strftime("%Y-%m-%d %H:00:00")
                elif part == "day":
                    return dt.strftime("%Y-%m-%d 00:00:00")
            except Exception:
                pass
            return str(val)

        conn.create_function("date_trunc", 2, _date_trunc)
        return conn


def run_query(query: str, params: Optional[Tuple] = None, is_dml: bool = False) -> Any:
    """
    Executes a SQL query safely across either PostgreSQL or SQLite.
    Translates placeholders (%s -> ?) and PostgreSQL interval math if on SQLite.
    """
    conn = get_connection()
    try:
        if USE_POSTGRES:
            with conn:
                with conn.cursor(cursor_factory=pg_module.extras.RealDictCursor) as cur:
                    cur.execute(query, params or ())
                    if is_dml:
                        conn.commit()
                        return True
                    return [dict(r) for r in cur.fetchall()]
        else:
            # SQLite query normalization
            q = query
            # Translate EXTRACT(EPOCH FROM (A - B)) to ((julianday(A) - julianday(B)) * 86400.0)
            q = re.sub(
                r'EXTRACT\s*\(\s*EPOCH\s+FROM\s*\(([^)]+)\s*-\s*([^)]+)\)\)',
                r'((julianday(\1) - julianday(\2)) * 86400.0)',
                q,
                flags=re.IGNORECASE
            )
            # Remove ::numeric, ::text type casts
            q = re.sub(r'::[a-zA-Z0-9_]+', '', q)
            # Replace %s with ? for SQLite parameterized queries
            q = q.replace("%s", "?")
            
            cur = conn.cursor()
            cur.execute(q, params or ())
            if is_dml:
                conn.commit()
                return True
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        if is_dml:
            try:
                conn.rollback()
            except Exception:
                pass
        raise e
    finally:
        conn.close()


# ----------------------------------------------------------------------------
# UNIFIED DATABASE SCHEMA & SEED DATA INITIALIZATION
# ----------------------------------------------------------------------------

def init_database(force_reseed: bool = False):
    """Initializes tables, constraints, triggers, views, and realistic Indian seed data."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if not USE_POSTGRES:
            # Check if FLIGHT table already exists in SQLite
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='FLIGHT';")
            exists = cur.fetchone()

            if not exists or force_reseed:
                cur.executescript(_UNIFIED_SQLITE_DDL_AND_SEED)
                conn.commit()
        else:
            schema_file = os.path.join(os.path.dirname(__file__), "schema_and_seed.sql")
            if os.path.exists(schema_file):
                with open(schema_file, "r") as f:
                    cur.execute(f.read())
                conn.commit()
    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------------------------
# MEMBER 1 OPERATIONS API (Ground Infrastructure & Terminal Movement)
# ----------------------------------------------------------------------------

def get_airports() -> List[Dict[str, Any]]:
    """Retrieves all 12 major Indian airport facilities."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT airport_code, airport_name, name, city, country, latitude, longitude, elevation_ft FROM AIRPORT ORDER BY city ASC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_runways(airport_code: Optional[str] = None) -> pd.DataFrame:
    """Retrieves runways with real-time operational status."""
    conn = get_connection()
    if airport_code:
        query = "SELECT * FROM RUNWAY WHERE airport_code = ? ORDER BY runway_designator;"
        df = pd.read_sql_query(query, conn, params=[airport_code])
    else:
        query = "SELECT * FROM RUNWAY ORDER BY airport_code, runway_designator;"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def set_runway_status(runway_id: int, new_status: str) -> Tuple[bool, str]:
    """Updates physical runway status (AVAILABLE, OCCUPIED, CLOSED)."""
    try:
        run_query("UPDATE RUNWAY SET current_status = ? WHERE runway_id = ?;", (new_status, runway_id), is_dml=True)
        return True, f"Runway ID {runway_id} status updated to {new_status}."
    except Exception as e:
        return False, str(e)


def get_gates(airport_code: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves terminal gates with optional filtering."""
    q = "SELECT gate_id, airport_code, terminal_number, terminal, gate_number, gate_category, gate_type, current_status FROM GATE WHERE 1=1"
    params = []
    if airport_code:
        q += " AND airport_code = ?"
        params.append(airport_code)
    if status and status != "ALL":
        q += " AND current_status = ?"
        params.append(status)
    q += " ORDER BY terminal_number, gate_number;"
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def assign_gate(gate_id: int, flight_id: int, assigned_from: str, assigned_until: str, status: str = "CONFIRMED") -> Tuple[bool, str]:
    """
    Books a gate assignment. Enforces the Gate Overlap Prevention Trigger.
    """
    try:
        run_query("""
            INSERT INTO GATE_ASSIGNMENT (gate_id, flight_id, assigned_from, assigned_until, assignment_type, status)
            VALUES (?, ?, ?, ?, 'DEPARTURE', ?);
        """, (gate_id, flight_id, assigned_from, assigned_until, status), is_dml=True)
        return True, "Gate successfully assigned to flight."
    except Exception as e:
        err = str(e)
        if "GATE_DOUBLE_BOOKED" in err or "ABORT" in err:
            return False, "⚠️ GATE CONFLICT: Gate is already booked during this time interval! Choose another gate or time window."
        return False, f"Database error: {err}"


def cancel_gate_assignment(assignment_id: int) -> Tuple[bool, str]:
    """Cancels or deletes an existing gate assignment."""
    try:
        run_query("DELETE FROM GATE_ASSIGNMENT WHERE assignment_id = ?;", (assignment_id,), is_dml=True)
        return True, f"Gate Assignment #{assignment_id} successfully cancelled."
    except Exception as e:
        return False, str(e)


def get_ground_dashboard_view(airport_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches pre-aggregated operational health from view_airport_ground_dashboard."""
    if airport_code:
        return run_query("SELECT * FROM view_airport_ground_dashboard WHERE airport_code = ?;", (airport_code,))
    return run_query("SELECT * FROM view_airport_ground_dashboard ORDER BY airport_code;")


def get_runway_congestion() -> List[Dict[str, Any]]:
    """Member 1 Query 1: Runway congestion grouped by peak hour."""
    q = """
    SELECT 
        r.airport_code,
        r.runway_designator,
        date_trunc('hour', f.scheduled_departure) AS peak_hour_window,
        COUNT(f.flight_id) AS total_scheduled_movements,
        r.current_status AS runway_status
    FROM RUNWAY r
    JOIN FLIGHT f ON r.runway_id = f.assigned_runway_id
    WHERE f.current_status NOT IN ('CANCELLED', 'DIVERTED')
    GROUP BY r.airport_code, r.runway_designator, date_trunc('hour', f.scheduled_departure), r.current_status
    HAVING COUNT(f.flight_id) >= 1
    ORDER BY total_scheduled_movements DESC, peak_hour_window ASC;
    """
    return run_query(q)


def get_gate_turnaround_stats() -> List[Dict[str, Any]]:
    """Member 1 Query 2: Gate turnaround time analysis using subqueries and aggregation."""
    q = """
    SELECT 
        g.airport_code,
        g.terminal_number AS terminal,
        g.gate_number,
        g.gate_category AS gate_type,
        stats.total_flights_handled,
        ROUND(stats.avg_turnaround_minutes, 1) AS avg_turnaround_mins,
        stats.min_turnaround_minutes,
        stats.max_turnaround_minutes
    FROM GATE g
    JOIN (
        SELECT 
            gate_id,
            COUNT(assignment_id) AS total_flights_handled,
            AVG(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS avg_turnaround_minutes,
            MIN(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS min_turnaround_minutes,
            MAX(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS max_turnaround_minutes
        FROM GATE_ASSIGNMENT
        WHERE status IN ('COMPLETED', 'OCCUPIED', 'CONFIRMED')
        GROUP BY gate_id
    ) stats ON g.gate_id = stats.gate_id
    ORDER BY stats.total_flights_handled DESC, avg_turnaround_mins DESC;
    """
    return run_query(q)


# ----------------------------------------------------------------------------
# MEMBER 2 OPERATIONS API (Commercial Fleet & Flight Operations)
# ----------------------------------------------------------------------------

def get_airlines() -> List[Dict[str, Any]]:
    """Retrieves all registered operating carriers."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT airline_id, airline_name, callsign_prefix, country_of_origin, contact_email FROM AIRLINE ORDER BY airline_name ASC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_aircraft(airline_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves aircraft fleet, optionally filtered by operating airline."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if airline_id:
            cur.execute("""
                SELECT ac.aircraft_reg_no, ac.model, ac.manufacturer, ac.passenger_capacity,
                       ac.max_altitude_ft, ac.cruising_speed_knots, ac.airline_id, al.airline_name
                FROM AIRCRAFT ac
                JOIN AIRLINE al ON ac.airline_id = al.airline_id
                WHERE ac.airline_id = ?
                ORDER BY ac.aircraft_reg_no ASC
            """, (airline_id,))
        else:
            cur.execute("""
                SELECT ac.aircraft_reg_no, ac.model, ac.manufacturer, ac.passenger_capacity,
                       ac.max_altitude_ft, ac.cruising_speed_knots, ac.airline_id, al.airline_name
                FROM AIRCRAFT ac
                JOIN AIRLINE al ON ac.airline_id = al.airline_id
                ORDER BY al.airline_name ASC, ac.aircraft_reg_no ASC
            """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_flights(
    search: Optional[str] = None,
    status: Optional[str] = None,
    origin: Optional[str] = None,
    dest: Optional[str] = None,
    destination: Optional[str] = None,
    airline_id: Optional[int] = None,
    date_val: Optional[str] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """Member 2 View 1: Retrieves flight dispatch board with multi-criteria filtering."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        conditions = []
        params = []
        target_dest = dest or destination

        if search:
            search_param = f"%{search.strip().upper()}%"
            conditions.append("(UPPER(f.flight_number) LIKE ? OR UPPER(f.aircraft_reg_no) LIKE ?)")
            params.extend([search_param, search_param])

        if origin and origin != "ALL":
            conditions.append("f.origin_airport = ?")
            params.append(origin)

        if target_dest and target_dest != "ALL":
            conditions.append("f.dest_airport = ?")
            params.append(target_dest)

        if status and status != "ALL":
            conditions.append("f.current_status = ?")
            params.append(status)

        if airline_id and airline_id != 0:
            conditions.append("f.airline_id = ?")
            params.append(airline_id)

        if date_val:
            conditions.append("f.flight_date = ?")
            params.append(date_val)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""
            SELECT 
                f.flight_id, f.flight_number, f.flight_date,
                al.airline_id, al.airline_name, al.callsign_prefix,
                f.aircraft_reg_no, ac.model AS aircraft_model, ac.passenger_capacity,
                f.origin_airport, orig.city AS origin_city, orig.airport_name AS origin_airport_name,
                f.dest_airport, dest.city AS dest_city, dest.airport_name AS dest_airport_name,
                f.scheduled_departure, f.scheduled_arrival,
                f.actual_departure, f.actual_arrival,
                f.current_status,
                CASE 
                    WHEN f.actual_departure IS NOT NULL AND f.actual_departure > f.scheduled_departure 
                        THEN ROUND(((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440.0))
                    ELSE 0
                END AS departure_delay_minutes
            FROM FLIGHT f
            JOIN AIRLINE al ON f.airline_id = al.airline_id
            JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
            JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
            JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
            {where_clause}
            ORDER BY f.scheduled_departure ASC;
        """
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_flight_by_id(flight_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single flight record by its surrogate flight_id."""
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
    current_status: str = "SCHEDULED",
    **kwargs
) -> Tuple[bool, str]:
    """
    Schedules a new commercial flight leg.
    Enforces route rules (origin <> dest) and time order (arrival > departure).
    """
    flight_number = flight_number.strip().upper()
    origin_airport = origin_airport.strip().upper()
    dest_airport = dest_airport.strip().upper()
    aircraft_reg_no = aircraft_reg_no.strip().upper()

    if origin_airport == dest_airport:
        return False, f"Constraint Violation: Origin airport ({origin_airport}) and Destination ({dest_airport}) cannot be the same aerodrome!"

    dep_dt = datetime.fromisoformat(scheduled_departure)
    arr_dt = datetime.fromisoformat(scheduled_arrival)
    if arr_dt <= dep_dt:
        return False, "Constraint Violation: Scheduled arrival timestamp must be strictly after scheduled departure timestamp!"

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO FLIGHT (
                flight_number, flight_date, airline_id, aircraft_reg_no,
                origin_airport, dest_airport, destination_airport,
                scheduled_departure, scheduled_arrival, current_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            flight_number,
            flight_date_val,
            airline_id,
            aircraft_reg_no,
            origin_airport,
            dest_airport,
            dest_airport,
            scheduled_departure,
            scheduled_arrival,
            current_status
        ))
        conn.commit()
        last_id = cur.lastrowid
        return True, f"Flight {flight_number} successfully scheduled for {flight_date_val} ({origin_airport} -> {dest_airport})!"
    except Exception as e:
        conn.rollback()
        err_msg = str(e)
        if "UNIQUE" in err_msg.upper():
            return False, f"Database Integrity Error: Flight {flight_number} is already scheduled on date {flight_date_val} (Unique constraint violation)!"
        elif "CHECK" in err_msg.upper():
            return False, f"Database Check Constraint Failed: {err_msg}"
        elif "FOREIGN KEY" in err_msg.upper():
            return False, f"Referential Integrity Error: Invalid foreign key reference (Airline, Aircraft or Airport)!"
        return False, f"Database Error: {err_msg}"
    finally:
        cur.close()
        conn.close()


def update_flight_status(
    flight_id: int,
    new_status: str,
    actual_departure: Optional[str] = None,
    actual_arrival: Optional[str] = None
) -> Tuple[bool, str]:
    """Updates operational flight lifecycle state."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE FLIGHT 
            SET current_status = ?,
                actual_departure = COALESCE(?, actual_departure),
                actual_arrival = COALESCE(?, actual_arrival)
            WHERE flight_id = ?
        """, (new_status, actual_departure, actual_arrival, flight_id))
        conn.commit()
        return True, f"Flight ID {flight_id} transitioned to {new_status}."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def apply_departure_delay(flight_id: int, delay_minutes: int) -> Tuple[bool, str]:
    """Applies a departure delay in minutes to a flight."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT scheduled_departure FROM FLIGHT WHERE flight_id = ?", (flight_id,))
        row = cur.fetchone()
        if not row:
            return False, f"Flight ID {flight_id} not found."

        sched_dep = datetime.fromisoformat(str(row["scheduled_departure"]))
        new_actual = (sched_dep + timedelta(minutes=delay_minutes)).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("""
            UPDATE FLIGHT 
            SET actual_departure = ?,
                current_status = CASE 
                    WHEN current_status = 'SCHEDULED' THEN 'BOARDING' 
                    ELSE current_status 
                END
            WHERE flight_id = ?
        """, (new_actual, flight_id))
        conn.commit()
        return True, f"Logged {delay_minutes}-minute delay for Flight ID {flight_id} (Actual dep: {new_actual})."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def cancel_or_delete_flight(flight_id: int, hard_delete: bool = False) -> Tuple[bool, str]:
    """Cancels or permanently removes a flight."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if hard_delete:
            cur.execute("DELETE FROM FLIGHT WHERE flight_id = ?", (flight_id,))
            conn.commit()
            return True, f"Flight ID {flight_id} permanently deleted from records."
        else:
            cur.execute("UPDATE FLIGHT SET current_status = 'CANCELLED' WHERE flight_id = ?", (flight_id,))
            conn.commit()
            return True, f"Flight ID {flight_id} status updated to CANCELLED."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def get_otp_analytics() -> List[Dict[str, Any]]:
    """Member 2 Query 1: On-Time Performance (OTP) by Carrier."""
    conn = get_connection()
    cur = conn.cursor()
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
                             ((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 86400.0) <= 900 
                        THEN 1 ELSE 0 
                    END) AS on_time_count,
                    SUM(CASE 
                        WHEN f.actual_departure IS NOT NULL AND 
                             ((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 86400.0) > 900
                        THEN 1 ELSE 0 
                    END) AS delayed_count,
                    CASE 
                        WHEN COUNT(f.actual_departure) > 0 
                        THEN ROUND(
                            (SUM(CASE WHEN ((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 86400.0) <= 900 THEN 1.0 ELSE 0.0 END) / COUNT(f.actual_departure)) * 100.0, 
                            2
                        )
                        ELSE 0.00 
                    END AS otp_rate_percentage,
                    ROUND(
                        COALESCE(AVG(CASE WHEN f.actual_departure > f.scheduled_departure THEN ((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440.0) ELSE 0 END), 0.0), 
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
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_route_density_analytics(min_flights: int = 1) -> List[Dict[str, Any]]:
    """Member 2 Query 2: Route Density & Bottleneck Analysis."""
    q = f"""
    SELECT 
        f.origin_airport,
        orig.city AS origin_city,
        f.dest_airport,
        dest.city AS dest_city,
        COUNT(f.flight_id) AS scheduled_movements,
        COUNT(DISTINCT f.airline_id) AS competing_airlines,
        ROUND(AVG(((julianday(f.scheduled_arrival) - julianday(f.scheduled_departure)) * 1440.0)), 0) AS scheduled_duration_minutes
    FROM FLIGHT f
    JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
    JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
    GROUP BY f.origin_airport, orig.city, f.dest_airport, dest.city
    HAVING COUNT(f.flight_id) >= {min_flights}
    ORDER BY scheduled_movements DESC;
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(q)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_excessive_delays(threshold_minutes: int = 30) -> List[Dict[str, Any]]:
    """Member 2 Query 3: Correlated Subquery finding excessive flight delays."""
    q = f"""
    SELECT 
        f.flight_number,
        al.airline_name,
        f.origin_airport,
        f.dest_airport,
        f.scheduled_departure,
        f.actual_departure,
        ROUND(((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440.0)) AS delay_minutes,
        f.current_status
    FROM FLIGHT f
    JOIN AIRLINE al ON f.airline_id = al.airline_id
    WHERE f.actual_departure IS NOT NULL
      AND f.flight_id IN (
          SELECT sub_f.flight_id 
          FROM FLIGHT sub_f 
          WHERE ((julianday(sub_f.actual_departure) - julianday(sub_f.scheduled_departure)) * 1440.0) >= {threshold_minutes}
      )
    ORDER BY delay_minutes DESC;
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(q)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def get_fleet_capacity_report() -> List[Dict[str, Any]]:
    """Member 2 Query 4: Aircraft Fleet Utilization vs Industry Average (Scalar Subquery)."""
    conn = get_connection()
    cur = conn.cursor()
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
            ORDER BY ac.passenger_capacity DESC;
        """
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def execute_raw_sql(sql_query: str) -> Tuple[bool, Any]:
    """Executes arbitrary SQL query for demonstration purposes."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query)
        if sql_query.strip().upper().startswith("SELECT"):
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            return True, {"columns": columns, "data": [dict(zip(columns, row)) for row in rows]}
        else:
            conn.commit()
            return True, f"Statement executed successfully. Rows affected: {cur.rowcount}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------------------------
# MEMBER 3 OPERATIONS API (ATC Tower, En-Route Radar & Safety Audit)
# ----------------------------------------------------------------------------

def get_active_flights() -> pd.DataFrame:
    """Retrieves all flights eligible to receive ATC clearances."""
    conn = get_connection()
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


def get_all_flights() -> pd.DataFrame:
    """Retrieves all flights for incident and clearance dropdowns."""
    conn = get_connection()
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


def get_controllers() -> pd.DataFrame:
    """Retrieves all licensed ATC controllers with shift and certification info."""
    conn = get_connection()
    query = """
    SELECT 
        c.controller_id, 
        c.first_name || ' ' || c.last_name AS full_name,
        c.license_number,
        c.certification_level,
        c.shift_start || ' - ' || c.shift_end AS shift_hours,
        COALESCE(sec.sector_name, 'Surface / Tower') AS sector_name
    FROM CONTROLLER c
    LEFT JOIN AIRSPACE_SECTOR sec ON c.assigned_sector_id = sec.sector_id
    ORDER BY c.certification_level, c.last_name;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def issue_clearance(
    flight_id: int,
    controller_id: int,
    clearance_type: str,
    runway_id: Optional[int] = None,
    altitude: Optional[int] = None,
    heading: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Issues an ATC clearance with transactional safety.
    Triggers runway collision check (aborts if occupied/closed) and auto-transitions
    the runway to OCCUPIED and flight state to AIRBORNE or LANDED.
    """
    conn = get_connection()
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
        return True, f"Clearance #{last_id} issued successfully ({clearance_type})."
    except Exception as e:
        conn.rollback()
        err_msg = str(e)
        if "Runway Safety Violation" in err_msg or "ABORT" in err_msg:
            return False, "⚠️ SAFETY INTERLOCK TRIGGERED: Runway is currently OCCUPIED or CLOSED! Clearance rejected to prevent runway incursion."
        return False, f"Database Error: {err_msg}"
    finally:
        cur.close()
        conn.close()


def file_incident(flight_id: Optional[int], reported_by: int, incident_type: str, severity: str, description: str) -> Tuple[bool, str]:
    """Files a safety incident report into INCIDENT_LOG."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO INCIDENT_LOG (
                flight_id, reported_by, incident_type, severity, incident_time, description
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?);
        """, (flight_id if flight_id else None, reported_by, incident_type, severity, description))
        conn.commit()
        last_id = cur.lastrowid
        return True, f"Incident Report #{last_id} filed successfully under Severity {severity}."
    except Exception as e:
        conn.rollback()
        return False, f"Failed to log incident: {str(e)}"
    finally:
        cur.close()
        conn.close()


def get_recent_clearances(limit: int = 50) -> pd.DataFrame:
    """Retrieves chronological black-box clearance audit trail."""
    conn = get_connection()
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


def get_incident_logs() -> pd.DataFrame:
    """Retrieves all filed safety incident anomaly reports."""
    conn = get_connection()
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


def get_controller_workload() -> pd.DataFrame:
    """Member 3 Query 2: Controller clearance workload via GROUP BY and HAVING."""
    conn = get_connection()
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


def get_airborne_radar_flights() -> pd.DataFrame:
    """Member 3 Query 1: Airborne flights with dynamic clearance subquery."""
    conn = get_connection()
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


def get_sector_utilization() -> pd.DataFrame:
    """Member 3 Query 4: Airspace Sector Capacity and Controller Count."""
    conn = get_connection()
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


def get_database_status() -> Dict[str, Any]:
    """Returns overall system connectivity and record counts across all 11 tables."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        counts = {}
        tables = [
            "AIRPORT", "RUNWAY", "GATE", "GATE_ASSIGNMENT",
            "AIRLINE", "AIRCRAFT", "FLIGHT",
            "AIRSPACE_SECTOR", "CONTROLLER", "FLIGHT_CLEARANCE", "INCIDENT_LOG"
        ]
        for tbl in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                counts[tbl] = cur.fetchone()[0]
            except Exception:
                counts[tbl] = 0
        return {
            "engine": "PostgreSQL (Enterprise)" if USE_POSTGRES else "SQLite (Local Zero-Config Standalone)",
            "db_path": PG_URL if USE_POSTGRES else DB_PATH,
            "connected": True,
            "counts": counts
        }
    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------------------------
# SQLITE DDL, CONSTRAINTS, TRIGGERS & SEED SCRIPT
# ----------------------------------------------------------------------------

_UNIFIED_SQLITE_DDL_AND_SEED = """
PRAGMA foreign_keys = OFF;

-- Drop tables in reverse dependency order if reseeding
DROP TABLE IF EXISTS INCIDENT_LOG;
DROP TABLE IF EXISTS FLIGHT_CLEARANCE;
DROP TABLE IF EXISTS GATE_ASSIGNMENT;
DROP TABLE IF EXISTS FLIGHT;
DROP TABLE IF EXISTS CONTROLLER;
DROP TABLE IF EXISTS AIRSPACE_SECTOR;
DROP TABLE IF EXISTS GATE;
DROP TABLE IF EXISTS RUNWAY;
DROP TABLE IF EXISTS AIRCRAFT;
DROP TABLE IF EXISTS AIRLINE;
DROP TABLE IF EXISTS AIRPORT;

-- 1. AIRPORT
CREATE TABLE IF NOT EXISTS AIRPORT (
    airport_code VARCHAR(4) PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,
    name VARCHAR(100),
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    elevation_ft INT CHECK (elevation_ft >= -1500 AND elevation_ft <= 15000)
);

-- 2. AIRLINE
CREATE TABLE IF NOT EXISTS AIRLINE (
    airline_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    callsign_prefix VARCHAR(10) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50) NOT NULL DEFAULT 'India',
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

-- 3. AIRCRAFT
CREATE TABLE IF NOT EXISTS AIRCRAFT (
    aircraft_reg_no VARCHAR(12) PRIMARY KEY,
    model VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    passenger_capacity INT NOT NULL CHECK (passenger_capacity > 0),
    max_altitude_ft INT NOT NULL CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000),
    cruising_speed_knots INT NOT NULL CHECK (cruising_speed_knots > 0),
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE CASCADE
);

-- 4. RUNWAY
CREATE TABLE IF NOT EXISTS RUNWAY (
    runway_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    runway_designator VARCHAR(10) NOT NULL,
    length_meters INT NOT NULL CHECK (length_meters >= 1000),
    length_m INT,
    width_m INT DEFAULT 45,
    surface_type VARCHAR(30) NOT NULL DEFAULT 'ASPHALT',
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED')),
    UNIQUE (airport_code, runway_designator)
);

-- 5. GATE
CREATE TABLE IF NOT EXISTS GATE (
    gate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    terminal_number VARCHAR(10) NOT NULL,
    terminal VARCHAR(10),
    gate_number VARCHAR(10) NOT NULL,
    gate_category VARCHAR(20) NOT NULL DEFAULT 'DOMESTIC'
        CHECK (gate_category IN ('DOMESTIC', 'INTERNATIONAL')),
    gate_type VARCHAR(20) DEFAULT 'CONTACT',
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    UNIQUE (airport_code, terminal_number, gate_number)
);

-- 6. AIRSPACE_SECTOR
CREATE TABLE IF NOT EXISTS AIRSPACE_SECTOR (
    sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name VARCHAR(50) NOT NULL UNIQUE,
    floor_altitude_ft INT NOT NULL CHECK (floor_altitude_ft >= 0),
    ceiling_altitude_ft INT NOT NULL CHECK (ceiling_altitude_ft > floor_altitude_ft),
    max_capacity INT NOT NULL CHECK (max_capacity > 0)
);

-- 7. CONTROLLER
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

-- 8. FLIGHT
CREATE TABLE IF NOT EXISTS FLIGHT (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number VARCHAR(10) NOT NULL,
    flight_date DATE NOT NULL,
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE RESTRICT,
    aircraft_reg_no VARCHAR(12) NOT NULL REFERENCES AIRCRAFT(aircraft_reg_no) ON DELETE RESTRICT,
    origin_airport VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE RESTRICT,
    dest_airport VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE RESTRICT,
    destination_airport VARCHAR(4),
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,
    actual_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    current_status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
        CHECK (current_status IN ('SCHEDULED', 'BOARDING', 'TAXIING', 'AIRBORNE', 'LANDED', 'DIVERTED', 'CANCELLED')),
    assigned_runway_id INT REFERENCES RUNWAY(runway_id),
    UNIQUE (flight_number, flight_date),
    CHECK (origin_airport <> dest_airport),
    CHECK (scheduled_arrival > scheduled_departure)
);

-- 9. GATE_ASSIGNMENT
CREATE TABLE IF NOT EXISTS GATE_ASSIGNMENT (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
    gate_id INT NOT NULL REFERENCES GATE(gate_id) ON DELETE CASCADE,
    assigned_from TIMESTAMP NOT NULL,
    assigned_until TIMESTAMP NOT NULL,
    assignment_type VARCHAR(10) NOT NULL DEFAULT 'DEPARTURE' CHECK (assignment_type IN ('ARRIVAL', 'DEPARTURE')),
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED' CHECK (status IN ('CONFIRMED', 'OCCUPIED', 'COMPLETED', 'CANCELLED')),
    CHECK (assigned_until > assigned_from)
);

-- 10. FLIGHT_CLEARANCE
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

-- 11. INCIDENT_LOG
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

-- ----------------------------------------------------------------------------
-- AUTOMATED TRIGGERS (SAFETY & BUSINESS RULES)
-- ----------------------------------------------------------------------------

-- Trigger 1 (Member 1): Gate Double Booking Prevention
DROP TRIGGER IF EXISTS trg_prevent_gate_double_booking;
CREATE TRIGGER trg_prevent_gate_double_booking
BEFORE INSERT ON GATE_ASSIGNMENT
BEGIN
    SELECT CASE 
        WHEN (
            SELECT COUNT(*) FROM GATE_ASSIGNMENT 
            WHERE gate_id = NEW.gate_id 
              AND status != 'CANCELLED' 
              AND (NEW.assigned_from < assigned_until AND NEW.assigned_until > assigned_from)
        ) > 0 THEN
            RAISE(ABORT, 'GATE_DOUBLE_BOOKED: Gate already has an active assignment overlapping with the requested window!')
    END;
END;

-- Trigger 2 (Member 3): Runway Safety Collision Interlock
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

-- Trigger 3 (Member 3): Runway State Auto-Update to OCCUPIED
DROP TRIGGER IF EXISTS trg_runway_clearance_occupy;
CREATE TRIGGER trg_runway_clearance_occupy
AFTER INSERT ON FLIGHT_CLEARANCE
WHEN NEW.runway_id IS NOT NULL AND NEW.clearance_type IN ('TAKEOFF', 'LANDING')
BEGIN
    UPDATE RUNWAY SET current_status = 'OCCUPIED' WHERE runway_id = NEW.runway_id;
END;

-- Trigger 4 (Member 3 -> Member 2): Takeoff Clearance Auto-Transitions Flight to AIRBORNE
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

-- Trigger 5 (Member 3 -> Member 2): Landing Clearance Auto-Transitions Flight to LANDED
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

-- ----------------------------------------------------------------------------
-- RELATIONAL VIEWS
-- ----------------------------------------------------------------------------

-- View 1: Member 1 Ground Dashboard View
DROP VIEW IF EXISTS view_airport_ground_dashboard;
CREATE VIEW view_airport_ground_dashboard AS
SELECT 
    a.airport_code,
    a.airport_name,
    a.city,
    a.elevation_ft,
    COUNT(DISTINCT r.runway_id) AS total_runways,
    COUNT(DISTINCT CASE WHEN r.current_status = 'AVAILABLE' THEN r.runway_id END) AS available_runways,
    COUNT(DISTINCT CASE WHEN r.current_status = 'OCCUPIED' THEN r.runway_id END) AS occupied_runways,
    COUNT(DISTINCT CASE WHEN r.current_status = 'CLOSED' THEN r.runway_id END) AS closed_runways,
    COUNT(DISTINCT g.gate_id) AS total_gates,
    COUNT(DISTINCT CASE WHEN g.current_status = 'AVAILABLE' THEN g.gate_id END) AS free_gates
FROM AIRPORT a
LEFT JOIN RUNWAY r ON a.airport_code = r.airport_code
LEFT JOIN GATE g ON a.airport_code = g.airport_code
GROUP BY a.airport_code, a.airport_name, a.city, a.elevation_ft;

-- View 2: Member 2 Flight Dispatch Board
DROP VIEW IF EXISTS VIEW_FLIGHT_DISPATCH_BOARD;
CREATE VIEW VIEW_FLIGHT_DISPATCH_BOARD AS
SELECT 
    f.flight_id, f.flight_number, f.flight_date,
    al.airline_name, al.callsign_prefix,
    f.aircraft_reg_no, ac.model AS aircraft_model, ac.passenger_capacity,
    f.origin_airport, orig.city AS origin_city,
    f.dest_airport, dest.city AS dest_city,
    f.scheduled_departure, f.scheduled_arrival,
    f.actual_departure, f.actual_arrival,
    f.current_status,
    CASE 
        WHEN f.actual_departure IS NOT NULL AND f.actual_departure > f.scheduled_departure 
            THEN ROUND(((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440.0))
        ELSE 0
    END AS departure_delay_minutes
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
JOIN AIRPORT dest ON f.dest_airport = dest.airport_code;

-- ----------------------------------------------------------------------------
-- COMPREHENSIVE SEED DATA (12 INDIAN AIRPORTS, FLEET, FLIGHTS, CONTROLLERS)
-- ----------------------------------------------------------------------------

-- 12 Indian Hubs
INSERT OR REPLACE INTO AIRPORT (airport_code, airport_name, name, city, country, latitude, longitude, elevation_ft) VALUES
('DEL', 'Indira Gandhi International Airport', 'Indira Gandhi International Airport', 'New Delhi', 'India', 28.556200, 77.100000, 777),
('BOM', 'Chhatrapati Shivaji Maharaj Int Airport', 'Chhatrapati Shivaji Maharaj Int Airport', 'Mumbai', 'India', 19.089600, 72.865600, 39),
('BLR', 'Kempegowda International Airport', 'Kempegowda International Airport', 'Bengaluru', 'India', 13.198600, 77.706600, 3000),
('MAA', 'Chennai International Airport', 'Chennai International Airport', 'Chennai', 'India', 12.994100, 80.170900, 52),
('HYD', 'Rajiv Gandhi International Airport', 'Rajiv Gandhi International Airport', 'Hyderabad', 'India', 17.240300, 78.429400, 2024),
('CCU', 'Netaji Subhash Chandra Bose Int Airport', 'Netaji Subhash Chandra Bose Int Airport', 'Kolkata', 'India', 22.654700, 88.446700, 16),
('AMD', 'Sardar Vallabhbhai Patel Int Airport', 'Sardar Vallabhbhai Patel Int Airport', 'Ahmedabad', 'India', 23.077200, 72.634700, 189),
('COK', 'Cochin International Airport', 'Cochin International Airport', 'Kochi', 'India', 10.152000, 76.401900, 30),
('PNQ', 'Pune Airport', 'Pune Airport', 'Pune', 'India', 18.582200, 73.919700, 1942),
('GOX', 'Manohar International Airport', 'Manohar International Airport', 'Mopa, Goa', 'India', 15.766700, 73.866700, 558),
('JAI', 'Jaipur International Airport', 'Jaipur International Airport', 'Jaipur', 'India', 26.824200, 75.812200, 1263),
('GAU', 'Lokpriya Gopinath Bordoloi Int Airport', 'Lokpriya Gopinath Bordoloi Int Airport', 'Guwahati', 'India', 26.106100, 91.585900, 162);

-- Airlines
INSERT OR REPLACE INTO AIRLINE (airline_id, airline_name, callsign_prefix, country_of_origin, contact_email) VALUES
(1, 'IndiGo', 'IGO', 'India', 'operations@goindigo.in'),
(2, 'Air India', 'AIC', 'India', 'dispatch@airindia.com'),
(3, 'SpiceJet', 'SEJ', 'India', 'ops@spicejet.com'),
(4, 'Akasa Air', 'AKJ', 'India', 'atc@akasaair.com'),
(5, 'Vistara', 'VTI', 'India', 'ops@airvistara.com');

-- Aircraft Fleet
INSERT OR REPLACE INTO AIRCRAFT (aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft, cruising_speed_knots, airline_id) VALUES
('VT-ISN', 'A320neo', 'Airbus', 186, 39000, 450, 1),
('VT-IFP', 'A321neo', 'Airbus', 222, 39000, 460, 1),
('VT-EXF', 'B787-8 Dreamliner', 'Boeing', 256, 43000, 490, 2),
('VT-CIO', 'A320neo', 'Airbus', 180, 39000, 450, 2),
('VT-SLA', 'B737-800', 'Boeing', 189, 41000, 455, 3),
('VT-YAA', 'B737-MAX8', 'Boeing', 189, 41000, 460, 4),
('VT-TNC', 'A320neo', 'Airbus', 180, 39000, 450, 5);

-- Runways
INSERT OR REPLACE INTO RUNWAY (runway_id, airport_code, runway_designator, length_meters, length_m, width_m, surface_type, current_status) VALUES
(1, 'DEL', '09/27', 3810, 3810, 45, 'ASPHALT', 'AVAILABLE'),
(2, 'DEL', '10/28', 3810, 3810, 45, 'ASPHALT', 'AVAILABLE'),
(3, 'DEL', '11/29', 4430, 4430, 60, 'ASPHALT', 'AVAILABLE'),
(4, 'BOM', '09/27', 3445, 3445, 45, 'ASPHALT', 'AVAILABLE'),
(5, 'BOM', '14/32', 2925, 2925, 45, 'ASPHALT', 'AVAILABLE'),
(6, 'MAA', '07/25', 3658, 3658, 45, 'ASPHALT', 'AVAILABLE'),
(7, 'BLR', '09L/27R', 4000, 4000, 45, 'ASPHALT', 'AVAILABLE'),
(8, 'BLR', '09R/27L', 4000, 4000, 45, 'ASPHALT', 'AVAILABLE'),
(9, 'HYD', '09L/27R', 4260, 4260, 45, 'ASPHALT', 'AVAILABLE'),
(10, 'CCU', '01R/19L', 3627, 3627, 45, 'ASPHALT', 'AVAILABLE');

-- Gates
INSERT OR REPLACE INTO GATE (gate_id, airport_code, terminal_number, terminal, gate_number, gate_category, gate_type, current_status) VALUES
(1, 'DEL', 'T3', 'T3', '01A', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(2, 'DEL', 'T3', 'T3', '02B', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(3, 'DEL', 'T3', 'T3', '14A', 'INTERNATIONAL', 'CONTACT', 'AVAILABLE'),
(4, 'BOM', 'T2', 'T2', '45', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(5, 'BOM', 'T2', 'T2', '46', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(6, 'MAA', 'T1', 'T1', '04', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(7, 'BLR', 'T1', 'T1', '08', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(8, 'BLR', 'T2', 'T2', '21', 'INTERNATIONAL', 'CONTACT', 'AVAILABLE'),
(9, 'HYD', 'T1', 'T1', '12', 'DOMESTIC', 'CONTACT', 'AVAILABLE'),
(10, 'CCU', 'T1', 'T1', '05', 'DOMESTIC', 'CONTACT', 'AVAILABLE');

-- Airspace Sectors
INSERT OR REPLACE INTO AIRSPACE_SECTOR (sector_id, sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity) VALUES
(1, 'Delhi FIR - Northern Sector (VIDF-N)', 0, 46000, 60),
(2, 'Mumbai FIR - Western Oceanic & Inland (VABF)', 0, 46000, 55),
(3, 'Chennai FIR - Southern Peninsular (VOMF)', 0, 46000, 50),
(4, 'Kolkata FIR - Eastern & Bay of Bengal (VECF)', 0, 46000, 45),
(5, 'Delhi Terminal Radar Approach Area (DEL-TMA)', 0, 15000, 30),
(6, 'Mumbai Terminal Radar Approach Area (BOM-TMA)', 0, 15000, 28);

-- Controllers
INSERT OR REPLACE INTO CONTROLLER (controller_id, first_name, last_name, license_number, certification_level, shift_start, shift_end, assigned_sector_id) VALUES
(1, 'Vikram', 'Rathore', 'AAI-ATCO-1092', 'TOWER', '06:00:00', '14:00:00', 1),
(2, 'Ananya', 'Sharma', 'AAI-ATCO-2234', 'EN_ROUTE', '06:00:00', '14:00:00', 1),
(3, 'Karthik', 'Ramanathan', 'AAI-ATCO-3310', 'TOWER', '14:00:00', '22:00:00', 3),
(4, 'Siddharth', 'Nair', 'AAI-ATCO-4491', 'APPROACH', '14:00:00', '22:00:00', 3),
(5, 'Neha', 'Deshmukh', 'AAI-ATCO-5582', 'TOWER', '06:00:00', '14:00:00', 2),
(6, 'Rajesh', 'Verma', 'AAI-ATCO-6719', 'GROUND', '06:00:00', '14:00:00', 1),
(7, 'Pooja', 'Menon', 'AAI-ATCO-7840', 'EN_ROUTE', '14:00:00', '22:00:00', 2),
(8, 'Arjun', 'Mehta', 'AAI-ATCO-8901', 'APPROACH', '22:00:00', '06:00:00', 5);

-- Scheduled & Active Flights
INSERT OR REPLACE INTO FLIGHT (
    flight_id, flight_number, flight_date, airline_id, aircraft_reg_no,
    origin_airport, dest_airport, destination_airport,
    scheduled_departure, scheduled_arrival, actual_departure, actual_arrival, current_status, assigned_runway_id
) VALUES
(1, '6E-204', '2026-10-30', 1, 'VT-ISN', 'DEL', 'MAA', 'MAA', '2026-10-30 07:00:00', '2026-10-30 09:45:00', '2026-10-30 07:05:00', NULL, 'AIRBORNE', 1),
(2, 'AI-101', '2026-10-30', 2, 'VT-EXF', 'BOM', 'DEL', 'DEL', '2026-10-30 08:30:00', '2026-10-30 10:40:00', '2026-10-30 09:15:00', NULL, 'BOARDING', 4),
(3, '6E-532', '2026-10-30', 1, 'VT-IFP', 'BLR', 'DEL', 'DEL', '2026-10-30 09:15:00', '2026-10-30 12:00:00', NULL, NULL, 'SCHEDULED', 7),
(4, 'QP-1102', '2026-10-30', 4, 'VT-YAA', 'BOM', 'BLR', 'BLR', '2026-10-30 10:00:00', '2026-10-30 11:45:00', NULL, NULL, 'SCHEDULED', 5),
(5, 'SG-8169', '2026-10-30', 3, 'VT-SLA', 'DEL', 'AMD', 'AMD', '2026-10-30 11:00:00', '2026-10-30 12:35:00', NULL, NULL, 'SCHEDULED', 2),
(6, 'UK-820', '2026-10-30', 5, 'VT-TNC', 'DEL', 'BOM', 'BOM', '2026-10-30 12:30:00', '2026-10-30 14:40:00', NULL, NULL, 'SCHEDULED', 3);

-- Initial Gate Allocations
INSERT OR REPLACE INTO GATE_ASSIGNMENT (assignment_id, flight_id, gate_id, assigned_from, assigned_until, assignment_type, status) VALUES
(1, 1, 1, '2026-10-30 06:00:00', '2026-10-30 07:00:00', 'DEPARTURE', 'COMPLETED'),
(2, 2, 4, '2026-10-30 07:30:00', '2026-10-30 08:45:00', 'DEPARTURE', 'OCCUPIED'),
(3, 3, 7, '2026-10-30 08:15:00', '2026-10-30 09:15:00', 'DEPARTURE', 'CONFIRMED'),
(4, 5, 2, '2026-10-30 10:00:00', '2026-10-30 11:00:00', 'DEPARTURE', 'CONFIRMED');

-- Initial Clearances
INSERT OR REPLACE INTO FLIGHT_CLEARANCE (clearance_id, flight_id, controller_id, runway_id, clearance_type, issued_timestamp, assigned_altitude_ft, assigned_heading_deg) VALUES
(1, 1, 6, NULL, 'PUSHBACK', '2026-10-30 06:45:00', NULL, NULL),
(2, 1, 6, NULL, 'TAXI', '2026-10-30 06:55:00', NULL, NULL),
(3, 1, 1, 1, 'TAKEOFF', '2026-10-30 07:05:00', 5000, 90),
(4, 1, 2, NULL, 'ALTITUDE_CHANGE', '2026-10-30 07:20:00', 36000, 175),
(5, 1, 2, NULL, 'HEADING', '2026-10-30 07:35:00', 36000, 180),
(6, 2, 5, NULL, 'PUSHBACK', '2026-10-30 08:15:00', NULL, NULL);

-- Initial Safety Incident Reports
INSERT OR REPLACE INTO INCIDENT_LOG (incident_id, flight_id, reported_by, incident_type, severity, incident_time, description) VALUES
(1, 1, 2, 'ALTITUDE_BUST', 'MEDIUM', '2026-10-30 07:25:00', 'Aircraft climbed 400 ft above FL360 due to turbulence over Bhopal FIR sector.'),
(2, NULL, 1, 'BIRD_STRIKE', 'LOW', '2026-10-30 05:40:00', 'Bird scaring team deployed at threshold of Runway 10/28 DEL; flock scattered.'),
(3, 2, 5, 'RUNWAY_INCURSION', 'HIGH', '2026-10-30 08:25:00', 'Tug vehicle crossed intermediate holding point near Taxiway Mike BOM.');

PRAGMA foreign_keys = ON;
"""
