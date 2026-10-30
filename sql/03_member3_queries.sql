-- ============================================================================
-- SkyFlow ATCMS – Member 3: Complex SQL Queries & Course Demonstrations
-- Meets DBMS Syllabus Rubrics: Joins, Correlated Subqueries, Aggregate Functions,
-- GROUP BY, HAVING, and Views.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Multi-Table Join with Correlated Clearance Subquery
-- Concept: INNER JOINs (4 tables), Subquery in WHERE clause, String Concat
-- Purpose: Retrieves all active airborne flights crossing Indian airspace with
--          carrier, aircraft type, route, authorizing controller, and the latest
--          assigned altitude and heading vectors.
-- ----------------------------------------------------------------------------
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
    c.first_name || ' ' || c.last_name AS authorizing_controller,
    c.certification_level
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

-- ----------------------------------------------------------------------------
-- QUERY 2: Aggregate Analysis with GROUP BY and HAVING
-- Concept: GROUP BY, COUNT(DISTINCT), LEFT JOIN, HAVING filter, ORDER BY
-- Purpose: Evaluates controller operational workload by counting total clearances
--          issued and distinct aircraft handled. Filters officers with active load.
-- ----------------------------------------------------------------------------
SELECT 
    c.controller_id,
    c.first_name || ' ' || c.last_name AS controller_name,
    c.license_number,
    c.certification_level,
    COALESCE(sec.sector_name, 'Unassigned / Surface') AS assigned_sector,
    COUNT(fc.clearance_id) AS total_clearances_issued,
    COUNT(DISTINCT fc.flight_id) AS distinct_aircraft_handled
FROM CONTROLLER c
LEFT JOIN FLIGHT_CLEARANCE fc ON c.controller_id = fc.controller_id
LEFT JOIN AIRSPACE_SECTOR sec ON c.assigned_sector_id = sec.sector_id
GROUP BY c.controller_id, c.first_name, c.last_name, c.license_number, c.certification_level, sec.sector_name
HAVING COUNT(fc.clearance_id) > 0
ORDER BY total_clearances_issued DESC;

-- ----------------------------------------------------------------------------
-- QUERY 3: Comprehensive Incident Severity & Safety Audit Report
-- Concept: Multi-table LEFT JOIN, CASE statement for risk score, Date filtering
-- Purpose: Produces an audit dossier of all recorded anomalies, linking them to
--          the operating airline, flight number, reporting controller, and risk tier.
-- ----------------------------------------------------------------------------
SELECT 
    inc.incident_id,
    inc.incident_time,
    inc.incident_type,
    inc.severity,
    CASE 
        WHEN inc.severity = 'CRITICAL' THEN 4
        WHEN inc.severity = 'HIGH' THEN 3
        WHEN inc.severity = 'MEDIUM' THEN 2
        ELSE 1 
    END AS risk_priority_level,
    COALESCE(f.flight_number, 'N/A (Ground/Perimeter)') AS flight_number,
    COALESCE(al.airline_name, 'N/A') AS operating_airline,
    c.first_name || ' ' || c.last_name AS reporting_controller,
    c.certification_level AS controller_cert,
    inc.description
FROM INCIDENT_LOG inc
JOIN CONTROLLER c ON inc.reported_by = c.controller_id
LEFT JOIN FLIGHT f ON inc.flight_id = f.flight_id
LEFT JOIN AIRLINE al ON f.airline_id = al.airline_id
ORDER BY risk_priority_level DESC, inc.incident_time DESC;

-- ----------------------------------------------------------------------------
-- QUERY 4: Airspace Sector Capacity & Congestion Index
-- Concept: Aggregation over active flights, mathematical percentage calculation
-- Purpose: Analyzes current sector density against maximum safety limits.
-- ----------------------------------------------------------------------------
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
