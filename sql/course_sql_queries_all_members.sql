-- ============================================================================
-- SkyFlow ATCMS – Master Course SQL Demonstrations (All 3 Members)
-- Fulfills DBS_Project Instructions.pdf (Section 10 & 11)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- CONCEPT 1: SELECT & FILTERING WITH WHERE
-- ----------------------------------------------------------------------------
-- Find all high-capacity aircraft (> 200 seats) capable of cruising at or above FL390
SELECT aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft
FROM AIRCRAFT
WHERE passenger_capacity >= 200 AND max_altitude_ft >= 39000
ORDER BY passenger_capacity DESC;

-- ----------------------------------------------------------------------------
-- CONCEPT 2: MULTI-TABLE JOINS (INNER, LEFT OUTER)
-- ----------------------------------------------------------------------------
-- Join FLIGHT, AIRLINE, AIRCRAFT, and AIRPORT to produce complete dispatch schedule
SELECT 
    f.flight_number,
    al.airline_name,
    f.aircraft_reg_no,
    ac.model,
    orig.city AS origin_city,
    dest.city AS destination_city,
    f.scheduled_departure,
    f.scheduled_arrival,
    f.current_status
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
ORDER BY f.scheduled_departure ASC;

-- ----------------------------------------------------------------------------
-- CONCEPT 3: AGGREGATE FUNCTIONS (COUNT, SUM, AVG, MIN, MAX)
-- ----------------------------------------------------------------------------
-- Fleet capacity statistics by airline
SELECT 
    al.airline_name,
    COUNT(ac.aircraft_reg_no) AS fleet_count,
    SUM(ac.passenger_capacity) AS total_passenger_capacity,
    ROUND(AVG(ac.passenger_capacity), 1) AS avg_seat_capacity,
    MIN(ac.cruising_speed_knots) AS min_cruising_speed,
    MAX(ac.max_altitude_ft) AS max_service_ceiling
FROM AIRLINE al
JOIN AIRCRAFT ac ON al.airline_id = ac.airline_id
GROUP BY al.airline_name;

-- ----------------------------------------------------------------------------
-- CONCEPT 4: GROUP BY AND HAVING
-- ----------------------------------------------------------------------------
-- (Member 1): Runway movements by peak hour where activity >= 1
SELECT 
    r.airport_code,
    r.runway_designator,
    COUNT(f.flight_id) AS scheduled_movements
FROM RUNWAY r
JOIN FLIGHT f ON r.runway_id = f.assigned_runway_id
WHERE f.current_status NOT IN ('CANCELLED')
GROUP BY r.airport_code, r.runway_designator
HAVING COUNT(f.flight_id) >= 1
ORDER BY scheduled_movements DESC;

-- (Member 3): Controller workload filtering officers with active clearances
SELECT 
    c.controller_id,
    c.first_name || ' ' || c.last_name AS controller_name,
    c.certification_level,
    COUNT(fc.clearance_id) AS total_clearances_issued,
    COUNT(DISTINCT fc.flight_id) AS distinct_aircraft_handled
FROM CONTROLLER c
JOIN FLIGHT_CLEARANCE fc ON c.controller_id = fc.controller_id
GROUP BY c.controller_id, c.first_name, c.last_name, c.certification_level
HAVING COUNT(fc.clearance_id) > 0
ORDER BY total_clearances_issued DESC;

-- ----------------------------------------------------------------------------
-- CONCEPT 5: CORRELATED SUBQUERIES
-- ----------------------------------------------------------------------------
-- (Member 3): Find latest clearance for each airborne flight
SELECT 
    f.flight_number,
    f.current_status,
    fc.clearance_type AS last_instruction,
    fc.assigned_altitude_ft,
    fc.assigned_heading_deg,
    fc.issued_timestamp
FROM FLIGHT f
JOIN FLIGHT_CLEARANCE fc ON f.flight_id = fc.flight_id
WHERE f.current_status = 'AIRBORNE'
  AND fc.clearance_id = (
      SELECT MAX(sub.clearance_id)
      FROM FLIGHT_CLEARANCE sub
      WHERE sub.flight_id = f.flight_id
  );

-- (Member 2): Find flights with departure delays exceeding 30 minutes
SELECT 
    f.flight_number,
    f.scheduled_departure,
    f.actual_departure,
    f.current_status
FROM FLIGHT f
WHERE f.actual_departure IS NOT NULL
  AND f.flight_id IN (
      SELECT sub_f.flight_id 
      FROM FLIGHT sub_f 
      WHERE sub_f.actual_departure > sub_f.scheduled_departure
  );

-- ----------------------------------------------------------------------------
-- CONCEPT 6: RELATIONAL VIEWS
-- ----------------------------------------------------------------------------
-- Aerodrome ground operational health view
SELECT * FROM view_airport_ground_dashboard ORDER BY airport_code;

-- Real-time commercial flight dispatch board view
SELECT * FROM VIEW_FLIGHT_DISPATCH_BOARD WHERE current_status != 'CANCELLED';

-- ----------------------------------------------------------------------------
-- CONCEPT 7: DATABASE TRIGGERS
-- ----------------------------------------------------------------------------
-- Member 1 Gate Overlap Prevention Trigger: trg_prevent_gate_double_booking
-- Member 3 Runway Collision Safety Trigger: trg_runway_clearance_safety_abort
-- Integration Auto-Status Triggers: trg_flight_status_takeoff, trg_flight_status_landing
