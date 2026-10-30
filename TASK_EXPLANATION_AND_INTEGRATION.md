# SkyFlow ATCMS – Member 3 Task Explanations & Inter-Task Integration Guide

**Author:** Member 3 (Air Traffic Control Tower, En-Route & Safety Lead)  
**System:** SkyFlow Air Traffic Control & Airspace Management System (ATCMS)  
**Course:** Database Management Systems (DBMS)  

---

## 1. Executive Summary & Member 3 Scope

As **Member 3**, the operational domain centers on the mission-critical airspace and tower control layer:
1. **Three-Dimensional Airspace Architecture:** Indian Flight Information Regions (FIRs - Delhi `VIDF`, Mumbai `VABF`, Chennai `VOMF`, Kolkata `VECF`), ceiling/floor altitudes, and sector aircraft capacities.
2. **Controller Resource Management:** Licensed ATC officers (`CONTROLLER`), DGCA license validation, certification levels (`GROUND`, `TOWER`, `APPROACH`, `EN_ROUTE`), shift timings, and sector assignments.
3. **Flight Clearances & Audit Ledger:** High-integrity, immutable clearances (`PUSHBACK`, `TAXI`, `TAKEOFF`, `ALTITUDE_CHANGE`, `HEADING`, `LANDING`) acting as an audit black-box ledger.
4. **Safety & Anomaly Reporting:** Safety incident logging (`NEAR_MISS`, `RUNWAY_INCURSION`, `ALTITUDE_BUST`, `BIRD_STRIKE`, `WEATHER_DIVERT`) with severity grading (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
5. **Real-time Trigger Logic:** PL/pgSQL constraint triggers to prevent runway incursions and verify runway vacancy before takeoff/landing clearances.
6. **Analytics & Streamlit User Interface:** ATC Tower Radar Console, Clearance Stream, Incident Filing, and Workload Distribution analytics.

---

## 2. Completed Tasks & Technical Breakdown

*(This section is updated incrementally after each completed milestone.)*

### Task 1: DDL Schema, Constraints & Relational Modeling (Member 3 Domain)
* **Entities Created:**
  - `AIRSPACE_SECTOR`: Surrogate primary key `sector_id`, unique sector name, altitude boundary validation (`ceiling_altitude_ft > floor_altitude_ft >= 0`), positive max capacity constraint.
  - `CONTROLLER`: Surrogate primary key `controller_id`, unique DGCA license identifier (`license_number`), check constraints on certification levels (`GROUND`, `TOWER`, `APPROACH`, `EN_ROUTE`), shift intervals, and foreign key reference to `AIRSPACE_SECTOR`.
  - `FLIGHT_CLEARANCE`: Primary key `clearance_id`, foreign keys to `FLIGHT`, `CONTROLLER`, and optional `RUNWAY`, check constraint on clearance types, valid altitude range (0 to 60,000 ft), and heading (0 to 360 deg).
  - `INCIDENT_LOG`: Primary key `incident_id`, foreign key to `FLIGHT` and `CONTROLLER` (reporting officer), strict check constraints on incident categories and severity levels.
* **Database Normalization:** All relations satisfy **Boyce-Codd Normal Form (BCNF)**: all functional determinants are superkeys; no transitive or partial dependencies.

### Task 2: Advanced Database Logic – Automated Safety Triggers
* **Objective:** Prevent runway collisions, double-booking, and unauthorized takeoffs/landings on occupied or closed runways.
* **Implementation:**
  - Created PL/pgSQL trigger function `trg_fn_enforce_runway_safety()` attached to `FLIGHT_CLEARANCE` table before insert.
  - Intercepts any clearance with `clearance_type IN ('TAKEOFF', 'LANDING')`.
  - Checks target `RUNWAY.current_status`. If not `'AVAILABLE'`, raises `EXCEPTION` aborting the SQL transaction.
  - Automatically transitions runway status to `'OCCUPIED'` when clearance is approved.
  - In `db.py`, mirrored identical safety behavior for SQLite via triggers `trg_runway_clearance_safety_abort` and `trg_runway_clearance_occupy`.

### Task 3: Comprehensive Indian Aviation Dataset & Seed Scripts
* **Objective:** Populate realistic domestic aviation data for evaluation.
* **Implementation:**
  - Seeded 6 FIR sectors (`VIDF-N`, `VABF`, `VOMF`, `VECF`, and TMAs).
  - Seeded 8 licensed controllers across `GROUND`, `TOWER`, `APPROACH`, and `EN_ROUTE` certifications with shifts.
  - Seeded historical voice/data clearances and incident anomaly records.

### Task 4: Complex SQL Queries & Analytical Demonstrations
* **Objective:** Fulfill course grading rubrics for Joins, Subqueries, Aggregations, GROUP BY, and HAVING.
* **Implementation:**
  - **Query 1 (Multi-Table Join with Correlated Subquery):** Joins `FLIGHT`, `AIRLINE`, `AIRCRAFT`, `FLIGHT_CLEARANCE`, and `CONTROLLER` with subquery selecting `MAX(clearance_id)` to show each airborne aircraft's most recent altitude and heading instructions.
  - **Query 2 (Aggregations with GROUP BY & HAVING):** Groups clearances by controller and sector to calculate clearance workload and distinct aircraft handled, filtering with `HAVING COUNT(clearance_id) > 0`.
  - **Query 3 (Safety Audit Dossier):** Multi-table join classifying incident records with priority scores.
  - **Query 4 (Sector Capacity Monitoring):** Aggregates sector capacity and active controller supervision.

### Task 5: Application Development – Streamlit ATC Tower Console
* **Objective:** Provide a working graphical user interface enabling users and examiners to interact with the database.
* **Implementation:**
  - Built `pages/3_ATC_Clearance_Console.py` with 5 distinct functional tabs:
    1. *Clearance Issuance*: Live form interacting with database triggers; handles errors and updates statuses.
    2. *Black-Box Ledger*: Searchable clearance stream with CSV export.
    3. *Incident Filing*: Safety anomaly filing system.
    4. *Analytics*: Visual charts for Query 1, 2, and 4.
    5. *Examiner Live Demo Mode*: Evaluation walk-through guide with SQL code snippets.
  - Built root `app.py` for system overview and navigation across Member 1, Member 2, and Member 3 modules.

---

## 3. Inter-Task & Inter-Member Connectivity Matrix

The SkyFlow database is built on a unified relational schema where Member 3 directly integrates with and depends upon Member 1 and Member 2:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Member 1: Ground & Hub Lead                           │
│  - AIRPORT (airport_code, name, city, elevation)                            │
│  - RUNWAY (runway_id, airport_code, designator, current_status)             │
│  - GATE (gate_id, airport_code, terminal, gate_number, current_status)       │
│  - GATE_ASSIGNMENT (flight_id, gate_id, assigned_from, assigned_until)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                      Referenced by Runway & Airport
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Member 3: ATC Tower & Safety Lead                     │
│  - AIRSPACE_SECTOR (sector_id, name, floor_alt, ceiling_alt, capacity)      │
│  - CONTROLLER (controller_id, license_no, certification, assigned_sector_id)│
│  - FLIGHT_CLEARANCE (clearance_id, flight_id, controller_id, runway_id, ...) │
│  - INCIDENT_LOG (incident_id, flight_id, reported_by, type, severity, ...)  │
│                                                                             │
│  [TRIGGER] trg_runway_clearance_safety:                                     │
│    Reads RUNWAY.current_status owned by Member 1.                           │
│    Prevents TAKEOFF/LANDING if status is 'OCCUPIED' or 'CLOSED'.            │
│    Updates RUNWAY.current_status to 'OCCUPIED' on approved clearance.       │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
                      Referenced by Flight & Aircraft
                                       │
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Member 2: Flight Operations Lead                      │
│  - AIRLINE (airline_id, airline_name, callsign_prefix)                      │
│  - AIRCRAFT (aircraft_reg_no, model, passenger_capacity, airline_id)        │
│  - FLIGHT (flight_id, flight_number, origin_airport, dest_airport, status)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Integration Points:

1. **Member 3 $\leftrightarrow$ Member 1 (Runway Safety Coordination):**
   - **How it connects:** In `FLIGHT_CLEARANCE`, every `TAKEOFF` and `LANDING` clearance references `RUNWAY(runway_id)`.
   - **Trigger Interlock:** Before inserting a clearance, the trigger queries Member 1's `RUNWAY` table. If the runway is not `'AVAILABLE'`, it raises an exception (`Runway Safety Violation`), protecting ground operations against catastrophic runway incursions.
   - **State Transition:** Upon clearance approval, the trigger updates the runway's status to `'OCCUPIED'`.

2. **Member 3 $\leftrightarrow$ Member 2 (Flight Trajectory & Lifecycle Tracking):**
   - **How it connects:** Every clearance in `FLIGHT_CLEARANCE` and every safety entry in `INCIDENT_LOG` links to `FLIGHT(flight_id)` created by Member 2.
   - **Flight Status Progression:** As clearances are issued (`PUSHBACK` $\rightarrow$ `TAXI` $\rightarrow$ `TAKEOFF` $\rightarrow$ `ALTITUDE_CHANGE` $\rightarrow$ `LANDING`), the system tracks the progression of Member 2's flights through operational phases (`SCHEDULED` $\rightarrow$ `BOARDING` $\rightarrow$ `AIRBORNE` $\rightarrow$ `LANDED`).
   - **Audit Trail:** If an aircraft experiences an altitude bust or near-miss, Member 3's incident report references Member 2's flight and the operating airline.


---

## 4. Evaluation Demonstration Walkthrough (Syllabus Checklist)

When demonstrating Member 3's contribution to instructors or examiners:

1. **Launch the Application:**
   ```bash
   source .venv/bin/activate
   streamlit run app.py
   ```
2. **Navigate to Member 3 Console:**
   Select **`3_ATC_Clearance_Console`** from the left navigation sidebar.
3. **Demonstrate Runway Safety Trigger Collision (Negative Test):**
   - In Tab 1, select a runway marked **`OCCUPIED`** (e.g., Runway 1 at DEL).
   - Select Clearance Type **`TAKEOFF`**.
   - Click **Transmit Clearance**.
   - **Show Output:** The system intercepts the transaction and displays:
     > `⚠️ SAFETY INTERLOCK TRIGGERED: Runway is currently OCCUPIED or CLOSED! Clearance rejected to prevent runway incursion.`
   - This proves automated constraint and trigger enforcement at the database level.
4. **Demonstrate Valid Clearance & Auto-Transition (Positive Test):**
   - Select an **`AVAILABLE`** runway.
   - Click **Transmit Clearance**.
   - **Show Output:** Clearance is accepted, logged to `FLIGHT_CLEARANCE`, the flight state transitions to `AIRBORNE`, and the runway automatically updates to `OCCUPIED`.
5. **Demonstrate Black-Box Audit Ledger (Tab 2):**
   - Show the immutable chronological clearance stream with filter and CSV download options.
6. **Demonstrate Safety Incident Reporting (Tab 3):**
   - File an occurrence (e.g. Near-Miss, Bird Strike) with severity `HIGH` or `CRITICAL`.
   - Show it immediately recorded in `INCIDENT_LOG` with controller attribution.
7. **Demonstrate Syllabus SQL Concepts (Tab 4 & 5):**
   - Show **Query 1** (Multi-table join with correlated subquery for airborne flights).
   - Show **Query 2** (`GROUP BY` and `HAVING` workload evaluation).
   - Show **Query 4** (Sector capacity and active controller assignment).
