-- ============================================================================
-- SkyFlow ATCMS – Member 3: Air Traffic Control Tower & Safety Schema
-- Tables: AIRSPACE_SECTOR, CONTROLLER, FLIGHT_CLEARANCE, INCIDENT_LOG
-- Constraints, Indexes & PL/pgSQL Safety Triggers
-- ============================================================================

-- 1. Airspace Sectors (Indian Flight Information Regions)
CREATE TABLE IF NOT EXISTS AIRSPACE_SECTOR (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(50) NOT NULL UNIQUE,
    floor_altitude_ft INT NOT NULL CHECK (floor_altitude_ft >= 0),
    ceiling_altitude_ft INT NOT NULL CHECK (ceiling_altitude_ft > floor_altitude_ft),
    max_capacity INT NOT NULL CHECK (max_capacity > 0)
);

-- 2. Licensed Controllers
CREATE TABLE IF NOT EXISTS CONTROLLER (
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

-- 3. ATC Flight Clearances (Immutable Black-Box Ledger)
CREATE TABLE IF NOT EXISTS FLIGHT_CLEARANCE (
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

-- 4. Safety & Anomaly Audit Log
CREATE TABLE IF NOT EXISTS INCIDENT_LOG (
    incident_id SERIAL PRIMARY KEY,
    flight_id INT REFERENCES FLIGHT(flight_id) ON DELETE SET NULL,
    reported_by INT NOT NULL REFERENCES CONTROLLER(controller_id),
    incident_type VARCHAR(30) NOT NULL 
        CHECK (incident_type IN ('NEAR_MISS', 'RUNWAY_INCURSION', 'ALTITUDE_BUST', 'BIRD_STRIKE', 'WEATHER_DIVERT')),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    incident_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- Performance & Lookup Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_clearance_flight ON FLIGHT_CLEARANCE(flight_id);
CREATE INDEX IF NOT EXISTS idx_clearance_controller ON FLIGHT_CLEARANCE(controller_id);
CREATE INDEX IF NOT EXISTS idx_clearance_timestamp ON FLIGHT_CLEARANCE(issued_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_incident_severity ON INCIDENT_LOG(severity);
CREATE INDEX IF NOT EXISTS idx_controller_sector ON CONTROLLER(assigned_sector_id);

-- ----------------------------------------------------------------------------
-- PL/pgSQL Safety Triggers
-- ----------------------------------------------------------------------------

-- Trigger: Enforce Runway Safety on Takeoff / Landing
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

DROP TRIGGER IF EXISTS trg_runway_clearance_safety ON FLIGHT_CLEARANCE;
CREATE TRIGGER trg_runway_clearance_safety
BEFORE INSERT ON FLIGHT_CLEARANCE
FOR EACH ROW
EXECUTE FUNCTION trg_fn_enforce_runway_safety();
