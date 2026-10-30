-- ============================================================================
-- SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)
-- Database: PostgreSQL
-- Focus: Indian Domestic Airspace & Airport Network (12 Hubs)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CLEANUP & SCHEMA INITIALIZATION
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS VIEW_AIRPORT_RADAR_DISPLAY CASCADE;
DROP TRIGGER IF EXISTS trg_runway_clearance_safety ON FLIGHT_CLEARANCE CASCADE;
DROP FUNCTION IF EXISTS trg_fn_enforce_runway_safety() CASCADE;

DROP TABLE IF EXISTS INCIDENT_LOG CASCADE;
DROP TABLE IF EXISTS FLIGHT_CLEARANCE CASCADE;
DROP TABLE IF EXISTS GATE_ASSIGNMENT CASCADE;
DROP TABLE IF EXISTS FLIGHT CASCADE;
DROP TABLE IF EXISTS CONTROLLER CASCADE;
DROP TABLE IF EXISTS AIRSPACE_SECTOR CASCADE;
DROP TABLE IF EXISTS GATE CASCADE;
DROP TABLE IF EXISTS RUNWAY CASCADE;
DROP TABLE IF EXISTS AIRCRAFT CASCADE;
DROP TABLE IF EXISTS AIRLINE CASCADE;
DROP TABLE IF EXISTS AIRPORT CASCADE;

-- ----------------------------------------------------------------------------
-- 2. DDL TABLE DEFINITIONS WITH INTEGRITY CONSTRAINTS
-- ----------------------------------------------------------------------------

-- Master Hubs (Airports)
CREATE TABLE AIRPORT (
    airport_code VARCHAR(4) PRIMARY KEY, -- ICAO/IATA code (e.g., 'DEL', 'MAA')
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    elevation_ft INT CHECK (elevation_ft >= -1500 AND elevation_ft <= 15000)
);

-- Commercial Operating Carriers
CREATE TABLE AIRLINE (
    airline_id SERIAL PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    callsign_prefix VARCHAR(10) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50) NOT NULL DEFAULT 'India',
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

-- Aircraft Fleet Registry
CREATE TABLE AIRCRAFT (
    aircraft_reg_no VARCHAR(12) PRIMARY KEY, -- DGCA tail number (e.g., 'VT-ISN')
    model VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    passenger_capacity INT CHECK (passenger_capacity > 0),
    max_altitude_ft INT CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000),
    cruising_speed_knots INT CHECK (cruising_speed_knots > 0),
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE CASCADE
);

-- Physical Runways
CREATE TABLE RUNWAY (
    runway_id SERIAL PRIMARY KEY,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    runway_designator VARCHAR(10) NOT NULL, -- e.g., '09/27', '07/25'
    length_meters INT NOT NULL CHECK (length_meters >= 1000),
    surface_type VARCHAR(30) DEFAULT 'ASPHALT',
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED')),
    UNIQUE (airport_code, runway_designator)
);

-- Terminal Gates
CREATE TABLE GATE (
    gate_id SERIAL PRIMARY KEY,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    terminal_number VARCHAR(10) NOT NULL, -- e.g., 'T1', 'T2', 'T3'
    gate_number VARCHAR(10) NOT NULL, -- e.g., '14A', '04'
    gate_category VARCHAR(20) NOT NULL DEFAULT 'DOMESTIC'
        CHECK (gate_category IN ('DOMESTIC', 'INTERNATIONAL')),
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    UNIQUE (airport_code, terminal_number, gate_number)
);

-- Airspace Sectors (Indian FIRs)
CREATE TABLE AIRSPACE_SECTOR (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(50) NOT NULL UNIQUE,
    floor_altitude_ft INT NOT NULL CHECK (floor_altitude_ft >= 0),
    ceiling_altitude_ft INT NOT NULL CHECK (ceiling_altitude_ft > floor_altitude_ft),
    max_capacity INT NOT NULL CHECK (max_capacity > 0)
);

-- Licensed Controllers
CREATE TABLE CONTROLLER (
    controller_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    license_number VARCHAR(30) NOT NULL UNIQUE,
    certification_level VARCHAR(20) NOT NULL 
        CHECK (certification_level IN ('GROUND', 'TOWER', 'APPROACH', 'EN_ROUTE')),
    shift_start TIME NOT NULL,
    shift_end TIME NOT NULL,
    assigned_sector_id INT REFERENCES AIRSPACE_SECTOR(sector_id) ON DELETE SET NULL
);

-- Scheduled & Active Flights
CREATE TABLE FLIGHT (
    flight_id SERIAL PRIMARY KEY,
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

-- Gate Turnaround Allocation
CREATE TABLE GATE_ASSIGNMENT (
    assignment_id SERIAL PRIMARY KEY,
    flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
    gate_id INT NOT NULL REFERENCES GATE(gate_id) ON DELETE CASCADE,
    assigned_from TIMESTAMP NOT NULL,
    assigned_until TIMESTAMP NOT NULL,
    assignment_type VARCHAR(10) NOT NULL CHECK (assignment_type IN ('ARRIVAL', 'DEPARTURE')),
    CHECK (assigned_until > assigned_from)
);

-- ATC Clearances (Black-box Ledger)
CREATE TABLE FLIGHT_CLEARANCE (
    clearance_id SERIAL PRIMARY KEY,
    flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
    controller_id INT NOT NULL REFERENCES CONTROLLER(controller_id),
    runway_id INT REFERENCES RUNWAY(runway_id),
    clearance_type VARCHAR(30) NOT NULL 
        CHECK (clearance_type IN ('PUSHBACK', 'TAXI', 'TAKEOFF', 'ALTITUDE_CHANGE', 'HEADING', 'LANDING')),
    issued_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_altitude_ft INT CHECK (assigned_altitude_ft >= 0 AND assigned_altitude_ft <= 60000),
    assigned_heading_deg INT CHECK (assigned_heading_deg >= 0 AND assigned_heading_deg <= 360)
);

-- Safety & Anomaly Audit Log
CREATE TABLE INCIDENT_LOG (
    incident_id SERIAL PRIMARY KEY,
    flight_id INT REFERENCES FLIGHT(flight_id) ON DELETE SET NULL,
    reported_by INT NOT NULL REFERENCES CONTROLLER(controller_id),
    incident_type VARCHAR(30) NOT NULL 
        CHECK (incident_type IN ('NEAR_MISS', 'RUNWAY_INCURSION', 'ALTITUDE_BUST', 'BIRD_STRIKE', 'WEATHER_DIVERT')),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    incident_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- Performance Indexes
CREATE INDEX idx_flight_dates ON FLIGHT(flight_date, origin_airport, dest_airport);
CREATE INDEX idx_flight_status ON FLIGHT(current_status);
CREATE INDEX idx_clearance_flight ON FLIGHT_CLEARANCE(flight_id);
CREATE INDEX idx_gate_time ON GATE_ASSIGNMENT(assigned_from, assigned_until);

-- ----------------------------------------------------------------------------
-- 3. ADVANCED LOGIC: TRIGGER & RADAR VIEW
-- ----------------------------------------------------------------------------

-- Trigger: Prevent Takeoff/Landing on Occupied/Closed Runways
CREATE OR REPLACE FUNCTION trg_fn_enforce_runway_safety()
RETURNS TRIGGER AS $$
DECLARE
    r_status VARCHAR(20);
BEGIN
    IF NEW.runway_id IS NOT NULL AND NEW.clearance_type IN ('TAKEOFF', 'LANDING') THEN
        SELECT current_status INTO r_status 
        FROM RUNWAY 
        WHERE runway_id = NEW.runway_id;

        IF r_status <> 'AVAILABLE' THEN
            RAISE EXCEPTION 'Runway Safety Violation: Runway ID % is currently %!', NEW.runway_id, r_status;
        END IF;

        UPDATE RUNWAY 
        SET current_status = 'OCCUPIED' 
        WHERE runway_id = NEW.runway_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_runway_clearance_safety
BEFORE INSERT ON FLIGHT_CLEARANCE
FOR EACH ROW
EXECUTE FUNCTION trg_fn_enforce_runway_safety();

-- Relational View for Application Dashboard
CREATE OR REPLACE VIEW VIEW_AIRPORT_RADAR_DISPLAY AS
SELECT 
    f.flight_id,
    f.flight_number,
    f.flight_date,
    al.airline_name,
    al.callsign_prefix,
    f.aircraft_reg_no,
    ac.model AS aircraft_model,
    f.origin_airport,
    f.dest_airport,
    f.scheduled_departure,
    f.scheduled_arrival,
    f.actual_departure,
    f.current_status AS flight_status,
    g.terminal_number || '-' || g.gate_number AS assigned_gate,
    r.runway_designator AS active_runway
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
LEFT JOIN GATE_ASSIGNMENT ga ON f.flight_id = ga.flight_id
LEFT JOIN GATE g ON ga.gate_id = g.gate_id
LEFT JOIN FLIGHT_CLEARANCE fc ON f.flight_id = fc.flight_id 
     AND fc.clearance_id = (
         SELECT MAX(sub_fc.clearance_id) 
         FROM FLIGHT_CLEARANCE sub_fc 
         WHERE sub_fc.flight_id = f.flight_id
     )
LEFT JOIN RUNWAY r ON fc.runway_id = r.runway_id;

-- ----------------------------------------------------------------------------
-- 4. REALISTIC SEED DATA (INDIAN DOMESTIC NETWORK)
-- ----------------------------------------------------------------------------

-- 12 Indian Hubs
INSERT INTO AIRPORT (airport_code, airport_name, city, country, latitude, longitude, elevation_ft) VALUES
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

-- Airlines
INSERT INTO AIRLINE (airline_name, callsign_prefix, country_of_origin, contact_email) VALUES
('IndiGo', 'IGO', 'India', 'operations@goindigo.in'),
('Air India', 'AIC', 'India', 'dispatch@airindia.com'),
('SpiceJet', 'SEJ', 'India', 'ops@spicejet.com'),
('Akasa Air', 'AKJ', 'India', 'atc@akasaair.com');

-- Aircraft Fleet
INSERT INTO AIRCRAFT (aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft, cruising_speed_knots, airline_id) VALUES
('VT-ISN', 'A320neo', 'Airbus', 186, 39000, 450, 1),
('VT-IFP', 'A321neo', 'Airbus', 222, 39000, 460, 1),
('VT-EXF', 'B787-8 Dreamliner', 'Boeing', 256, 43000, 490, 2),
('VT-CIO', 'A320neo', 'Airbus', 180, 39000, 450, 2),
('VT-SLA', 'B737-800', 'Boeing', 189, 41000, 455, 3),
('VT-YAA', 'B737-MAX8', 'Boeing', 189, 41000, 460, 4);

-- FIR Airspace Sectors
INSERT INTO AIRSPACE_SECTOR (sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity) VALUES
('Delhi FIR (VIDF)', 0, 46000, 60),
('Mumbai FIR (VABF)', 0, 46000, 55),
('Chennai FIR (VOMF)', 0, 46000, 50),
('Kolkata FIR (VECF)', 0, 46000, 45);

-- Runways
INSERT INTO RUNWAY (airport_code, runway_designator, length_meters, current_status) VALUES
('DEL', '09/27', 3810, 'AVAILABLE'),
('DEL', '10/28', 3810, 'AVAILABLE'),
('DEL', '11/29', 4430, 'AVAILABLE'),
('BOM', '09/27', 3445, 'AVAILABLE'),
('BOM', '14/32', 2925, 'AVAILABLE'),
('MAA', '07/25', 3658, 'AVAILABLE'),
('MAA', '12/30', 2045, 'AVAILABLE'),
('BLR', '09L/27R', 4000, 'AVAILABLE'),
('BLR', '09R/27L', 4000, 'AVAILABLE');

-- Terminal Gates
INSERT INTO GATE (airport_code, terminal_number, gate_number, gate_category, current_status) VALUES
('DEL', 'T3', '01A', 'DOMESTIC', 'AVAILABLE'),
('DEL', 'T3', '02B', 'DOMESTIC', 'AVAILABLE'),
('DEL', 'T3', '14A', 'INTERNATIONAL', 'AVAILABLE'),
('BOM', 'T2', '45', 'DOMESTIC', 'AVAILABLE'),
('BOM', 'T2', '46', 'DOMESTIC', 'AVAILABLE'),
('MAA', 'T1', '04', 'DOMESTIC', 'AVAILABLE'),
('MAA', 'T4', '12', 'INTERNATIONAL', 'AVAILABLE'),
('BLR', 'T1', '08', 'DOMESTIC', 'AVAILABLE'),
('BLR', 'T2', '21', 'INTERNATIONAL', 'AVAILABLE');

-- Controllers
INSERT INTO CONTROLLER (first_name, last_name, license_number, certification_level, shift_start, shift_end, assigned_sector_id) VALUES
('Vikram', 'Rathore', 'AAI-ATCO-1092', 'TOWER', '06:00', '14:00', 1),
('Ananya', 'Sharma', 'AAI-ATCO-2234', 'EN_ROUTE', '06:00', '14:00', 1),
('Karthik', 'Ramanathan', 'AAI-ATCO-3310', 'TOWER', '14:00', '22:00', 3),
('Siddharth', 'Nair', 'AAI-ATCO-4491', 'APPROACH', '14:00', '22:00', 3),
('Neha', 'Deshmukh', 'AAI-ATCO-5582', 'TOWER', '06:00', '14:00', 2);

-- Scheduled Flights
INSERT INTO FLIGHT (flight_number, flight_date, airline_id, aircraft_reg_no, origin_airport, dest_airport, scheduled_departure, scheduled_arrival, actual_departure, current_status) VALUES
('6E-204', '2026-11-01', 1, 'VT-ISN', 'DEL', 'MAA', '2026-11-01 07:00:00', '2026-11-01 09:45:00', '2026-11-01 07:05:00', 'AIRBORNE'),
('AI-101', '2026-11-01', 2, 'VT-EXF', 'BOM', 'DEL', '2026-11-01 08:30:00', '2026-11-01 10:40:00', NULL, 'BOARDING'),
('6E-532', '2026-11-01', 1, 'VT-IFP', 'BLR', 'DEL', '2026-11-01 09:15:00', '2026-11-01 12:00:00', NULL, 'SCHEDULED'),
('QP-1102', '2026-11-01', 4, 'VT-YAA', 'BOM', 'BLR', '2026-11-01 10:00:00', '2026-11-01 11:45:00', NULL, 'SCHEDULED'),
('SG-8169', '2026-11-01', 3, 'VT-SLA', 'DEL', 'AMD', '2026-11-01 11:00:00', '2026-11-01 12:35:00', NULL, 'SCHEDULED');

-- Initial Gate Allocations
INSERT INTO GATE_ASSIGNMENT (flight_id, gate_id, assigned_from, assigned_until, assignment_type) VALUES
(1, 1, '2026-11-01 06:00:00', '2026-11-01 07:00:00', 'DEPARTURE'),
(2, 4, '2026-11-01 07:30:00', '2026-11-01 08:30:00', 'DEPARTURE');

-- Initial Clearances
INSERT INTO FLIGHT_CLEARANCE (flight_id, controller_id, runway_id, clearance_type, issued_timestamp, assigned_altitude_ft, assigned_heading_deg) VALUES
(1, 1, 1, 'TAKEOFF', '2026-11-01 07:02:00', 5000, 90),
(1, 2, NULL, 'ALTITUDE_CHANGE', '2026-11-01 07:20:00', 36000, 175);
