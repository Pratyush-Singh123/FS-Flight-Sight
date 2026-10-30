# SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)
## Complete Database Design, Technical Blueprint & Implementation Guide
**Course:** Database Management Systems (DBMS)  
**Domain:** Air Traffic Control (ATC) – India Domestic Airspace & Airport Network  
**Team Composition:** 3 Members (Parallel Development Architecture)

---

## Table of Contents
1. [Project Overview & Problem Statement](#1-project-overview--problem-statement)
2. [User Personas & Operational Roles](#2-user-personas--operational-roles)
3. [Functional Modules](#3-functional-modules)
4. [Entity Catalog & Attribute Dictionary](#4-entity-catalog--attribute-dictionary)
5. [Relationship Matrix & Cardinality Specifications](#5-relationship-matrix--cardinality-specifications)
6. [Visual Entity-Relationship (ER) Diagram](#6-visual-entity-relationship-er-diagram)
7. [Relational Schema (PostgreSQL DDL)](#7-relational-schema-postgresql-ddl)
8. [Normalization Analysis (1NF to 3NF/BCNF)](#8-normalization-analysis-1nf-to-3nfbcnf)
9. [Advanced Database Logic (Triggers & Views)](#9-advanced-database-logic-triggers--views)
10. [Complex SQL Queries & Course Demonstrations](#10-complex-sql-queries--course-demonstrations)
11. [Indian Aviation Dataset & Seed Scripts](#11-indian-aviation-dataset--seed-scripts)
12. [3-Member Team Parallel Work Breakdown Structure (WBS)](#12-3-member-team-parallel-work-breakdown-structure-wbs)
13. [Application Architecture & UI Blueprint](#13-application-architecture--ui-blueprint)
14. [14-Day Implementation Timeline & Demo Checklist](#14-14-day-implementation-timeline--demo-checklist)

---

## 1. Project Overview & Problem Statement

### 1.1 Problem Statement
Modern terminal radar approach control (TRACON) facilities and airport ground traffic controllers coordinate dense streams of aircraft movements across shared, constrained physical infrastructure: runways, taxiways, gates, and three-dimensional airspace sectors. 

In traditional or uncoordinated administrative systems:
- Runway and gate assignments risk double-booking or dangerous runway incursions.
- Flight clearances lack immutable, timestamped audit tracking.
- Flight delays cascade across domestic routes without centralized visibility.
- Controller handoffs between terminal towers and en-route sector centers lack verified capacity enforcement.

### 1.2 System Objectives
The **SkyFlow Air Traffic Control Management System (ATCMS)** is a relational database-driven platform designed to model, manage, and verify high-density air traffic operations across major Indian flight corridors.

Key objectives:
1. **Infrastructure Modeling:** Represent multi-airport ground assets (terminals, gates, runways) within a unified schema.
2. **Conflict Prevention:** Enforce zero-overlap runway occupancy and gate turnaround schedules at the database level via constraints and transactional triggers.
3. **Audit Ledger:** Provide an append-only log of ATC clearance instructions for post-incident black-box investigations.
4. **Operations Analytics:** Deliver real-time query capability for calculating airline on-time performance (OTP), runway congestion indices, and controller workload distribution.

---

## 2. User Personas & Operational Roles

| Persona | Operational Scope | Key System Interactions |
| :--- | :--- | :--- |
| **Ground & Tower Controller** | Local Airport Surface & Runway | Allocates gates, tracks taxi movements, reserves runways for takeoff/landing, updates physical runway status (`AVAILABLE`, `OCCUPIED`, `MAINTENANCE`). |
| **En-Route Sector Controller** | Regional 3D Airspace (FIR) | Issues cruising altitude clearances, vectors headings, monitors sector traffic limits, authorizes handoffs between sectors. |
| **Airline Flight Operations Dispatcher** | Commercial Fleet Scheduling | Registers flights, assigns aircraft tail numbers, logs scheduled turnaround times, updates flight statuses (`SCHEDULED`, `BOARDING`, `CANCELLED`). |
| **Airport Safety & Audit Officer** | Safety Inspection & Compliance | Reviews historical clearance logs, investigates incident reports (bird strikes, near-misses, runway incursions), audits controller duty logs. |

---

## 3. Functional Modules

```
                    ┌────────────────────────────────────────────────────────┐
                    │               SkyFlow ATC Management System            │
                    └───────────────────┬────────────────────────────────────┘
          ┌─────────────────────────────┼────────────────────────────┐
          ▼                             ▼                            ▼
┌──────────────────┐          ┌───────────────────┐        ┌──────────────────┐
│ Module 1:        │          │ Module 2:         │        │ Module 3:        │
│ Flight Planning  │          │ Ground & Terminal │        │ Airspace & En-   │
│ & Fleet Registry │          │ Movement Control  │        │ Route Tracking   │
└──────────────────┘          └───────────────────┘        └──────────────────┘
          │                             │                            │
          ├─────────────────────────────┼────────────────────────────┤
          ▼                             ▼                            ▼
┌──────────────────┐          ┌───────────────────┐        ┌──────────────────┐
│ Module 4:        │          │ Module 5:         │        │ Module 6:        │
│ ATC Clearances   │          │ Safety Incident   │        │ Operations &     │
│ & Audit Ledger   │          │ & Anomaly Log     │        │ Delay Analytics  │
└──────────────────┘          └───────────────────┘        └──────────────────┘
```

1. **Flight Planning & Fleet Registry Module:** Handles airline registration, aircraft fleet profiles (tail numbers, capacities, cruising limits), domestic route scheduling, and flight cancellations.
2. **Ground & Terminal Movement Control Module:** Allocates physical runways and terminal gates, verifies gate turnaround availability windows, and manages surface statuses.
3. **Airspace & En-Route Tracking Module:** Organizes 3D airspace sectors based on Indian Flight Information Regions (FIRs), enforces vertical separation (floor/ceiling altitudes), and tracks sector density against safety limits.
4. **ATC Clearances & Audit Ledger Module:** Maintains a timestamped, tamper-evident ledger of clearance instructions issued by controllers to flights (pushback, takeoff, altitude adjustments, heading vectors, landing).
5. **Safety Incident & Anomaly Log Module:** Records flight irregularities such as near-misses, runway incursions, altitude busts, bird strikes, or emergency weather diversions with severity classifications.
6. **Operations & Delay Analytics Module:** Executes aggregate queries and relational joins across tables to report on-time performance, controller action frequencies, and runway turnaround times.

---

## 4. Entity Catalog & Attribute Dictionary

### 4.1 Master Infrastructure Entities

#### `AIRPORT`
Represents physical aerodromes. Root entity for all local ground infrastructure and flight route endpoints.
- `airport_code` (VARCHAR(4), PK): ICAO/IATA identifier (e.g., `DEL`, `BOM`, `MAA`, `BLR`).
- `airport_name` (VARCHAR(100), NOT NULL): Full official name.
- `city` (VARCHAR(50), NOT NULL): Municipality served.
- `country` (VARCHAR(50), NOT NULL): Sovereign jurisdiction (default `'India'`).
- `latitude` (DECIMAL(9, 6), NOT NULL): Geographic latitude coordinate.
- `longitude` (DECIMAL(9, 6), NOT NULL): Geographic longitude coordinate.
- `elevation_ft` (INT, CHECK >= -1500 AND <= 15000): Elevation above mean sea level.

#### `RUNWAY`
Physical landing and takeoff strips at an airport.
- `runway_id` (SERIAL, PK): Unique surrogate identifier.
- `airport_code` (VARCHAR(4), FK -> `AIRPORT.airport_code`, NOT NULL): Associated airport.
- `runway_designator` (VARCHAR(10), NOT NULL): Magnetic heading label (e.g., `'09L/27R'`, `'07/25'`).
- `length_meters` (INT, CHECK >= 1000): Paved length in meters.
- `surface_type` (VARCHAR(30), DEFAULT `'ASPHALT'`): Material (`ASPHALT`, `CONCRETE`).
- `current_status` (VARCHAR(20), CHECK IN (`'AVAILABLE'`, `'OCCUPIED'`, `'CLOSED'`)): Live state.
- *Constraint:* `UNIQUE(airport_code, runway_designator)`.

#### `GATE`
Terminal parking stand for passenger boarding, deplaning, and aircraft ground handling.
- `gate_id` (SERIAL, PK): Unique surrogate identifier.
- `airport_code` (VARCHAR(4), FK -> `AIRPORT.airport_code`, NOT NULL): Associated airport.
- `terminal_number` (VARCHAR(10), NOT NULL): Terminal identifier (e.g., `'T1'`, `'T2'`, `'T3'`).
- `gate_number` (VARCHAR(10), NOT NULL): Specific gate bay (e.g., `'14A'`, `'08'`).
- `gate_category` (VARCHAR(20), CHECK IN (`'DOMESTIC'`, `'INTERNATIONAL'`)): Customs zone.
- `current_status` (VARCHAR(20), CHECK IN (`'AVAILABLE'`, `'OCCUPIED'`, `'MAINTENANCE'`)): Live state.
- *Constraint:* `UNIQUE(airport_code, terminal_number, gate_number)`.

#### `AIRSPACE_SECTOR`
Three-dimensional block of controlled sky within Indian Flight Information Regions (FIRs).
- `sector_id` (SERIAL, PK): Unique surrogate identifier.
- `sector_name` (VARCHAR(50), NOT NULL, UNIQUE): Formal airspace label (e.g., `'Delhi FIR North Upper'`).
- `floor_altitude_ft` (INT, CHECK >= 0): Minimum boundary altitude in feet.
- `ceiling_altitude_ft` (INT, CHECK > `floor_altitude_ft`): Maximum boundary altitude in feet.
- `max_capacity` (INT, CHECK > 0): Maximum concurrent aircraft permitted before mandatory rerouting.

---

### 4.2 Fleet & Personnel Entities

#### `AIRLINE`
Commercial or cargo operating entity.
- `airline_id` (SERIAL, PK): Unique surrogate identifier.
- `airline_name` (VARCHAR(100), NOT NULL, UNIQUE): Commercial brand name (e.g., `'IndiGo'`).
- `callsign_prefix` (VARCHAR(10), NOT NULL, UNIQUE): ATC voice prefix/ICAO 3-letter code (`'IGO'`, `'AIC'`).
- `country_of_origin` (VARCHAR(50), NOT NULL): Registered country.
- `contact_email` (VARCHAR(100), NOT NULL, UNIQUE): Corporate dispatch contact.

#### `AIRCRAFT`
Individual physical airframe identified by its civil aviation registration.
- `aircraft_reg_no` (VARCHAR(12), PK): Civil tail registration (e.g., `'VT-ISN'`, `'VT-EXF'`).
- `model` (VARCHAR(50), NOT NULL): Model name (e.g., `'A320neo'`, `'B737-MAX8'`).
- `manufacturer` (VARCHAR(50), NOT NULL): Manufacturer (e.g., `'Airbus'`, `'Boeing'`, `'ATR'`).
- `passenger_capacity` (INT, CHECK > 0): Maximum seating capacity.
- `max_altitude_ft` (INT, CHECK BETWEEN 1000 AND 60000): Certified service ceiling.
- `cruising_speed_knots` (INT, CHECK > 0): Standard true airspeed.
- `airline_id` (INT, FK -> `AIRLINE.airline_id`, NOT NULL): Registered operating carrier.

#### `CONTROLLER`
Certified air traffic control officer on duty.
- `controller_id` (SERIAL, PK): Unique employee/license surrogate ID.
- `first_name` (VARCHAR(50), NOT NULL): Given name.
- `last_name` (VARCHAR(50), NOT NULL): Family name.
- `license_number` (VARCHAR(30), NOT NULL, UNIQUE): Official regulatory license string.
- `certification_level` (VARCHAR(20), CHECK IN (`'GROUND'`, `'TOWER'`, `'APPROACH'`, `'EN_ROUTE'`)): Clearance authority.
- `shift_start` (TIME, NOT NULL): Scheduled duty start time.
- `shift_end` (TIME, NOT NULL): Scheduled duty end time.
- `assigned_sector_id` (INT, FK -> `AIRSPACE_SECTOR.sector_id`, NULLABLE): Current active monitoring sector.

---

### 4.3 Operational & Transactional Entities

#### `FLIGHT`
Specific flight leg on a given calendar date.
- `flight_id` (SERIAL, PK): Unique surrogate flight leg ID.
- `flight_number` (VARCHAR(10), NOT NULL): Commercial flight number (e.g., `'6E-204'`).
- `flight_date` (DATE, NOT NULL): Operational calendar date.
- `airline_id` (INT, FK -> `AIRLINE.airline_id`, NOT NULL): Operating carrier.
- `aircraft_reg_no` (VARCHAR(12), FK -> `AIRCRAFT.aircraft_reg_no`, NOT NULL): Assigned airframe.
- `origin_airport` (VARCHAR(4), FK -> `AIRPORT.airport_code`, NOT NULL): Departure aerodrome.
- `dest_airport` (VARCHAR(4), FK -> `AIRPORT.airport_code`, NOT NULL): Arrival aerodrome.
- `scheduled_departure` (TIMESTAMP, NOT NULL): Planned departure time.
- `scheduled_arrival` (TIMESTAMP, NOT NULL): Planned arrival time.
- `actual_departure` (TIMESTAMP, NULLABLE): Actual off-ground timestamp.
- `actual_arrival` (TIMESTAMP, NULLABLE): Actual touchdown timestamp.
- `current_status` (VARCHAR(20), CHECK IN (`'SCHEDULED'`, `'BOARDING'`, `'TAXIING'`, `'AIRBORNE'`, `'LANDED'`, `'DIVERTED'`, `'CANCELLED'`)): Current state.
- *Constraints:* 
  - `UNIQUE(flight_number, flight_date)`
  - `CHECK(origin_airport <> dest_airport)`
  - `CHECK(scheduled_arrival > scheduled_departure)`

#### `GATE_ASSIGNMENT`
Time-bounded reservation of a terminal gate for aircraft turnaround.
- `assignment_id` (SERIAL, PK): Unique surrogate ID.
- `flight_id` (INT, FK -> `FLIGHT.flight_id`, NOT NULL): Associated flight.
- `gate_id` (INT, FK -> `GATE.gate_id`, NOT NULL): Physical gate.
- `assigned_from` (TIMESTAMP, NOT NULL): Gate occupancy start.
- `assigned_until` (TIMESTAMP, NOT NULL): Gate vacancy release.
- `assignment_type` (VARCHAR(10), CHECK IN (`'ARRIVAL'`, `'DEPARTURE'`)): Purpose.
- *Constraint:* `CHECK(assigned_until > assigned_from)`.

#### `FLIGHT_CLEARANCE`
Atomic instructional command issued by ATC personnel to an active flight.
- `clearance_id` (SERIAL, PK): Unique audit event ID.
- `flight_id` (INT, FK -> `FLIGHT.flight_id`, NOT NULL): Target aircraft.
- `controller_id` (INT, FK -> `CONTROLLER.controller_id`, NOT NULL): Authorizing officer.
- `runway_id` (INT, FK -> `RUNWAY.runway_id`, NULLABLE): Referenced runway (if takeoff/landing).
- `clearance_type` (VARCHAR(30), CHECK IN (`'PUSHBACK'`, `'TAXI'`, `'TAKEOFF'`, `'ALTITUDE_CHANGE'`, `'HEADING'`, `'LANDING'`)): Action.
- `issued_timestamp` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP): Command timestamp.
- `assigned_altitude_ft` (INT, CHECK BETWEEN 0 AND 60000): Altitude assignment.
- `assigned_heading_deg` (INT, CHECK BETWEEN 0 AND 360): Vector heading in degrees.

#### `INCIDENT_LOG`
Safety violation, near-miss, or emergency event audit ledger.
- `incident_id` (SERIAL, PK): Unique incident report ID.
- `flight_id` (INT, FK -> `FLIGHT.flight_id`, NULLABLE): Involved flight (if applicable).
- `reported_by` (INT, FK -> `CONTROLLER.controller_id`, NOT NULL): Reporting controller.
- `incident_type` (VARCHAR(30), CHECK IN (`'NEAR_MISS'`, `'RUNWAY_INCURSION'`, `'ALTITUDE_BUST'`, `'BIRD_STRIKE'`, `'WEATHER_DIVERT'`)): Anomaly category.
- `severity` (VARCHAR(10), CHECK IN (`'LOW'`, `'MEDIUM'`, `'HIGH'`, `'CRITICAL'`)): Safety classification.
- `incident_time` (TIMESTAMP, NOT NULL, DEFAULT CURRENT_TIMESTAMP): Incident occurrence timestamp.
- `description` (TEXT, NOT NULL): Narrative explanation of the event.

---

## 5. Relationship Matrix & Cardinality Specifications

| Parent Entity | Child Entity | Foreign Key Column | Cardinality | Business Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `AIRLINE` | `AIRCRAFT` | `airline_id` | 1 : N | An airline owns/leases multiple aircraft; each aircraft belongs to one airline. |
| `AIRPORT` | `RUNWAY` | `airport_code` | 1 : N | An airport contains multiple runways; each runway belongs to one airport. |
| `AIRPORT` | `GATE` | `airport_code` | 1 : N | An airport houses multiple terminal gates; each gate resides at one airport. |
| `AIRPORT` | `FLIGHT` | `origin_airport` | 1 : N | An airport serves as origin for many flights; each flight departs from one origin. |
| `AIRPORT` | `FLIGHT` | `dest_airport` | 1 : N | An airport serves as destination for many flights; each flight arrives at one destination. |
| `AIRCRAFT` | `FLIGHT` | `aircraft_reg_no`| 1 : N | An aircraft flies sequential flight legs over time; a flight leg uses one airframe. |
| `AIRLINE` | `FLIGHT` | `airline_id` | 1 : N | An airline schedules and operates multiple flights; each flight belongs to one carrier. |
| `FLIGHT` | `GATE_ASSIGNMENT` | `flight_id` | 1 : N | A flight has gate reservations (departure and arrival); an assignment belongs to one flight. |
| `GATE` | `GATE_ASSIGNMENT` | `gate_id` | 1 : N | A gate accommodates multiple sequential flights; an assignment reserves one gate. |
| `AIRSPACE_SECTOR` | `CONTROLLER`| `assigned_sector_id`| 1 : N | A sector is monitored by controllers across shifts; a controller monitors one sector per shift. |
| `FLIGHT` | `FLIGHT_CLEARANCE`| `flight_id` | 1 : N | A flight receives multiple sequential clearance instructions; a clearance applies to one flight. |
| `CONTROLLER` | `FLIGHT_CLEARANCE`| `controller_id`| 1 : N | A controller issues many clearances over a shift; each clearance is logged by one controller. |
| `RUNWAY` | `FLIGHT_CLEARANCE`| `runway_id` | 1 : N | A runway is referenced in multiple takeoff/landing clearances; a clearance references at most one runway. |
| `FLIGHT` | `INCIDENT_LOG` | `flight_id` | 1 : N | A flight may be involved in zero, one, or more safety incidents; an incident references at most one flight. |
| `CONTROLLER` | `INCIDENT_LOG` | `reported_by` | 1 : N | A controller can log multiple safety incidents; each report is filed by one controller. |

---

## 6. Visual Entity-Relationship (ER) Diagram

```
               ┌────────────────┐
               │    AIRLINE     │
               └───┬────────────┘
                   │ 1
                   │ owns/operates
                   │ N
┌──────────────┐   ┌────────────┴───┐
│   AIRPORT    │   │    AIRCRAFT    │
└───┬───┬───┬──┘   └───┬────────────┘
    │   │   │          │
    │   │   │ origin/  │
    │   │   │ dest     │ assigned to
    │   │   └─────┐    │
    │   │         ▼    ▼
    │   │       ┌───────────────┐                  ┌────────────────────┐
    │   │       │    FLIGHT     │ 1 ──────────── N │  GATE_ASSIGNMENT   │
    │   │       └───┬───────┬───┘                  └─────────┬──────────┘
    │   │           │       │                                │ N
    │   │           │       │ 1                              │ assigned to
    │   │           │       │ receives                       │ 1
    │   │           │       ▼                      ┌─────────┴──────────┐
    │   │           │   ┌───────────────────┐      │        GATE        │
    │   │           │   │ FLIGHT_CLEARANCE  │      └────────────────────┘
    │   │ has gates │   └───┬───────────┬───┘
    │   └───────────┼───────┼───────────┼──────────┐
    │               │       │           │          │ has runways
    ▼               ▼       ▼           │          ▼
┌───────────────┐ ┌───────────────┐     │     ┌─────────────────┐
│ INCIDENT_LOG  │ │  CONTROLLER   │     │     │     RUNWAY      │
└───────────────┘ └───┬───────────┘     │     └─────────────────┘
                      │                 │              ▲
                      │ 1               └──────────────┘
                      │ monitors (N:1)    handled by (N:1)
                      ▼
            ┌───────────────────┐
            │  AIRSPACE_SECTOR  │
            └───────────────────┘
```

---

## 7. Relational Schema (PostgreSQL DDL)

Save and execute the following DDL script in your PostgreSQL database (`skyflow_atc`):

```sql
-- ============================================================================
-- SkyFlow ATC Management System: Complete Database Schema
-- DBMS Course Project: Relational Implementation
-- ============================================================================

-- Drop tables in reverse order of foreign key dependencies
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

-- 1. AIRPORT TABLE
CREATE TABLE AIRPORT (
    airport_code VARCHAR(4) PRIMARY KEY, -- ICAO/IATA identifier (e.g., 'DEL', 'VIDP')
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'India',
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    elevation_ft INT CHECK (elevation_ft >= -1500 AND elevation_ft <= 15000)
);

-- 2. AIRLINE TABLE
CREATE TABLE AIRLINE (
    airline_id SERIAL PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    callsign_prefix VARCHAR(10) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50) NOT NULL DEFAULT 'India',
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

-- 3. AIRCRAFT TABLE
CREATE TABLE AIRCRAFT (
    aircraft_reg_no VARCHAR(12) PRIMARY KEY, -- DGCA tail number (e.g., 'VT-ISN')
    model VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    passenger_capacity INT CHECK (passenger_capacity > 0),
    max_altitude_ft INT CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000),
    cruising_speed_knots INT CHECK (cruising_speed_knots > 0),
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE CASCADE
);

-- 4. RUNWAY TABLE
CREATE TABLE RUNWAY (
    runway_id SERIAL PRIMARY KEY,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    runway_designator VARCHAR(10) NOT NULL, -- e.g. '09L/27R', '07/25'
    length_meters INT NOT NULL CHECK (length_meters >= 1000),
    surface_type VARCHAR(30) DEFAULT 'ASPHALT',
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED')),
    UNIQUE (airport_code, runway_designator)
);

-- 5. GATE TABLE
CREATE TABLE GATE (
    gate_id SERIAL PRIMARY KEY,
    airport_code VARCHAR(4) NOT NULL REFERENCES AIRPORT(airport_code) ON DELETE CASCADE,
    terminal_number VARCHAR(10) NOT NULL, -- e.g. 'T1', 'T2', 'T3'
    gate_number VARCHAR(10) NOT NULL, -- e.g. '14A', '08'
    gate_category VARCHAR(20) NOT NULL DEFAULT 'DOMESTIC'
        CHECK (gate_category IN ('DOMESTIC', 'INTERNATIONAL')),
    current_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    UNIQUE (airport_code, terminal_number, gate_number)
);

-- 6. AIRSPACE_SECTOR TABLE
CREATE TABLE AIRSPACE_SECTOR (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(50) NOT NULL UNIQUE,
    floor_altitude_ft INT NOT NULL CHECK (floor_altitude_ft >= 0),
    ceiling_altitude_ft INT NOT NULL CHECK (ceiling_altitude_ft > floor_altitude_ft),
    max_capacity INT NOT NULL CHECK (max_capacity > 0)
);

-- 7. CONTROLLER TABLE
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

-- 8. FLIGHT TABLE
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

-- 9. GATE_ASSIGNMENT TABLE
CREATE TABLE GATE_ASSIGNMENT (
    assignment_id SERIAL PRIMARY KEY,
    flight_id INT NOT NULL REFERENCES FLIGHT(flight_id) ON DELETE CASCADE,
    gate_id INT NOT NULL REFERENCES GATE(gate_id) ON DELETE CASCADE,
    assigned_from TIMESTAMP NOT NULL,
    assigned_until TIMESTAMP NOT NULL,
    assignment_type VARCHAR(10) NOT NULL CHECK (assignment_type IN ('ARRIVAL', 'DEPARTURE')),
    CHECK (assigned_until > assigned_from)
);

-- 10. FLIGHT_CLEARANCE TABLE
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

-- 11. INCIDENT_LOG TABLE
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

-- Indexes for frequent query paths
CREATE INDEX idx_flight_dates ON FLIGHT(flight_date, origin_airport, dest_airport);
CREATE INDEX idx_flight_status ON FLIGHT(current_status);
CREATE INDEX idx_clearance_flight ON FLIGHT_CLEARANCE(flight_id);
CREATE INDEX idx_gate_time ON GATE_ASSIGNMENT(assigned_from, assigned_until);
```

---

## 8. Normalization Analysis (1NF to 3NF/BCNF)

A core requirement in CSE evaluations is proving why the database design avoids redundancy and update/delete anomalies.

### First Normal Form (1NF)
* **Rule:** Every attribute contains only atomic (indivisible) values; no repeating groups or arrays.
* **Verification:** 
  - Rather than storing multiple clearances or telemetry pings inside arrays or comma-delimited strings within `FLIGHT`, separate child tables (`FLIGHT_CLEARANCE`, `GATE_ASSIGNMENT`) record each atomic event.
  - Geographical coordinates are partitioned into atomic `latitude` and `longitude` fields.

### Second Normal Form (2NF)
* **Rule:** Table must be in 1NF, and all non-key attributes must be fully functionally dependent on the entire primary key (no partial dependencies).
* **Verification:**
  - In tables with surrogate keys (`flight_id`, `runway_id`, `gate_id`), every non-key column depends strictly on the entire single-attribute surrogate key.
  - In associative tables (`GATE_ASSIGNMENT`), attributes like `assigned_from` and `assignment_type` depend on the unique `assignment_id`, avoiding partial dependencies.

### Third Normal Form (3NF) & Boyce-Codd Normal Form (BCNF)
* **Rule:** Table must be in 2NF, and no non-key attribute is transitively dependent on the primary key (no $X \rightarrow Y \rightarrow Z$ dependencies where $X$ is the PK and $Y$ is a non-key).
* **Verification:**
  - In `FLIGHT`, we store `aircraft_reg_no` and `airline_id`, but we do **not** store `model`, `passenger_capacity`, or `airline_name`. Those attributes are looked up from `AIRCRAFT` and `AIRLINE`. This eliminates transitive dependency and prevents update anomalies (e.g., updating aircraft capacity requires modifying only one row in `AIRCRAFT`).
  - In `GATE` and `RUNWAY`, airport metadata (`city`, `country`, `elevation_ft`) is not duplicated; it resides exclusively in `AIRPORT`.

---

## 9. Advanced Database Logic (Triggers & Views)

### 9.1 Real-Time Runway Conflict Prevention Trigger
Prevents an air traffic controller from issuing a `TAKEOFF` or `LANDING` clearance if the specified runway is currently marked `OCCUPIED` or `CLOSED`. If available, it automatically locks the runway status to `OCCUPIED`.

```sql
CREATE OR REPLACE FUNCTION trg_fn_enforce_runway_safety()
RETURNS TRIGGER AS $$
DECLARE
    r_status VARCHAR(20);
BEGIN
    IF NEW.runway_id IS NOT NULL AND NEW.clearance_type IN ('TAKEOFF', 'LANDING') THEN
        -- Fetch current runway status
        SELECT current_status INTO r_status 
        FROM RUNWAY 
        WHERE runway_id = NEW.runway_id;

        IF r_status <> 'AVAILABLE' THEN
            RAISE EXCEPTION 'Runway Safety Violation: Runway ID % is currently %!', NEW.runway_id, r_status;
        END IF;

        -- Automatically lock runway status
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
```

### 9.2 Comprehensive Airport Operations Radar View
Joins flights, airlines, gates, and runways to provide an immediate overview for the UI:

```sql
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
```

---

## 10. Complex SQL Queries & Course Demonstrations

The following representative queries demonstrate major relational database concepts covered in core syllabus rubrics:

### Query 1: Multi-Table Join with Dynamic Clearance Subquery
*Retrieves all active airborne flights crossing Indian airspace with operating carrier, aircraft type, and the last authorized altitude command:*
```sql
SELECT 
    f.flight_number,
    al.airline_name,
    f.aircraft_reg_no,
    ac.model,
    f.origin_airport || ' -> ' || f.dest_airport AS route,
    f.actual_departure,
    fc.assigned_altitude_ft,
    fc.assigned_heading_deg,
    c.first_name || ' ' || c.last_name AS authorizing_controller
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
JOIN FLIGHT_CLEARANCE fc ON f.flight_id = fc.flight_id
JOIN CONTROLLER c ON fc.controller_id = c.controller_id
WHERE f.current_status = 'AIRBORNE'
  AND fc.clearance_id = (
      SELECT MAX(sub.clearance_id)
      FROM FLIGHT_CLEARANCE sub
      WHERE sub.flight_id = f.flight_id
  )
ORDER BY f.actual_departure ASC;
```

### Query 2: Aggregate Analysis with `GROUP BY` and `HAVING`
*Analyzes controller workload and filters officers who have authorized 10 or more clearances during their shift:*
```sql
SELECT 
    c.controller_id,
    c.first_name || ' ' || c.last_name AS controller_name,
    c.certification_level,
    sec.sector_name,
    COUNT(fc.clearance_id) AS total_clearances_issued,
    COUNT(DISTINCT fc.flight_id) AS distinct_aircraft_handled
FROM CONTROLLER c
JOIN FLIGHT_CLEARANCE fc ON c.controller_id = fc.controller_id
LEFT JOIN AIRSPACE_SECTOR sec ON c.assigned_sector_id = sec.sector_id
GROUP BY c.controller_id, c.first_name, c.last_name, c.certification_level, sec.sector_name
HAVING COUNT(fc.clearance_id) >= 10
ORDER BY total_clearances_issued DESC;
```

### Query 3: Correlated Subquery for Airline Delay Analysis
*Computes departure delay in minutes and filters domestic flights delayed past 30 minutes:*
```sql
SELECT 
    f.flight_number,
    al.airline_name,
    f.origin_airport,
    f.dest_airport,
    f.scheduled_departure,
    f.actual_departure,
    ROUND(EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60) AS delay_minutes
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
WHERE f.actual_departure IS NOT NULL
  AND f.flight_id IN (
      SELECT sub_f.flight_id 
      FROM FLIGHT sub_f 
      WHERE sub_f.actual_departure > sub_f.scheduled_departure + INTERVAL '30 minutes'
  )
ORDER BY delay_minutes DESC;
```

### Query 4: Set Operations & Terminal Gate Bottleneck Report
*Finds all terminal gates at Chennai (`MAA`) and Delhi (`DEL`) that currently have zero assigned flights:*
```sql
SELECT g.gate_id, g.airport_code, g.terminal_number, g.gate_number, g.gate_category
FROM GATE g
WHERE g.airport_code IN ('MAA', 'DEL')
EXCEPT
SELECT g.gate_id, g.airport_code, g.terminal_number, g.gate_number, g.gate_category
FROM GATE g
JOIN GATE_ASSIGNMENT ga ON g.gate_id = ga.gate_id
WHERE CURRENT_TIMESTAMP BETWEEN ga.assigned_from AND ga.assigned_until;
```

---

## 11. Indian Aviation Dataset & Seed Scripts

Save and run this script to populate realistic Indian aviation records:

```sql
-- 1. 12 Major Indian Airports
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

-- 2. Operating Indian Airlines
INSERT INTO AIRLINE (airline_name, callsign_prefix, country_of_origin, contact_email) VALUES
('IndiGo', 'IGO', 'India', 'operations@goindigo.in'),
('Air India', 'AIC', 'India', 'dispatch@airindia.com'),
('SpiceJet', 'SEJ', 'India', 'ops@spicejet.com'),
('Akasa Air', 'AKJ', 'India', 'atc@akasaair.com');

-- 3. Commercial Aircraft Fleet (DGCA Registry)
INSERT INTO AIRCRAFT (aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft, cruising_speed_knots, airline_id) VALUES
('VT-ISN', 'A320neo', 'Airbus', 186, 39000, 450, 1),
('VT-IFP', 'A321neo', 'Airbus', 222, 39000, 460, 1),
('VT-EXF', 'B787-8 Dreamliner', 'Boeing', 256, 43000, 490, 2),
('VT-CIO', 'A320neo', 'Airbus', 180, 39000, 450, 2),
('VT-SLA', 'B737-800', 'Boeing', 189, 41000, 455, 3),
('VT-YAA', 'B737-MAX8', 'Boeing', 189, 41000, 460, 4);

-- 4. Indian FIR Airspace Sectors
INSERT INTO AIRSPACE_SECTOR (sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity) VALUES
('Delhi FIR (VIDF)', 0, 46000, 60),
('Mumbai FIR (VABF)', 0, 46000, 55),
('Chennai FIR (VOMF)', 0, 46000, 50),
('Kolkata FIR (VECF)', 0, 46000, 45);

-- 5. Physical Runways at Major Hubs
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

-- 6. Terminal Gates
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

-- 7. Controllers on Duty
INSERT INTO CONTROLLER (first_name, last_name, license_number, certification_level, shift_start, shift_end, assigned_sector_id) VALUES
('Vikram', 'Rathore', 'AAI-ATCO-1092', 'TOWER', '06:00', '14:00', 1),
('Ananya', 'Sharma', 'AAI-ATCO-2234', 'EN_ROUTE', '06:00', '14:00', 1),
('Karthik', 'Ramanathan', 'AAI-ATCO-3310', 'TOWER', '14:00', '22:00', 3),
('Siddharth', 'Nair', 'AAI-ATCO-4491', 'APPROACH', '14:00', '22:00', 3),
('Neha', 'Deshmukh', 'AAI-ATCO-5582', 'TOWER', '06:00', '14:00', 2);

-- 8. Scheduled Domestic Flights
INSERT INTO FLIGHT (flight_number, flight_date, airline_id, aircraft_reg_no, origin_airport, dest_airport, scheduled_departure, scheduled_arrival, current_status) VALUES
('6E-204', '2026-11-01', 1, 'VT-ISN', 'DEL', 'MAA', '2026-11-01 07:00:00', '2026-11-01 09:45:00', 'SCHEDULED'),
('AI-101', '2026-11-01', 2, 'VT-EXF', 'BOM', 'DEL', '2026-11-01 08:30:00', '2026-11-01 10:40:00', 'BOARDING'),
('6E-532', '2026-11-01', 1, 'VT-IFP', 'BLR', 'DEL', '2026-11-01 09:15:00', '2026-11-01 12:00:00', 'SCHEDULED'),
('QP-1102', '2026-11-01', 4, 'VT-YAA', 'BOM', 'BLR', '2026-11-01 10:00:00', '2026-11-01 11:45:00', 'SCHEDULED'),
('SG-8169', '2026-11-01', 3, 'VT-SLA', 'DEL', 'AMD', '2026-11-01 11:00:00', '2026-11-01 12:35:00', 'SCHEDULED');
```

---

## 12. 3-Member Team Parallel Work Breakdown Structure (WBS)

To ensure that each member can work 100% independently from Day 1 without blocking each other:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FROZEN DATABASE SCHEMA CONTRACT                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
         ┌─────────────────────────────┼────────────────────────────┐
         ▼                             ▼                            ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│ Member 1: Ground & Hubs   │ │ Member 2: Flight Ops      │ │ Member 3: ATC Clearances  │
├───────────────────────────┤ ├───────────────────────────┤ ├───────────────────────────┤
│ DB: AIRPORT, RUNWAY,      │ │ DB: AIRLINE, AIRCRAFT,    │ │ DB: AIRSPACE_SECTOR,      │
│     GATE, GATE_ASSIGNMENT │ │     FLIGHT                │ │     CONTROLLER, CLEARANCE,│
│ Queries: Ground & Gates   │ │ Queries: OTP, Routes      │ │     INCIDENT_LOG          │
│ UI: Airport & Ground Hub  │ │ UI: Flight Dispatch Page  │ │ UI: ATC Radar Console     │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

### Member 1: Ground Infrastructure & Terminal Movement Lead
* **Scope:** Physical aerodromes, runways, terminal gates, and turnaround schedules.
* **Database Responsibilities:**
  - Owns DDL & constraints for `AIRPORT`, `RUNWAY`, `GATE`, and `GATE_ASSIGNMENT`.
  - Populates runway lengths and terminal gate configurations across all 12 Indian airports.
  - Implements constraints preventing double-booking of gates.
* **SQL Queries:**
  - Calculates runway utilization rates across hubs.
  - Generates gate idle-time reports and terminal congestion metrics.
* **UI Screen (Page 1):**
  - **Airport Surface & Terminal Dashboard:**
    - Hub selector (dropdown: `DEL`, `BOM`, `MAA`, `BLR`, etc.).
    - Runway status card with toggles (`AVAILABLE`, `OCCUPIED`, `CLOSED`).
    - Gate assignment board showing docked flights and allowing ground staff to reassign gates.

### Member 2: Commercial Fleet & Flight Operations Lead
* **Scope:** Airlines, aircraft registry, and domestic flight scheduling.
* **Database Responsibilities:**
  - Owns DDL & constraints for `AIRLINE`, `AIRCRAFT`, and `FLIGHT`.
  - Populates Indian carriers and aircraft fleet registries with DGCA `VT-` tail numbers.
  - Enforces route scheduling rules (`origin <> dest`, `arrival > departure`).
* **SQL Queries:**
  - Calculates On-Time Performance (OTP) by airline carrier.
  - Evaluates highest density routes (`BOM-DEL`, `DEL-BLR`) and average delay lengths.
* **UI Screen (Page 2):**
  - **Flight Operations & Dispatch Portal:**
    - Interactive form to add new flights (airline, tail number, route, scheduled timestamps).
    - Flight status updater (transitions flight from `SCHEDULED` $\rightarrow$ `BOARDING` $\rightarrow$ `AIRBORNE` $\rightarrow$ `LANDED` or logs delay minutes).
    - Flight search & filter view by flight number, origin, or destination.

### Member 3: Air Traffic Control Tower, En-Route & Safety Lead
* **Scope:** Airspace sectors (FIRs), controllers, real-time clearances, and safety audits.
* **Database Responsibilities:**
  - Owns DDL & constraints for `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT_CLEARANCE`, and `INCIDENT_LOG`.
  - Implements PL/pgSQL triggers enforcing runway vacancy before issuing takeoff/landing clearances.
  - Populates Indian FIR sectors and controller shift schedules.
* **SQL Queries:**
  - Controller clearance workload metrics grouped by certification level.
  - Incident severity audit report linking incidents to flights and controllers.
* **UI Screen (Page 3):**
  - **ATC Tower Clearance Console & Safety Dashboard:**
    - Clearance issuance console (select active flight, select clearance type, assign altitude/heading/runway).
    - Live clearance stream displaying the last 20 ATC instructions issued.
    - Safety incident filing modal (log near-miss, runway incursion, bird strike with severity).

---

## 13. Application Architecture & UI Blueprint

### Recommended Stack Options

#### Option A: Python + Streamlit (Fastest to implement for 3 members)
- **Backend/DB Connector:** `psycopg2-binary` or `SQLAlchemy`.
- **Multi-page Structure:**
  - `app.py`: Main overview dashboard and system connection.
  - `pages/1_Airport_Ground_Control.py` (Owned by Member 1)
  - `pages/2_Flight_Operations.py` (Owned by Member 2)
  - `pages/3_ATC_Clearance_Console.py` (Owned by Member 3)
- **Advantage:** Native data tables, forms, and metric widgets in pure Python without writing HTML/CSS/JavaScript.

#### Option B: React + Node.js/Express + PostgreSQL
- **Backend:** Express.js REST API with `pg` (node-postgres) pool.
- **Frontend:** React with Tailwind CSS and Lucide icons.
- **Routing:** React Router with 3 top navigation tabs matching the 3 member roles.

---

## 14. 14-Day Implementation Timeline & Demo Checklist

```
Days 1–2   : Git Repo setup & execute unified DDL/Seed data.
Days 3–6   : Individual DDL polish, constraints, and distinct domain queries in parallel.
Days 7–10  : Build distinct UI pages and connect backend queries in parallel.
Days 11–12 : Merge branches into main; run cross-table verification tests.
Days 13–14 : Final report documentation and demo presentation practice.
```

### Demonstration Script for Course Evaluators
1. **Show Database Design & Constraints:**
   - Display the ER diagram and explain the 11 entities and foreign key mappings.
   - Intentionally attempt to insert an invalid flight where `origin_airport = dest_airport` to show database-level constraint rejection.
2. **Demonstrate Member 1's Module (Ground & Runways):**
   - Switch to the Airport Ground Control tab.
   - Select `MAA` (Chennai). Toggle Runway `07/25` to `OCCUPIED`.
   - Show available gates and allocate Gate `04` to an arriving aircraft.
3. **Demonstrate Member 2's Module (Flight Dispatch):**
   - Switch to the Flight Operations tab.
   - Schedule a new flight: `6E-901` from `DEL` to `BOM` on `VT-ISN`.
   - Update its status to `AIRBORNE` and show the change reflecting in the database.
4. **Demonstrate Member 3's Module (ATC Clearance & Safety):**
   - Switch to the ATC Clearance Console.
   - Attempt to issue a `TAKEOFF` clearance on the occupied runway; verify that the PL/pgSQL trigger throws an error.
   - Issue a valid clearance on an available runway and log a sample safety incident.
5. **Show Analytical Reports:**
   - Display the On-Time Performance (OTP) summary and controller workload distribution charts generated via the complex SQL queries.
