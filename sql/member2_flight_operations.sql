-- ============================================================================
-- SkyFlow ATCMS - MEMBER 2: Advanced SQL Queries & Relational Views
-- Domain: Commercial Fleet & Flight Operations Subsystem
-- Database: PostgreSQL / ANSI SQL Compatible
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SECTION 1: RELATIONAL VIEWS (MEMBER 2 DOMAIN)
-- ----------------------------------------------------------------------------

-- View 1: Real-Time Flight Dispatch Schedule Board
-- Combines flights, airline details, aircraft specs, and airport hub metadata
DROP VIEW IF EXISTS VIEW_FLIGHT_DISPATCH_BOARD CASCADE;
CREATE VIEW VIEW_FLIGHT_DISPATCH_BOARD AS
SELECT 
    f.flight_id,
    f.flight_number,
    f.flight_date,
    al.airline_name,
    al.callsign_prefix,
    f.aircraft_reg_no,
    ac.model AS aircraft_model,
    ac.passenger_capacity,
    f.origin_airport,
    orig.airport_name AS origin_airport_name,
    orig.city AS origin_city,
    f.dest_airport,
    dest.airport_name AS dest_airport_name,
    dest.city AS dest_city,
    f.scheduled_departure,
    f.scheduled_arrival,
    f.actual_departure,
    f.actual_arrival,
    f.current_status,
    CASE 
        WHEN f.actual_departure IS NOT NULL AND f.actual_departure > f.scheduled_departure 
            THEN ROUND(EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60)
        ELSE 0
    END AS departure_delay_minutes
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
JOIN AIRPORT dest ON f.dest_airport = dest.airport_code;


-- View 2: Airline Fleet & Capacity Summary View
-- Demonstrates multi-table aggregation, SUM, AVG, MIN, MAX
DROP VIEW IF EXISTS VIEW_AIRLINE_FLEET_SUMMARY CASCADE;
CREATE VIEW VIEW_AIRLINE_FLEET_SUMMARY AS
SELECT 
    al.airline_id,
    al.airline_name,
    al.callsign_prefix,
    COUNT(ac.aircraft_reg_no) AS total_fleet_size,
    COALESCE(SUM(ac.passenger_capacity), 0) AS total_seat_capacity,
    ROUND(COALESCE(AVG(ac.passenger_capacity), 0), 1) AS avg_seat_capacity,
    COALESCE(MAX(ac.max_altitude_ft), 0) AS max_service_ceiling_ft,
    ROUND(COALESCE(AVG(ac.cruising_speed_knots), 0), 1) AS avg_cruising_speed_knots
FROM AIRLINE al
LEFT JOIN AIRCRAFT ac ON al.airline_id = ac.airline_id
GROUP BY al.airline_id, al.airline_name, al.callsign_prefix;


-- View 3: Carrier On-Time Performance (OTP) Metrics View
-- Demonstrates conditional aggregation (SUM with CASE), date arithmetic, and percentage calculations
DROP VIEW IF EXISTS VIEW_CARRIER_OTP_ANALYTICS CASCADE;
CREATE VIEW VIEW_CARRIER_OTP_ANALYTICS AS
SELECT 
    al.airline_id,
    al.airline_name,
    al.callsign_prefix,
    COUNT(f.flight_id) AS total_scheduled_flights,
    COUNT(f.actual_departure) AS total_departed_flights,
    SUM(CASE WHEN f.actual_departure IS NOT NULL AND f.actual_departure <= f.scheduled_departure + INTERVAL '15 minutes' THEN 1 ELSE 0 END) AS on_time_departures,
    SUM(CASE WHEN f.actual_departure IS NOT NULL AND f.actual_departure > f.scheduled_departure + INTERVAL '15 minutes' THEN 1 ELSE 0 END) AS delayed_departures,
    CASE 
        WHEN COUNT(f.actual_departure) > 0 
        THEN ROUND((SUM(CASE WHEN f.actual_departure <= f.scheduled_departure + INTERVAL '15 minutes' THEN 1.0 ELSE 0.0 END) / COUNT(f.actual_departure)) * 100.0, 2)
        ELSE 0.00
    END AS on_time_percentage,
    ROUND(COALESCE(AVG(CASE WHEN f.actual_departure > f.scheduled_departure THEN EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60.0 ELSE 0 END), 0.0), 1) AS avg_delay_minutes
FROM AIRLINE al
LEFT JOIN FLIGHT f ON al.airline_id = f.airline_id
GROUP BY al.airline_id, al.airline_name, al.callsign_prefix;


-- ----------------------------------------------------------------------------
-- SECTION 2: COMPLEX & SYLLABUS-DEMONSTRATIVE SQL QUERIES
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- QUERY 1: Carrier On-Time Performance (OTP) Report
-- DBMS Concepts: Multi-table JOIN, CASE expression, Aggregation (COUNT, SUM, AVG),
--                 Arithmetic operations, GROUP BY, ORDER BY
-- Purpose: Evaluates airline operational punctuality using DGCA 15-minute buffer.
-- ----------------------------------------------------------------------------
SELECT 
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
JOIN FLIGHT f ON al.airline_id = f.airline_id
GROUP BY al.airline_name, al.callsign_prefix
ORDER BY otp_rate_percentage DESC, al.airline_name ASC;


-- ----------------------------------------------------------------------------
-- QUERY 2: High-Density Airspace Corridors & Bottleneck Analysis
-- DBMS Concepts: GROUP BY, HAVING filter, Aggregate functions (COUNT, MIN, MAX),
--                 String concatenation, Nested sorting
-- Purpose: Pinpoints congested domestic route pairs with high traffic volume.
-- ----------------------------------------------------------------------------
SELECT 
    f.origin_airport || ' -> ' || f.dest_airport AS route_corridor,
    orig.city AS origin_city,
    dest.city AS dest_city,
    COUNT(f.flight_id) AS total_scheduled_flights,
    COUNT(DISTINCT f.airline_id) AS competing_airlines_count,
    COUNT(DISTINCT f.aircraft_reg_no) AS distinct_aircraft_assigned,
    MIN(f.scheduled_departure) AS earliest_departure_today,
    MAX(f.scheduled_departure) AS latest_departure_today
FROM FLIGHT f
JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
GROUP BY f.origin_airport, f.dest_airport, orig.city, dest.city
HAVING COUNT(f.flight_id) >= 2
ORDER BY total_scheduled_flights DESC, route_corridor ASC;


-- ----------------------------------------------------------------------------
-- QUERY 3: Excessive Delays Investigation (Correlated Subquery)
-- DBMS Concepts: Correlated Subquery with WHERE EXISTS / IN, Timestamp arithmetic,
--                 Multi-table JOINs, Filtering with threshold
-- Purpose: Identifies flight legs delayed by > 30 minutes for safety/audit review.
-- ----------------------------------------------------------------------------
SELECT 
    f.flight_id,
    f.flight_number,
    f.flight_date,
    al.airline_name,
    al.contact_email AS dispatch_alert_email,
    f.aircraft_reg_no,
    ac.model AS aircraft_type,
    f.origin_airport || ' -> ' || f.dest_airport AS corridor,
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
      WHERE sub_f.actual_departure > (sub_f.scheduled_departure + INTERVAL '30 minutes')
  )
ORDER BY delay_minutes DESC;


-- ----------------------------------------------------------------------------
-- QUERY 4: Aircraft Fleet Utilization vs. Industry Capacity Benchmark
-- DBMS Concepts: Scalar Subquery in WHERE clause, Arithmetic comparison,
--                 Multi-table JOIN, String formatting
-- Purpose: Identifies wide-body/high-capacity aircraft that exceed average fleet capacity.
-- ----------------------------------------------------------------------------
SELECT 
    ac.aircraft_reg_no,
    ac.model,
    ac.manufacturer,
    ac.passenger_capacity,
    al.airline_name,
    ROUND((ac.passenger_capacity - (SELECT AVG(passenger_capacity) FROM AIRCRAFT)), 1) AS seats_above_fleet_average,
    COUNT(f.flight_id) AS total_assigned_flights
FROM AIRCRAFT ac
JOIN AIRLINE al ON ac.airline_id = al.airline_id
LEFT JOIN FLIGHT f ON ac.aircraft_reg_no = f.aircraft_reg_no
WHERE ac.passenger_capacity > (
    SELECT AVG(passenger_capacity) FROM AIRCRAFT
)
GROUP BY ac.aircraft_reg_no, ac.model, ac.manufacturer, ac.passenger_capacity, al.airline_name
ORDER BY ac.passenger_capacity DESC;


-- ----------------------------------------------------------------------------
-- QUERY 5: Active Airborne Flight Vectors with Airframe Specs
-- DBMS Concepts: Inner JOINs, State filtering, Multi-column sorting
-- Purpose: Real-time radar feeds showing airborne aircraft specs and flight progress.
-- ----------------------------------------------------------------------------
SELECT 
    f.flight_number,
    al.airline_name,
    al.callsign_prefix,
    f.aircraft_reg_no,
    ac.model,
    ac.cruising_speed_knots,
    ac.max_altitude_ft,
    f.origin_airport || ' -> ' || f.dest_airport AS active_route,
    f.scheduled_departure,
    f.actual_departure,
    f.current_status
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
WHERE f.current_status = 'AIRBORNE'
ORDER BY f.actual_departure ASC;


-- ----------------------------------------------------------------------------
-- SECTION 3: DATA MANIPULATION (INSERT, UPDATE, DELETE) PATTERNS
-- ----------------------------------------------------------------------------

-- Pattern 1: Schedule a New Flight Leg (INSERT with validation)
-- Demonstrates parameterized insertion respecting table check constraints
-- INSERT INTO FLIGHT (flight_number, flight_date, airline_id, aircraft_reg_no, origin_airport, dest_airport, scheduled_departure, scheduled_arrival, current_status)
-- VALUES ('6E-901', '2026-11-01', 1, 'VT-ISN', 'DEL', 'BOM', '2026-11-01 16:30:00', '2026-11-01 18:45:00', 'SCHEDULED');

-- Pattern 2: Update Flight Operational Status & Actual Departure (UPDATE)
-- Demonstrates state progression in operational workflow
-- UPDATE FLIGHT 
-- SET current_status = 'AIRBORNE', actual_departure = CURRENT_TIMESTAMP 
-- WHERE flight_id = :flight_id AND current_status = 'TAXIING';

-- Pattern 3: Log Departure Delay (UPDATE)
-- Demonstrates updating schedules during ground hold or ATC flow control
-- UPDATE FLIGHT 
-- SET actual_departure = scheduled_departure + (:delay_minutes || ' minutes')::INTERVAL,
--     current_status = 'BOARDING'
-- WHERE flight_id = :flight_id;

-- Pattern 4: Cancel Flight Leg (DELETE or Soft-cancel UPDATE)
-- Demonstrates safe removal of uncommenced flights
-- DELETE FROM FLIGHT 
-- WHERE flight_id = :flight_id AND current_status = 'SCHEDULED';
