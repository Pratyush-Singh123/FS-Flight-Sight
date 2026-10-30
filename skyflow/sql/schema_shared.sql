-- =====================================================================
-- SkyFlow Database System
-- Master Shared Schema: schema_shared.sql
-- All table definitions (empty) with PKs, FKs, CHECK, and UNIQUE constraints
-- Follows all Frozen Decisions: snake_case, surrogate PKs, standard status values
-- =====================================================================

-- Drop tables in reverse dependency order if needed during reset
DROP TABLE IF EXISTS incident_log CASCADE;
DROP TABLE IF EXISTS flight_clearance CASCADE;
DROP TABLE IF EXISTS controller CASCADE;
DROP TABLE IF EXISTS airspace_sector CASCADE;
DROP TABLE IF EXISTS gate_assignment CASCADE;
DROP TABLE IF EXISTS flight CASCADE;
DROP TABLE IF EXISTS aircraft CASCADE;
DROP TABLE IF EXISTS airline CASCADE;
DROP TABLE IF EXISTS gate CASCADE;
DROP TABLE IF EXISTS runway CASCADE;
DROP TABLE IF EXISTS airport CASCADE;

-- =====================================================================
-- MEMBER 1 TABLES: Ground Infrastructure & Terminal Movement
-- =====================================================================

-- 1. AIRPORT (Master Facility Entity)
CREATE TABLE airport (
    airport_code    CHAR(3) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    elevation_ft    INTEGER NOT NULL CHECK (elevation_ft >= -100 AND elevation_ft <= 15000),
    latitude        NUMERIC(9, 6) NOT NULL CHECK (latitude BETWEEN -90.0 AND 90.0),
    longitude       NUMERIC(9, 6) NOT NULL CHECK (longitude BETWEEN -180.0 AND 180.0)
);

-- 2. RUNWAY (Landing and Takeoff Strips)
CREATE TABLE runway (
    runway_id           SERIAL PRIMARY KEY,
    airport_code        CHAR(3) NOT NULL REFERENCES airport(airport_code) ON DELETE CASCADE,
    runway_designator   VARCHAR(10) NOT NULL, -- e.g. '09/27', '11R/29L'
    length_m            INTEGER NOT NULL CHECK (length_m > 500 AND length_m < 6000), -- Meters
    width_m             INTEGER NOT NULL CHECK (width_m >= 15 AND width_m <= 100),
    surface_type        VARCHAR(30) DEFAULT 'ASPHALT',
    current_status      VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
                        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED')),
    CONSTRAINT uq_airport_runway UNIQUE (airport_code, runway_designator)
);

-- 3. GATE (Terminal Aircraft Parking Positions)
CREATE TABLE gate (
    gate_id         SERIAL PRIMARY KEY,
    airport_code    CHAR(3) NOT NULL REFERENCES airport(airport_code) ON DELETE CASCADE,
    terminal        VARCHAR(20) NOT NULL, -- e.g. 'T1', 'T2', 'T3'
    gate_number     VARCHAR(10) NOT NULL, -- e.g. 'G12', '14A'
    gate_type       VARCHAR(20) NOT NULL DEFAULT 'CONTACT'
                    CHECK (gate_type IN ('CONTACT', 'REMOTE')),
    current_status  VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
                    CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    CONSTRAINT uq_airport_terminal_gate UNIQUE (airport_code, terminal, gate_number)
);

-- =====================================================================
-- MEMBER 2 TABLES (Shared Stubs/Dependencies): Fleet & Flight Operations
-- =====================================================================

CREATE TABLE airline (
    airline_code    CHAR(2) PRIMARY KEY, -- e.g. '6E', 'AI', 'UK', 'SG', 'QP'
    airline_name    VARCHAR(100) NOT NULL,
    country         VARCHAR(50) DEFAULT 'India'
);

CREATE TABLE aircraft (
    aircraft_id     SERIAL PRIMARY KEY,
    registration_no VARCHAR(20) NOT NULL UNIQUE, -- e.g. 'VT-IFJ'
    airline_code    CHAR(2) NOT NULL REFERENCES airline(airline_code),
    model           VARCHAR(50) NOT NULL, -- e.g. 'Airbus A320neo'
    capacity        INTEGER NOT NULL CHECK (capacity > 0)
);

CREATE TABLE flight (
    flight_id           SERIAL PRIMARY KEY,
    flight_number       VARCHAR(10) NOT NULL, -- e.g. '6E204'
    flight_date         DATE NOT NULL,
    airline_code        CHAR(2) NOT NULL REFERENCES airline(airline_code),
    aircraft_id         INTEGER REFERENCES aircraft(aircraft_id),
    origin_airport      CHAR(3) NOT NULL REFERENCES airport(airport_code),
    destination_airport CHAR(3) NOT NULL REFERENCES airport(airport_code),
    scheduled_departure TIMESTAMP NOT NULL,
    scheduled_arrival   TIMESTAMP NOT NULL,
    actual_departure    TIMESTAMP,
    actual_arrival      TIMESTAMP,
    current_status      VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
                        CHECK (current_status IN ('SCHEDULED', 'BOARDING', 'TAXIING', 
                                                  'AIRBORNE', 'LANDED', 'DIVERTED', 'CANCELLED')),
    assigned_runway_id  INTEGER REFERENCES runway(runway_id),
    CONSTRAINT uq_flight_num_date UNIQUE (flight_number, flight_date),
    CONSTRAINT chk_flight_airports CHECK (origin_airport <> destination_airport),
    CONSTRAINT chk_flight_times CHECK (scheduled_arrival > scheduled_departure)
);

-- =====================================================================
-- MEMBER 1 JUNCTION TABLE: Gate Assignment
-- Connects GATE (M1) and FLIGHT (M2)
-- =====================================================================

CREATE TABLE gate_assignment (
    assignment_id   SERIAL PRIMARY KEY,
    gate_id         INTEGER NOT NULL REFERENCES gate(gate_id) ON DELETE CASCADE,
    flight_id       INTEGER NOT NULL REFERENCES flight(flight_id) ON DELETE CASCADE,
    assigned_from   TIMESTAMP NOT NULL,
    assigned_until  TIMESTAMP NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED'
                    CHECK (status IN ('CONFIRMED', 'OCCUPIED', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT chk_assignment_time CHECK (assigned_until > assigned_from),
    CONSTRAINT uq_flight_assignment UNIQUE (flight_id)
);

-- =====================================================================
-- MEMBER 3 TABLES (Shared Stubs): Airspace, ATC Controllers, Clearance & Logs
-- =====================================================================

CREATE TABLE airspace_sector (
    sector_id       SERIAL PRIMARY KEY,
    fir_name        VARCHAR(20) NOT NULL CHECK (fir_name IN ('DELHI', 'MUMBAI', 'CHENNAI', 'KOLKATA')),
    sector_code     VARCHAR(20) NOT NULL UNIQUE,
    lower_alt_ft    INTEGER NOT NULL CHECK (lower_alt_ft >= 0),
    upper_alt_ft    INTEGER NOT NULL CHECK (upper_alt_ft > lower_alt_ft)
);

CREATE TABLE controller (
    controller_id   SERIAL PRIMARY KEY,
    license_number  VARCHAR(30) NOT NULL UNIQUE,
    full_name       VARCHAR(100) NOT NULL,
    assigned_sector INTEGER REFERENCES airspace_sector(sector_id),
    duty_status     VARCHAR(20) DEFAULT 'ACTIVE' CHECK (duty_status IN ('ACTIVE', 'OFF_DUTY', 'RELIEVED'))
);

CREATE TABLE flight_clearance (
    clearance_id    SERIAL PRIMARY KEY,
    flight_id       INTEGER NOT NULL REFERENCES flight(flight_id),
    controller_id   INTEGER NOT NULL REFERENCES controller(controller_id),
    clearance_type  VARCHAR(30) NOT NULL CHECK (clearance_type IN ('TAKEOFF', 'LANDING', 'ALTITUDE', 'HEADING')),
    issued_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details         TEXT
);

CREATE TABLE incident_log (
    incident_id     SERIAL PRIMARY KEY,
    flight_id       INTEGER REFERENCES flight(flight_id),
    airport_code    CHAR(3) REFERENCES airport(airport_code),
    incident_type   VARCHAR(50) NOT NULL,
    severity        VARCHAR(20) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    logged_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description     TEXT NOT NULL
);
