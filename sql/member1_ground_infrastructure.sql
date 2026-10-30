-- =====================================================================
-- SkyFlow Database System
-- Deliverable 4: Member 1 SQL Queries, Views, and DML Operations
-- =====================================================================

-- =====================================================================
-- 1. ANALYTICAL QUERY 1: Runway Congestion
-- Concept: Movements per runway per peak hour
-- Uses: JOIN (runway + flight) + date_trunc('hour') + GROUP BY + HAVING
-- =====================================================================
SELECT 
    r.airport_code,
    r.runway_designator,
    date_trunc('hour', f.scheduled_departure) AS peak_hour_window,
    COUNT(f.flight_id) AS total_scheduled_movements,
    r.current_status AS runway_status
FROM runway r
JOIN flight f ON r.runway_id = f.assigned_runway_id
WHERE f.current_status NOT IN ('CANCELLED', 'DIVERTED')
GROUP BY 
    r.airport_code, 
    r.runway_designator, 
    date_trunc('hour', f.scheduled_departure),
    r.current_status
HAVING COUNT(f.flight_id) >= 2
ORDER BY total_scheduled_movements DESC, peak_hour_window ASC;

-- =====================================================================
-- 2. ANALYTICAL QUERY 2: Gate Occupancy and Turnaround Analysis
-- Concept: Identifies the busiest gates by total assignments and calculates
--          the average turnaround duration in minutes using subqueries & aggregates.
-- Uses: Subquery, EXTRACT(EPOCH), AVG, COUNT, GROUP BY
-- =====================================================================
SELECT 
    g.airport_code,
    g.terminal,
    g.gate_number,
    g.gate_type,
    stats.total_flights_handled,
    ROUND(stats.avg_turnaround_minutes::numeric, 1) AS avg_turnaround_mins,
    stats.min_turnaround_minutes,
    stats.max_turnaround_minutes
FROM gate g
JOIN (
    SELECT 
        gate_id,
        COUNT(assignment_id) AS total_flights_handled,
        AVG(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS avg_turnaround_minutes,
        MIN(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS min_turnaround_minutes,
        MAX(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS max_turnaround_minutes
    FROM gate_assignment
    WHERE status IN ('COMPLETED', 'OCCUPIED', 'CONFIRMED')
    GROUP BY gate_id
) stats ON g.gate_id = stats.gate_id
WHERE stats.total_flights_handled >= 1
ORDER BY stats.total_flights_handled DESC, avg_turnaround_mins DESC;

-- =====================================================================
-- 3. VIEW: Airport Ground Operational Dashboard
-- Concept: Pre-aggregates physical operational health for each airport:
--          Total runways, Available runways, Closed runways,
--          Total gates, and Currently available free gates.
-- Uses: CREATE VIEW, LEFT JOIN, conditional COUNT(CASE WHEN ...)
-- =====================================================================
CREATE OR REPLACE VIEW view_airport_ground_dashboard AS
SELECT 
    a.airport_code,
    a.name AS airport_name,
    a.city,
    a.elevation_ft,
    COUNT(DISTINCT r.runway_id) AS total_runways,
    COUNT(DISTINCT CASE WHEN r.current_status = 'AVAILABLE' THEN r.runway_id END) AS available_runways,
    COUNT(DISTINCT CASE WHEN r.current_status = 'OCCUPIED' THEN r.runway_id END) AS occupied_runways,
    COUNT(DISTINCT CASE WHEN r.current_status = 'CLOSED' THEN r.runway_id END) AS closed_runways,
    COUNT(DISTINCT g.gate_id) AS total_gates,
    COUNT(DISTINCT CASE WHEN g.current_status = 'AVAILABLE' THEN g.gate_id END) AS free_gates
FROM airport a
LEFT JOIN runway r ON a.airport_code = r.airport_code
LEFT JOIN gate g ON a.airport_code = g.airport_code
GROUP BY a.airport_code, a.name, a.city, a.elevation_ft;

-- Querying the view:
-- SELECT * FROM view_airport_ground_dashboard ORDER BY airport_code;

-- =====================================================================
-- 4. DML OPERATIONS EXAMPLES (INSERT, UPDATE, DELETE)
-- =====================================================================

-- 4a. INSERT: Assign a newly scheduled flight to Gate 2 at DEL
INSERT INTO gate_assignment (gate_id, flight_id, assigned_from, assigned_until, status)
VALUES (2, 6, '2026-10-30 11:30:00', '2026-10-30 12:45:00', 'CONFIRMED')
RETURNING assignment_id, gate_id, flight_id, status;

-- 4b. UPDATE: Change runway status due to inspection or obstruction
UPDATE runway
SET current_status = 'CLOSED'
WHERE airport_code = 'DEL' AND runway_designator = '09/27';

-- 4c. DELETE / CANCEL: Cancel or release an assignment safely
DELETE FROM gate_assignment
WHERE assignment_id = 40;
-- Alternatively, soft delete / state transition:
-- UPDATE gate_assignment SET status = 'CANCELLED' WHERE assignment_id = 40;
