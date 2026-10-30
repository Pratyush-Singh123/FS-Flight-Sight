-- ============================================================================
-- SkyFlow ATCMS – Member 3: Realistic Seed Dataset
-- Indian FIR Sectors, Controllers, Clearance History & Incident Audit Logs
-- ============================================================================

-- 1. Airspace Sectors (Indian Flight Information Regions & En-Route Sectors)
INSERT INTO AIRSPACE_SECTOR (sector_id, sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity) VALUES
(1, 'Delhi FIR - Northern Sector (VIDF-N)', 0, 46000, 60),
(2, 'Mumbai FIR - Western Oceanic & Inland (VABF)', 0, 46000, 55),
(3, 'Chennai FIR - Southern Peninsular (VOMF)', 0, 46000, 50),
(4, 'Kolkata FIR - Eastern & Bay of Bengal (VECF)', 0, 46000, 45),
(5, 'Delhi Terminal Radar Approach Area (DEL-TMA)', 0, 15000, 30),
(6, 'Mumbai Terminal Radar Approach Area (BOM-TMA)', 0, 15000, 28)
ON CONFLICT (sector_id) DO UPDATE SET 
    sector_name = EXCLUDED.sector_name,
    max_capacity = EXCLUDED.max_capacity;

-- 2. Licensed Controllers (AAI DGCA Certified Officers)
INSERT INTO CONTROLLER (controller_id, first_name, last_name, license_number, certification_level, shift_start, shift_end, assigned_sector_id) VALUES
(1, 'Vikram', 'Rathore', 'AAI-ATCO-1092', 'TOWER', '06:00:00', '14:00:00', 1),
(2, 'Ananya', 'Sharma', 'AAI-ATCO-2234', 'EN_ROUTE', '06:00:00', '14:00:00', 1),
(3, 'Karthik', 'Ramanathan', 'AAI-ATCO-3310', 'TOWER', '14:00:00', '22:00:00', 3),
(4, 'Siddharth', 'Nair', 'AAI-ATCO-4491', 'APPROACH', '14:00:00', '22:00:00', 3),
(5, 'Neha', 'Deshmukh', 'AAI-ATCO-5582', 'TOWER', '06:00:00', '14:00:00', 2),
(6, 'Rajesh', 'Verma', 'AAI-ATCO-6719', 'GROUND', '06:00:00', '14:00:00', 1),
(7, 'Pooja', 'Menon', 'AAI-ATCO-7840', 'EN_ROUTE', '14:00:00', '22:00:00', 2),
(8, 'Arjun', 'Mehta', 'AAI-ATCO-8901', 'APPROACH', '22:00:00', '06:00:00', 5)
ON CONFLICT (controller_id) DO UPDATE SET 
    license_number = EXCLUDED.license_number,
    certification_level = EXCLUDED.certification_level;

-- 3. Realistic Initial Clearances
INSERT INTO FLIGHT_CLEARANCE (clearance_id, flight_id, controller_id, runway_id, clearance_type, issued_timestamp, assigned_altitude_ft, assigned_heading_deg) VALUES
(1, 1, 6, NULL, 'PUSHBACK', CURRENT_TIMESTAMP - INTERVAL '60 minutes', NULL, NULL),
(2, 1, 6, NULL, 'TAXI', CURRENT_TIMESTAMP - INTERVAL '50 minutes', NULL, NULL),
(3, 1, 1, 1, 'TAKEOFF', CURRENT_TIMESTAMP - INTERVAL '40 minutes', 5000, 90),
(4, 1, 2, NULL, 'ALTITUDE_CHANGE', CURRENT_TIMESTAMP - INTERVAL '25 minutes', 36000, 175),
(5, 1, 2, NULL, 'HEADING', CURRENT_TIMESTAMP - INTERVAL '10 minutes', 36000, 180),
(6, 2, 5, NULL, 'PUSHBACK', CURRENT_TIMESTAMP - INTERVAL '30 minutes', NULL, NULL),
(7, 2, 5, NULL, 'TAXI', CURRENT_TIMESTAMP - INTERVAL '20 minutes', NULL, NULL)
ON CONFLICT (clearance_id) DO NOTHING;

-- 4. Initial Safety Incidents & Anomaly Reports
INSERT INTO INCIDENT_LOG (incident_id, flight_id, reported_by, incident_type, severity, incident_time, description) VALUES
(1, 1, 2, 'ALTITUDE_BUST', 'MEDIUM', CURRENT_TIMESTAMP - INTERVAL '20 minutes', 'Aircraft momentarily climbed 400 ft above FL360 due to sudden clear-air turbulence over Bhopal corridor.'),
(2, NULL, 1, 'BIRD_STRIKE', 'LOW', CURRENT_TIMESTAMP - INTERVAL '3 hours', 'Inspection flock spotted near approach boundary of Runway 10/28 DEL; bird scaring patrol dispatched.'),
(3, 2, 5, 'RUNWAY_INCURSION', 'HIGH', CURRENT_TIMESTAMP - INTERVAL '1 day', 'Ground support vehicle strayed past perimeter holding line on Taxiway Echo near Runway 09 BOM.')
ON CONFLICT (incident_id) DO NOTHING;
