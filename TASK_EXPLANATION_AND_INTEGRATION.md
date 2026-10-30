# SkyFlow ATCMS – Complete Project Architecture, Task Explanations & Cross-Member Integration Guide

**System:** SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)  
**Domain:** High-Density Indian Domestic Airspace & Airport Network  
**Course:** Database Management Systems (DBMS)  
**Architecture:** 3-Member Collaborative Relational Platform  

---

## 1. Executive Summary & Problem Statement

### 1.1 Real-World Problem Statement
Modern commercial aviation coordinates dense streams of aircraft movements across shared, constrained physical infrastructure: runways, terminal aerobridges, taxiways, and three-dimensional airspace sectors. In traditional uncoordinated administrative platforms:
- Runway and gate schedules risk double-booking or catastrophic runway incursions.
- Clearances between terminal control towers and en-route sector radar facilities lack immutable audit logging.
- Flight delay cascades propagate across domestic hubs without centralized operational visibility.
- Airline dispatchers and ATC controllers operate in organizational silos, leading to miscommunication.

### 1.2 System Objectives
The **SkyFlow Integrated Operations Control Center (IOCC)** is a full-stack, relational database-driven platform built to resolve these operational bottlenecks across 12 major Indian aviation hubs (Delhi `DEL`, Mumbai `BOM`, Bengaluru `BLR`, Chennai `MAA`, Kolkata `CCU`, Hyderabad `HYD`, etc.).

---

## 2. 3-Member Collaborative Architecture & Task Division

SkyFlow enforces a **Frozen Database Schema Contract** (Boyce-Codd Normal Form) that allows all 3 team members to develop, test, and demonstrate their operational subsystems in parallel while sharing a synchronized relational database:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FROZEN RELATIONAL SCHEMA CONTRACT                                      │
└───────────────────────────────────┬──────────────────────────────────┬─────────────────────────────────┘
                                    │                                  │
         ┌──────────────────────────┴──────────┐                       │
         ▼                                     ▼                       ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Member 1: Ground & Hubs     │ │ Member 2: Flight Operations │ │ Member 3: Tower & Safety    │
├─────────────────────────────┤ ├─────────────────────────────┤ ├─────────────────────────────┤
│ Entities:                   │ │ Entities:                   │ │ Entities:                   │
│  - AIRPORT                  │ │  - AIRLINE                  │ │  - AIRSPACE_SECTOR          │
│  - RUNWAY                   │ │  - AIRCRAFT                 │ │  - CONTROLLER               │
│  - GATE                     │ │  - FLIGHT                   │ │  - FLIGHT_CLEARANCE         │
│  - GATE_ASSIGNMENT          │ │                             │ │  - INCIDENT_LOG             │
│ Trigger:                    │ │ Constraints:                │ │ Triggers:                   │
│  - Gate Double-Booking      │ │  - Route (origin <> dest)   │ │  - Runway Collision Abort   │
│    Overlap Interlock        │ │  - Time (arr > dep)         │ │  - Auto-Occupancy Update    │
│ Queries:                    │ │ Queries:                    │ │ Queries:                    │
│  - Runway Congestion (Peak) │ │  - On-Time Performance (OTP)│ │  - Correlated Airborne Join │
│  - Gate Turnaround Averages │ │  - Route Density Analysis   │ │  - Controller Workload      │
│ UI: Page 1                  │ │ UI: Page 2                  │ │ UI: Page 3                  │
└─────────────────────────────┘ └─────────────────────────────┘ └─────────────────────────────┘
```

---

## 3. In-Depth Technical Breakdown by Member

### 🏢 Member 1: Ground Infrastructure & Terminal Movement Lead
* **Primary Scope:** Master airport aerodromes, paved runways, passenger terminal gates, and turnaround allocations.
* **Entities Owned:**
  - `AIRPORT` (airport_code, airport_name, city, country, latitude, longitude, elevation_ft)
  - `RUNWAY` (runway_id, airport_code, runway_designator, length_meters, width_m, surface_type, current_status)
  - `GATE` (gate_id, airport_code, terminal_number, gate_number, gate_category, current_status)
  - `GATE_ASSIGNMENT` (assignment_id, flight_id, gate_id, assigned_from, assigned_until, status)
* **Automated Database Trigger (`trg_prevent_gate_double_booking`):**
  - **Logic:** Before inserting or updating a `GATE_ASSIGNMENT`, checks if an active reservation already exists for that gate where `(NEW.assigned_from < assigned_until AND NEW.assigned_until > assigned_from)`.
  - **Behavior:** Aborts the transaction with an exception if an overlap is detected, eliminating double-booked terminal gates.
* **Complex SQL Demonstrations:**
  - *Query 1 (Runway Congestion):* Uses `date_trunc('hour')`, multi-table joins, `GROUP BY`, and `HAVING COUNT(*) >= 1` to compute movements per runway per peak hour.
  - *Query 2 (Gate Turnaround Averages):* Uses correlated subqueries with `EXTRACT(EPOCH)` and `AVG()` to calculate turnaround minutes per aerobridge.
  - *View (`view_airport_ground_dashboard`):* Pre-aggregates airport health (total runways, free runways, total gates, free gates).
* **UI Interface (`pages/1_Airport_Ground_Control.py`):**
  - Aerodrome facility selector across all 12 hubs.
  - Live runway status grid with interactive toggle (`AVAILABLE`, `OCCUPIED`, `CLOSED`).
  - Terminal bay occupancy monitor.
  - Gate booking form with automated trigger validation.

---

### 🛫 Member 2: Commercial Fleet & Flight Operations Lead
* **Primary Scope:** Operating airlines, civil aircraft airframes with DGCA `VT-` registrations, and domestic route scheduling.
* **Entities Owned:**
  - `AIRLINE` (airline_id, airline_name, callsign_prefix, country_of_origin, contact_email)
  - `AIRCRAFT` (aircraft_reg_no, model, manufacturer, passenger_capacity, max_altitude_ft, cruising_speed_knots, airline_id)
  - `FLIGHT` (flight_id, flight_number, flight_date, airline_id, aircraft_reg_no, origin_airport, dest_airport, scheduled_departure, scheduled_arrival, actual_departure, actual_arrival, current_status)
* **Domain & Table-Level Constraints:**
  - Distinct endpoints: `CHECK (origin_airport <> dest_airport)`
  - Chronological consistency: `CHECK (scheduled_arrival > scheduled_departure)`
  - Unique schedule leg: `UNIQUE (flight_number, flight_date)`
* **Complex SQL Demonstrations:**
  - *Query 1 (Airline On-Time Performance - OTP):* Analyzes departed flights, counts on-time departures ($\le 15$ min buffer), and calculates carrier OTP percentage and average delay.
  - *Query 2 (High-Density Domestic Corridors):* Aggregates scheduled flights between city pairs with competing airline counts using `GROUP BY` and `HAVING`.
  - *Query 3 (Excessive Delay Correlated Subquery):* Identifies flights with departure delays exceeding 30 minutes.
  - *View 1 (`VIEW_FLIGHT_DISPATCH_BOARD`):* Comprehensive commercial schedule board.
  - *View 2 (`VIEW_AIRLINE_FLEET_SUMMARY`):* Fleet size and passenger capacity summaries.
* **UI Interface (`pages/2_Flight_Operations.py`):**
  - Live search and filterable dispatch schedule board.
  - Flight scheduling portal with real-time constraint enforcement.
  - State machine updater (`SCHEDULED` $\rightarrow$ `BOARDING` $\rightarrow$ `TAXIING` $\rightarrow$ `AIRBORNE` $\rightarrow$ `LANDED`).
  - Delay logger with human explanations and OTP charts.

---

### 📡 Member 3: Air Traffic Control Tower, En-Route Radar & Safety Lead
* **Primary Scope:** Indian Flight Information Regions (FIRs), licensed ATC officers, timestamped flight clearances, and safety incident reporting.
* **Entities Owned:**
  - `AIRSPACE_SECTOR` (sector_id, sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity)
  - `CONTROLLER` (controller_id, first_name, last_name, license_number, certification_level, shift_start, shift_end, assigned_sector_id)
  - `FLIGHT_CLEARANCE` (clearance_id, flight_id, controller_id, runway_id, clearance_type, issued_timestamp, assigned_altitude_ft, assigned_heading_deg)
  - `INCIDENT_LOG` (incident_id, flight_id, reported_by, incident_type, severity, incident_time, description)
* **Automated Safety Triggers:**
  - *Runway Collision Prevention Trigger (`trg_runway_clearance_safety_abort`):* Before inserting a `TAKEOFF` or `LANDING` clearance, queries Member 1's `RUNWAY.current_status`. If not `'AVAILABLE'`, immediately aborts the transaction with `Runway Safety Violation`.
  - *Runway Auto-Occupancy Trigger (`trg_runway_clearance_occupy`):* Upon clearance approval, automatically transitions target runway status to `'OCCUPIED'`.
  - *Flight State Progression Triggers (`trg_flight_status_takeoff`, `trg_flight_status_landing`):* Automatically transitions Member 2's `FLIGHT.current_status` to `AIRBORNE` or `LANDED` and logs timestamp.
* **Complex SQL Demonstrations:**
  - *Query 1 (Airborne Flights Dynamic Clearance Subquery):* Joins `FLIGHT`, `AIRLINE`, `AIRCRAFT`, `FLIGHT_CLEARANCE`, and `CONTROLLER` with correlated subquery `MAX(clearance_id)` to display active aircraft altitude vectors and authorizing officers.
  - *Query 2 (Controller Workload Distribution):* Evaluates controller clearances grouped by certification level using `GROUP BY` and `HAVING COUNT(*) > 0`.
  - *Query 3 (Safety Audit Dossier):* Multi-table incident reporting with priority case-weighting.
  - *Query 4 (Airspace Sector Utilization):* Density and controller staffing across FIR sectors.
* **UI Interface (`pages/3_ATC_Clearance_Console.py`):**
  - Clearance issuance console with live runway status checks and trigger violation alerts.
  - Black-box clearance audit ledger with multi-column filtering and CSV download.
  - Incident filing modal with severity grading (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - Controller workload and sector analytics charts.
  - Examiner evaluation walk-through guide with live SQL viewer.

---

## 4. Cross-Member Connectivity & The Flight Lifecycle

The diagram below details the operational and database-level dependencies connecting all three members across a complete flight lifecycle:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CROSS-MEMBER RELATIONAL COORDINATION MATRIX                               │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
 1. GATE ALLOCATION (Member 1)                      ▼
    • Ground staff assigns Gate T3-01A to Flight 6E-204 in GATE_ASSIGNMENT.
    • Trigger `trg_prevent_gate_double_booking` verifies zero time-overlap.
                                                    │
 2. FLIGHT DISPATCH (Member 2)                      ▼
    • Airline Dispatcher schedules Flight 6E-204 (DEL -> MAA) on A320neo (VT-ISN).
    • State moves from `SCHEDULED` ➔ `BOARDING` as turnaround progresses.
                                                    │
 3. TOWER PUSHBACK & TAXI (Member 3)                ▼
    • Controller logs PUSHBACK & TAXI instructions in FLIGHT_CLEARANCE.
    • Flight transitions to `TAXIING`.
                                                    │
 4. TAKEOFF SAFETY INTERLOCK (Member 3 ➔ Member 1)  ▼
    • Controller attempts TAKEOFF clearance on Runway 09/27 (DEL).
    • Trigger `trg_runway_clearance_safety_abort` inspects Member 1's RUNWAY status:
      - If OCCUPIED/CLOSED: Transaction ABORTED with Safety Violation error!
      - If AVAILABLE: Clearance approved, RUNWAY auto-marked OCCUPIED, FLIGHT auto-moves to `AIRBORNE`.
                                                    │
 5. EN-ROUTE RADAR SECTOR (Member 3)                ▼
    • Cruising through Delhi & Mumbai FIR sectors with ALTITUDE and HEADING clearances.
    • Sector traffic limits enforced against `AIRSPACE_SECTOR.max_capacity`.
    • Any near-miss or turbulence anomaly filed into `INCIDENT_LOG`.
                                                    │
 6. APPROACH & LANDING (Member 3 ➔ Member 1 & 2)    ▼
    • Landing clearance granted on Runway 07/25 (MAA).
    • Trigger automatically transitions FLIGHT to `LANDED`, sets actual arrival time, and logs landing.
                                                    │
 7. TURNAROUND COMPLETION (Member 1)                ▼
    • Aircraft docks at Chennai Gate T1-04; previous departure turnaround marked `COMPLETED`.
```

---

## 5. Normalization Analysis (1NF to BCNF)

All 11 relational entities satisfy **Boyce-Codd Normal Form (BCNF)**:

1. **First Normal Form (1NF):**
   - Every column contains purely atomic, non-decomposable values.
   - No repeating groups or multivalued attributes (e.g. runways, gates, and clearances are normalized into independent entities rather than stored as arrays in `AIRPORT` or `FLIGHT`).
2. **Second Normal Form (2NF):**
   - Every table is in 1NF.
   - All non-key attributes are fully functionally dependent on the entire primary key. In composite candidate keys like `(flight_number, flight_date)`, neither attribute alone determines airline or origin airport.
3. **Third Normal Form (3NF):**
   - Every table is in 2NF.
   - No transitive functional dependencies exist ($X \rightarrow Y \rightarrow Z$). Airport elevation and coordinates depend directly on `airport_code`, not through a runway or flight. Controller certifications depend solely on `controller_id`.
4. **Boyce-Codd Normal Form (BCNF):**
   - For every non-trivial functional dependency $X \rightarrow Y$, the determinant $X$ is a superkey. All relations have explicit single-column or composite superkeys, guaranteeing zero update anomalies.

---

## 6. Examiner Demonstration Script (Viva Evaluation)

Follow these steps to demonstrate the unified project during viva examination:

1. **Launch the Integrated Portal:**
   ```bash
   source .venv/bin/activate
   streamlit run app.py
   ```
2. **IOCC Overview (`app.py`):**
   - Show the 12 Indian hub metrics, live radar board, and the 3 collaborative operational wings.
3. **Demonstrate Member 1 (Ground Hubs):**
   - Navigate to `1_Airport_Ground_Control`.
   - Select `DEL` or `BOM`. Show the physical runway statuses and gate grid.
   - **Trigger Test:** Attempt to book Gate 1 during an overlapping time window; verify that the Gate Overlap Trigger aborts the request with a humanized conflict notice.
4. **Demonstrate Member 2 (Flight Operations):**
   - Navigate to `2_Flight_Operations`.
   - Show the filterable dispatch board.
   - **Constraint Test:** Attempt to schedule a flight with identical origin and destination (`DEL` $\rightarrow$ `DEL`); show error feedback.
   - Schedule a valid flight and log a departure delay; observe On-Time Performance (OTP) analytics update dynamically.
5. **Demonstrate Member 3 (ATC Tower & Safety):**
   - Navigate to `3_ATC_Clearance_Console`.
   - **Runway Safety Trigger Test:** Select an `OCCUPIED` runway and attempt to issue a `TAKEOFF` clearance. Show the safety alert banner intercepting the transaction.
   - Select an `AVAILABLE` runway and transmit clearance: show clearance issued, runway automatically flipped to `OCCUPIED`, and flight transitioned to `AIRBORNE`.
   - Show the Black-Box Audit Ledger and file an incident into `INCIDENT_LOG`.
6. **Show SQL Syllabus Concepts:**
   - In Tab 5 of Page 3 or Tab 5 of Page 2, show live executions of Joins, Correlated Subqueries, `GROUP BY`, and `HAVING`.
