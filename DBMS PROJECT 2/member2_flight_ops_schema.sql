-- ============================================================================
-- SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)
-- MEMBER 2 SUBSYSTEM: Commercial Fleet & Flight Operations
-- Database: PostgreSQL / ANSI SQL
-- Tables Owned: AIRLINE, AIRCRAFT, FLIGHT
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DROP EXISTING MEMBER 2 TABLES (CASCADE TO CLEAN UP CONSTRAINTS)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS FLIGHT CASCADE;
DROP TABLE IF EXISTS AIRCRAFT CASCADE;
DROP TABLE IF EXISTS AIRLINE CASCADE;

-- ----------------------------------------------------------------------------
-- 2. DDL DEFINITIONS WITH DOMAIN & INTEGRITY CONSTRAINTS
-- ----------------------------------------------------------------------------

-- Entity 1: AIRLINE
-- Represents commercial and cargo carriers operating within Indian airspace
CREATE TABLE AIRLINE (
    airline_id SERIAL PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    callsign_prefix VARCHAR(10) NOT NULL UNIQUE, -- ICAO 3-letter telephony designator (e.g., 'IGO', 'AIC')
    country_of_origin VARCHAR(50) NOT NULL DEFAULT 'India',
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

-- Entity 2: AIRCRAFT
-- Individual physical airframe registered with DGCA (Directorate General of Civil Aviation)
CREATE TABLE AIRCRAFT (
    aircraft_reg_no VARCHAR(12) PRIMARY KEY, -- Indian civil tail registration (e.g., 'VT-ISN')
    model VARCHAR(50) NOT NULL,              -- e.g., 'A320neo', 'B787-8 Dreamliner'
    manufacturer VARCHAR(50) NOT NULL,       -- e.g., 'Airbus', 'Boeing'
    passenger_capacity INT NOT NULL CHECK (passenger_capacity > 0),
    max_altitude_ft INT NOT NULL CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000),
    cruising_speed_knots INT NOT NULL CHECK (cruising_speed_knots > 0),
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE CASCADE
);

-- Entity 3: FLIGHT
-- Specific flight leg scheduled on an operational calendar date
CREATE TABLE FLIGHT (
    flight_id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL, -- Commercial flight identifier (e.g., '6E-204')
    flight_date DATE NOT NULL,
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE RESTRICT,
    aircraft_reg_no VARCHAR(12) NOT NULL REFERENCES AIRCRAFT(aircraft_reg_no) ON DELETE RESTRICT,
    origin_airport VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE RESTRICT,
    dest_airport VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE RESTRICT,
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival TIMESTAMP NOT NULL,
    actual_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    current_status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
        CHECK (current_status IN ('SCHEDULED', 'BOARDING', 'TAXIING', 'AIRBORNE', 'LANDED', 'DIVERTED', 'CANCELLED')),
    
    -- Table-level Integrity Constraints
    CONSTRAINT uq_flight_number_date UNIQUE (flight_number, flight_date),
    CONSTRAINT chk_flight_airports_distinct CHECK (origin_airport <> dest_airport),
    CONSTRAINT chk_flight_schedule_chronology CHECK (scheduled_arrival > scheduled_departure)
);

-- ----------------------------------------------------------------------------
-- 3. PERFORMANCE INDEXES (OPTIMIZING DISPATCH & FILTER PATHS)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_flight_dates ON FLIGHT(flight_date, origin_airport, dest_airport);
CREATE INDEX idx_flight_status ON FLIGHT(current_status);
CREATE INDEX idx_flight_carrier ON FLIGHT(airline_id);
CREATE INDEX idx_flight_aircraft ON FLIGHT(aircraft_reg_no);
CREATE INDEX idx_aircraft_carrier ON AIRCRAFT(airline_id);

-- ----------------------------------------------------------------------------
-- 4. REALISTIC SEED DATA (MEMBER 2 SCOPE: INDIAN FLEET & SCHEDULED FLIGHTS)
-- ----------------------------------------------------------------------------

-- Registered Indian Carriers
INSERT INTO AIRLINE (airline_name, callsign_prefix, country_of_origin, contact_email) VALUES
('IndiGo', 'IGO', 'India', 'operations@goindigo.in'),
('Air India', 'AIC', 'India', 'dispatch@airindia.com'),
('SpiceJet', 'SEJ', 'India', 'ops@spicejet.com'),
('Akasa Air', 'AKJ', 'India', 'atc@akasaair.com'),
('Vistara', 'VTI', 'India', 'dispatch@airvistara.com'),
('AIX Connect', 'IAD', 'India', 'ops@aixconnect.in');

-- Commercial Aircraft Fleet (DGCA Registry with Indian 'VT-' tail numbers)
INSERT INTO AIRCRAFT (aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft, cruising_speed_knots, airline_id) VALUES
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

-- Scheduled & Active Domestic Flights across Major Indian Corridors
INSERT INTO FLIGHT (flight_number, flight_date, airline_id, aircraft_reg_no, origin_airport, dest_airport, scheduled_departure, scheduled_arrival, actual_departure, actual_arrival, current_status) VALUES
-- On-time flight (Airborne)
('6E-204', '2026-11-01', 1, 'VT-ISN', 'DEL', 'MAA', '2026-11-01 07:00:00', '2026-11-01 09:45:00', '2026-11-01 07:05:00', NULL, 'AIRBORNE'),

-- Boarding flight (slight delay)
('AI-101', '2026-11-01', 2, 'VT-EXF', 'BOM', 'DEL', '2026-11-01 08:30:00', '2026-11-01 10:40:00', NULL, NULL, 'BOARDING'),

-- Scheduled departure (Delhi - Bengaluru)
('6E-532', '2026-11-01', 1, 'VT-IFP', 'BLR', 'DEL', '2026-11-01 09:15:00', '2026-11-01 12:00:00', NULL, NULL, 'SCHEDULED'),

-- Scheduled departure (Mumbai - Bengaluru)
('QP-1102', '2026-11-01', 4, 'VT-YAA', 'BOM', 'BLR', '2026-11-01 10:00:00', '2026-11-01 11:45:00', NULL, NULL, 'SCHEDULED'),

-- Scheduled departure (Delhi - Ahmedabad)
('SG-8169', '2026-11-01', 3, 'VT-SLA', 'DEL', 'AMD', '2026-11-01 11:00:00', '2026-11-01 12:35:00', NULL, NULL, 'SCHEDULED'),

-- Completed On-Time Flight (Landed)
('UK-871', '2026-11-01', 5, 'VT-TVA', 'DEL', 'BOM', '2026-11-01 06:00:00', '2026-11-01 08:10:00', '2026-11-01 06:03:00', '2026-11-01 08:08:00', 'LANDED'),

-- Significantly Delayed Flight (Delayed > 30 minutes, departed 42 mins late)
('AI-624', '2026-11-01', 2, 'VT-CIO', 'DEL', 'HYD', '2026-11-01 07:30:00', '2026-11-01 09:40:00', '2026-11-01 08:12:00', '2026-11-01 10:18:00', 'LANDED'),

-- High-density Golden Triangle Route (BOM -> DEL)
('6E-5011', '2026-11-01', 1, 'VT-IMR', 'BOM', 'DEL', '2026-11-01 12:00:00', '2026-11-01 14:15:00', NULL, NULL, 'SCHEDULED'),

-- High-density Corridor Flight (DEL -> BOM)
('AI-805', '2026-11-01', 2, 'VT-ALQ', 'DEL', 'BOM', '2026-11-01 14:00:00', '2026-11-01 16:15:00', NULL, NULL, 'SCHEDULED'),

-- Goa Tourist Route
('QP-1314', '2026-11-01', 4, 'VT-YAE', 'BOM', 'GOX', '2026-11-01 13:30:00', '2026-11-01 14:45:00', NULL, NULL, 'SCHEDULED'),

-- Kolkata Route
('6E-212', '2026-11-01', 1, 'VT-ISN', 'DEL', 'CCU', '2026-11-01 15:00:00', '2026-11-01 17:10:00', NULL, NULL, 'SCHEDULED'),

-- South Corridor (Bengaluru -> Chennai)
('I5-982', '2026-11-01', 6, 'VT-IXC', 'BLR', 'MAA', '2026-11-01 08:00:00', '2026-11-01 08:55:00', '2026-11-01 08:02:00', '2026-11-01 08:54:00', 'LANDED'),

-- Severe Delay flight (> 45 min delay)
('SG-103', '2026-11-01', 3, 'VT-SGZ', 'DEL', 'PNQ', '2026-11-01 06:45:00', '2026-11-01 08:50:00', '2026-11-01 07:35:00', '2026-11-01 09:38:00', 'LANDED'),

-- Taxiing Flight
('UK-993', '2026-11-01', 5, 'VT-TTB', 'DEL', 'BLR', '2026-11-01 08:45:00', '2026-11-01 11:30:00', NULL, NULL, 'TAXIING');
