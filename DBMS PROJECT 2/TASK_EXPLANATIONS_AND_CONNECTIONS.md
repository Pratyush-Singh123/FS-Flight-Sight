# SkyFlow ATCMS – Member 2: Task Explanations & Inter-Task Connectivity Document

## Role: Member 2 – Commercial Fleet & Flight Operations Lead
**Domain Scope:** Airlines, DGCA Aircraft Registry, Domestic Flight Scheduling, Delay & On-Time Performance (OTP) Analytics, and Flight Dispatch Portal.

---

## Document Purpose
As mandated by course project guidelines and team division contracts:
1. Explain **what has been done** in each task with exact technical details.
2. Explain **why it was done** in accordance with DBMS principles and course evaluation rubrics.
3. Detail **how each task connects to Member 2's other tasks** (internal architectural coherence).
4. Detail **how each task connects to Member 1's tasks** (Airport Ground & Hub Management).
5. Detail **how each task connects to Member 3's tasks** (ATC Tower, Airspace Clearances & Safety Logs).

---

## Structured Task Breakdown

### Overview of Member 2 Pipeline
```
┌────────────────────────────────────────────────────────────────────────┐
│ Task 1: Member 2 Relational Schema, Integrity Constraints & Seed Data  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ feeds schema & baseline data
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Task 2: Advanced SQL Queries, Views & Analytical Logic                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ encodes business rules & reporting
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Task 3: Dual-Mode Database Access Layer & Connection Manager (`db.py`) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ powers data transactions & validation
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Task 4: Interactive Web UI – Flight Operations Portal (`pages/...`)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ verifies UI & DB integrity
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Task 5: End-to-End Test Suite & Constraint Verification Script         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ compiles academic deliverables
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Task 6: Academic Project Documentation & Normalization Analysis        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Relational Schema, Domain Constraints & Indian Fleet Seed Data

### 1. What was done in this task?
1. **Isolated Subsystem DDL (`member2_flight_ops_schema.sql`):**
   - Engineered the complete relational table definitions for Member 2's assigned entities: `AIRLINE`, `AIRCRAFT`, and `FLIGHT`.
   - Applied strict primary key definitions (`airline_id SERIAL`, `aircraft_reg_no VARCHAR(12)`, and `flight_id SERIAL`).
   - Implemented domain integrity constraints:
     - `passenger_capacity INT CHECK (passenger_capacity > 0)`: Prohibits aircraft records with non-positive capacities.
     - `max_altitude_ft INT CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000)`: Guards against aerodynamically invalid service ceilings.
     - `cruising_speed_knots INT CHECK (cruising_speed_knots > 0)`: Ensures positive physical airspeed.
     - `chk_flight_airports_distinct CHECK (origin_airport <> dest_airport)`: Prevents circular flights to the exact same aerodrome.
     - `chk_flight_schedule_chronology CHECK (scheduled_arrival > scheduled_departure)`: Enforces temporal causality (arrival must be strictly after departure).
     - `current_status CHECK (current_status IN ('SCHEDULED', 'BOARDING', 'TAXIING', 'AIRBORNE', 'LANDED', 'DIVERTED', 'CANCELLED'))`: Enforces a finite-state machine for flight lifecycle.
     - `uq_flight_number_date UNIQUE (flight_number, flight_date)`: Guarantees that a commercial flight number cannot be duplicate-scheduled on the same calendar day.
2. **Performance B-Tree Indexing:**
   - Created multi-column and single-column indexes on high-frequency search paths: `(flight_date, origin_airport, dest_airport)`, `current_status`, `airline_id`, and `aircraft_reg_no`.
3. **Rich Indian Civil Aviation Seed Dataset:**
   - Populated 6 major operating Indian airlines (IndiGo, Air India, SpiceJet, Akasa Air, Vistara, AIX Connect) with official callsign prefixes and dispatch contact addresses.
   - Populated 13 commercial aircraft registered under DGCA rules using realistic Indian civil tail prefixes (`VT-ISN`, `VT-IFP`, `VT-EXF`, `VT-CIO`, `VT-ALQ`, `VT-SLA`, `VT-SGZ`, `VT-YAA`, `VT-YAE`, `VT-TVA`, `VT-TTB`, `VT-IXC`).
   - Populated 14 flight schedules reflecting major high-density Indian flight routes (`DEL-BOM`, `BOM-DEL`, `DEL-BLR`, `BOM-BLR`, `BLR-MAA`, `DEL-HYD`, `DEL-CCU`, `BOM-GOX`, `DEL-PNQ`) with diverse operational states (`SCHEDULED`, `BOARDING`, `TAXIING`, `AIRBORNE`, `LANDED`) and varied departure delay profiles (on-time, +5 min, +42 min, +50 min) to enable rigorous On-Time Performance (OTP) testing.

### 2. Why was this done?
- **DBS Syllabus Compliance:** Sections 5, 7, and 8 of the DBS Project Instructions require identifying entities, attributes, primary/foreign keys, establishing referential integrity, applying check constraints, and seeding realistic domain data.
- **Relational Integrity:** Catching scheduling errors (such as identical departure/arrival airports or negative flight durations) at the DBMS engine layer via CHECK constraints guarantees that corrupt records can never enter the database regardless of UI bugs.

### 3. How does Task 1 connect to Member 2's other tasks?
- **Feeds Task 2 (Advanced SQL Queries & Views):** The schema structures and sample data directly provide the rows, keys, and foreign-key join paths needed for On-Time Performance calculations, route density grouping, and subquery delay filtering.
- **Feeds Task 3 (Database Access Layer):** Provides the physical table structure (`FLIGHT`, `AIRLINE`, `AIRCRAFT`) that `db.py` queries, inserts into, and updates.
- **Feeds Task 4 (Streamlit UI):** Populates dropdown lists (airlines, aircraft, origin, destination) and provides initial flight records for the Flight Dispatch Portal.
- **Feeds Task 5 (Testing & Verification):** Provides the target tables and constraints tested by automated scripts (`verify_member2.py`).

### 4. How does Task 1 connect to Member 1's tasks (Airport Ground & Hubs)?
- **Airport References (`origin_airport`, `dest_airport`):** Member 2's `FLIGHT` table references Member 1's `AIRPORT(airport_code)`. A flight can only depart from or arrive at an aerodrome registered by Member 1.
- **Gate Turnaround Integration (`GATE_ASSIGNMENT`):** Member 1 assigns physical gates to Member 2's flights via `GATE_ASSIGNMENT.flight_id -> FLIGHT.flight_id`. Member 1's gate board cannot function without Member 2's flights.
- **Runway Surface Movement:** Member 1 monitors runway availability, while Member 2's flights transition between `TAXIING`, `AIRBORNE`, and `LANDED`.

### 5. How does Task 1 connect to Member 3's tasks (ATC Clearances & Safety Logs)?
- **Clearance Issuance Target (`FLIGHT_CLEARANCE`):** Member 3 issues pushback, taxi, takeoff, altitude change, and landing clearances to individual flights via `FLIGHT_CLEARANCE.flight_id -> FLIGHT.flight_id`. Member 3's ATC console relies completely on active flights scheduled by Member 2.
- **Safety Incident Logging (`INCIDENT_LOG`):** When Member 3's controllers log near-misses, bird strikes, or diversions, the incident references `INCIDENT_LOG.flight_id -> FLIGHT.flight_id`.
- **Status Coordination:** When Member 3 issues a `TAKEOFF` clearance, Member 2's flight transitions from `TAXIING` to `AIRBORNE`.



---

## Task 2: Advanced SQL Queries, Relational Views & Operational Analytics

### 1. What was done in this task?
1. **Relational Views (`member2_queries_and_views.sql`):**
   - **`VIEW_FLIGHT_DISPATCH_BOARD`:** Encapsulates a 4-table relational join between `FLIGHT`, `AIRLINE`, `AIRCRAFT`, origin `AIRPORT`, and dest `AIRPORT`. It dynamically calculates departure delay in minutes using epoch timestamp arithmetic (`EXTRACT(EPOCH FROM ...) / 60`).
   - **`VIEW_AIRLINE_FLEET_SUMMARY`:** Pre-aggregates fleet metrics across carriers, computing count of aircraft (`COUNT`), total seats (`SUM`), average seats (`AVG`), maximum altitude service ceiling (`MAX`), and average cruise airspeed (`AVG`).
   - **`VIEW_CARRIER_OTP_ANALYTICS`:** Implements the official DGCA 15-minute standard for On-Time Performance (OTP). It calculates scheduled legs, departed legs, on-time departures, delayed departures, OTP percentage, and average delay minutes per carrier using conditional aggregation (`SUM(CASE WHEN ...)`).
2. **Advanced Demonstration SQL Queries:**
   - **Query 1 (Carrier OTP Report):** Demonstrates `JOIN`, `CASE` branching expressions, multiple aggregate functions (`COUNT`, `SUM`, `AVG`), date arithmetic (`+ INTERVAL '15 minutes'`), `GROUP BY`, and multi-column `ORDER BY`.
   - **Query 2 (High-Density Corridors):** Evaluates route congestion. Demonstrates `GROUP BY` on route pairs, string concatenation (`||`), distinct count (`COUNT(DISTINCT ...)`), and post-aggregation filtering via `HAVING COUNT(flight_id) >= 2`.
   - **Query 3 (Excessive Delays - Correlated Subquery):** Detects flights experiencing > 30 minutes of departure delay. Demonstrates a subquery with `WHERE flight_id IN (SELECT sub_f.flight_id FROM FLIGHT sub_f WHERE ...)` and multi-table joins to retrieve carrier dispatch emails.
   - **Query 4 (Fleet Capacity vs. Fleet Average - Scalar Subquery):** Compares individual aircraft passenger capacities against the database-wide average using a scalar subquery `WHERE ac.passenger_capacity > (SELECT AVG(passenger_capacity) FROM AIRCRAFT)`.
   - **Query 5 (Airborne Radar Telemetry):** Filters live flights with `current_status = 'AIRBORNE'` and sorts by chronological departure.
3. **Core DML Operations (INSERT, UPDATE, DELETE):**
   - Established parameterized transactional SQL templates for scheduling flights, transitioning operational states, adjusting delay minutes, and safe flight deletion.

### 2. Why was this done?
- **DBS Syllabus Compliance:** Sections 10, 11, and 13 of the DBS Project Instructions mandate demonstrating:
  - Filtering (`WHERE`) and sorting (`ORDER BY`).
  - Aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).
  - `GROUP BY` and `HAVING` clauses.
  - Multi-table `JOIN`s and subqueries (both scalar and correlated).
  - Database `VIEW`s to simplify client application logic and decouple UI from physical schema structure.
  - Data manipulation operations (`INSERT`, `UPDATE`, `DELETE`).
- **Operational Realism:** In modern airline dispatch, airlines and ATC command centers constantly compute OTP rates, delay cascades, and route bottlenecks. Views provide zero-redundancy virtual tables that always reflect live database state.

### 3. How does Task 2 connect to Member 2's other tasks?
- **Relies on Task 1:** Task 2's queries execute directly against the `AIRLINE`, `AIRCRAFT`, and `FLIGHT` schema and data seeded in Task 1.
- **Feeds Task 3 (Database Access Layer):** The SQL logic defined here is wrapped as clean Python helper methods in `db.py` (`get_otp_analytics()`, `get_route_density_analytics()`, `get_fleet_summary()`).
- **Feeds Task 4 (Streamlit UI):** Powers the interactive analytical dashboards, charts, and data tables in `pages/2_Flight_Operations.py`. Evaluators can view live OTP charts and inspect the underlying SQL queries directly in the UI.
- **Feeds Task 5 (Testing & Verification):** All queries are executed and validated by `verify_member2.py`.

### 4. How does Task 2 connect to Member 1's tasks (Airport Ground & Hubs)?
- **Origin & Destination Aggregation:** Task 2 joins Member 1's `AIRPORT` table to translate ICAO/IATA codes (`DEL`, `BOM`, `BLR`) into city names and airport descriptions for flight dispatch and route reports.
- **Congestion Analysis:** When Task 2 identifies high-density routes (e.g., `DEL -> BOM`), Member 1 can cross-reference this with runway utilization and gate occupancy at Delhi and Mumbai hubs to prevent ground congestion.

### 5. How does Task 2 connect to Member 3's tasks (ATC Clearances & Safety Logs)?
- **Delay Cascades & Clearance Workload:** Member 2's delay analytics pinpoint flights that were delayed on the ground. Member 3 can correlate these delays with controller workload (`FLIGHT_CLEARANCE`) or incident logs (`INCIDENT_LOG` like bird strikes or runway incursions).
- **Active Airborne Feed:** Task 2's airborne flight query provides the exact operational flight list that Member 3 uses in the ATC Tower Radar Console to issue heading vectors and cruising altitude clearances.


---

## Task 3: Dual-Mode Database Connection & Data Access Layer (`db.py`)

### 1. What was done in this task?
1. **Engine-Agnostic Database Connector:**
   - Implemented `db.py` to support dual database modes:
     - **PostgreSQL Mode:** Seamlessly activates when `DATABASE_URL` or `PG_CONNECTION_STRING` is detected.
     - **Local Zero-Config SQLite Mode (`skyflow_atc.db`):** Provides instant, friction-free local execution without requiring an external PostgreSQL daemon or service configuration on student or evaluator laptops.
   - Configured SQLite with `PRAGMA foreign_keys = ON` to strictly enforce relational referential integrity at the engine level.
2. **Automated Schema & Seed Migration:**
   - Built an embedded initialization routine (`init_database()`) that automatically deploys tables for all 3 members (`AIRPORT`, `AIRLINE`, `AIRCRAFT`, `RUNWAY`, `GATE`, `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT`, `GATE_ASSIGNMENT`, `FLIGHT_CLEARANCE`, `INCIDENT_LOG`) and seeds realistic Indian aviation data if absent.
3. **Comprehensive Member 2 Data Access Object (DAO) Interface:**
   - **Create (INSERT):** `add_flight(...)` performs pre-validation and transactional insertion with explicit exception handling for UNIQUE, CHECK, and FOREIGN KEY violations.
   - **Read (SELECT):** `get_flights(...)` supports flexible multi-criteria filtering (search text, status, origin, destination, airline) with multi-table joins.
   - **Update (UPDATE):** `update_flight_status(...)` and `apply_departure_delay(...)` modify live flight timestamps and operational states.
   - **Delete (DELETE / Cancel):** `cancel_or_delete_flight(...)` offers soft cancellation or hard deletion with protection against foreign-key constraint violations when child records exist in `GATE_ASSIGNMENT` or `FLIGHT_CLEARANCE`.
   - **Analytical Query Executors:** Implemented dedicated methods for OTP analytics, route density calculations, excessive delay investigation, and fleet benchmarking.
   - **Evaluator Query Console:** Implemented `execute_raw_sql(...)` to allow course evaluators to run arbitrary SQL queries live from the application interface.

### 2. Why was this done?
- **DBS Syllabus Compliance:** Sections 8, 9, and 10 of the DBS Project Instructions require connecting the application to the database and demonstrating meaningful database operations: adding records, updating records, deleting records, searching/retrieving records, displaying information, and generating reports.
- **Portability & Demonstration Reliability:** Evaluators may run the project in varied environments (Windows/macOS/Linux) where a PostgreSQL server may not be running. Providing dual PostgreSQL/SQLite engine support guarantees 100% immediate functionality while strictly adhering to SQL standards.

### 3. How does Task 3 connect to Member 2's other tasks?
- **Executes Task 1 & Task 2:** Task 3 converts the static schema and SQL queries designed in Tasks 1 and 2 into active Python functions and methods.
- **Powers Task 4 (Streamlit UI):** Serves as the backend for the Flight Dispatch Portal. Every button click, form submission, filter change, and chart render in `pages/2_Flight_Operations.py` calls methods in `db.py`.
- **Enables Task 5 (Test Automation):** Provides programmatic access for the automated verification test script.

### 4. How does Task 3 connect to Member 1's tasks (Airport Ground & Hubs)?
- **Hub Master Data Lookup:** When dispatchers schedule a flight or filter flight boards in Member 2's module, `db.get_airports()` queries Member 1's `AIRPORT` table to populate valid origin and destination airport dropdowns.
- **Referential Integrity Enforcement:** Member 2's `add_flight()` will fail with a foreign key violation if an invalid airport code is submitted, respecting Member 1's authority over airport infrastructure.

### 5. How does Task 3 connect to Member 3's tasks (ATC Clearances & Safety Logs)?
- **Shared Operational Target:** Member 3's ATC radar console queries `get_flights()` to display airborne targets and issue clearance commands.
- **Referential Safety on Deletion:** If an evaluator attempts to hard-delete a flight that has an active clearance issued by Member 3, `cancel_or_delete_flight()` detects the foreign key lock, catches the exception, and suggests soft-cancellation instead to preserve black-box audit integrity.


---

## Task 4: Streamlit Multi-Page UI Implementation (`app.py` & `pages/2_Flight_Operations.py`)

### 1. What was done in this task?
1. **System Entry & Architecture Dashboard (`app.py`):**
   - Configured multi-page Streamlit application structure as specified in Section 13 (Option A) of the Technical Blueprint.
   - Designed top-level status widgets summarizing total registered hubs, aircraft, and active domestic flights.
   - Detailed the 3-member parallel development architecture and provided clear visual guidance directing evaluators to Member 2's portal.
2. **Comprehensive Member 2 Portal (`pages/2_Flight_Operations.py`):**
   - **Tab 1 (Dispatch Board & Multi-Criteria Search):**
     - Live search bar filtering by flight number or aircraft tail registration.
     - Multi-dimensional filters: flight status (`SCHEDULED`, `BOARDING`, `TAXIING`, `AIRBORNE`, `LANDED`), origin hub, destination hub, and operating airline.
     - Flight Inspector drawer: expandable card revealing aircraft specs, passenger capacity, delay minutes, and airline contact emails.
   - **Tab 2 (Schedule New Flight - INSERT):**
     - Form with reactive dropdowns: selecting an airline automatically filters available aircraft to airframes belonging exclusively to that carrier.
     - Origin and destination selectors linked to official Indian airports.
     - Immediate database constraint validation: tests and prevents identical origin/destination or arrival timestamps that precede departures, catching and rendering DBMS errors clearly.
   - **Tab 3 (Operational State Transition & Delay Logger - UPDATE):**
     - State machine transition tool: steps flights through operational stages (`SCHEDULED` ➔ `BOARDING` ➔ `TAXIING` ➔ `AIRBORNE` ➔ `LANDED`). Automatically generates departure or touchdown timestamps on state change.
     - Ground delay logger: applies delay minutes and recalibrates actual departure timestamps.
   - **Tab 4 (Flight Cancellation & Removal - DELETE):**
     - Dual cancellation policy: Soft-cancel (updates state to `CANCELLED`, preserving historical referential integrity) vs. Hard-delete (`DELETE FROM FLIGHT`), with referential constraint protection against dependent gate reservations or ATC clearances.
   - **Tab 5 (Operations Analytics & Course SQL Demonstrator):**
     - Interactive On-Time Performance (OTP) summary table and Altair/Streamlit bar chart.
     - High-density corridor analysis table with interactive threshold sliders.
     - Excessive departure delays audit log (>30 mins).
     - Fleet capacity benchmark table.
     - Live SQL Query Terminal allowing evaluators to load syllabus query templates or write custom SQL statements and view tabular results in real time.
3. **Cross-Member Coordination Pages (`pages/1_...` and `pages/3_...`):**
   - Created clear interface stubs showing Member 1's runway/gate tables and Member 3's controllers/sectors/airborne target feeds, maintaining a cohesive project structure.

### 2. Why was this done?
- **DBS Syllabus Compliance:** Sections 9, 10, 13, and 15 of the DBS Project Instructions require a working application interface that performs actual database operations (adding, updating, deleting, searching, displaying records, and generating reports) rather than static mockup code.
- **Visual Validation:** Course evaluators require interactive proof that DBMS constraints and business logic work end-to-end through a user interface.

### 3. How does Task 4 connect to Member 2's other tasks?
- **Front-End for Task 3 (`db.py`):** Every interactive component in Task 4 calls the corresponding Python DAO method implemented in Task 3.
- **Visualizes Task 1 & Task 2:** Displays the schema structures and seeds from Task 1, and renders the analytical calculations and views formulated in Task 2.
- **Subject of Task 5 (Verification):** All workflows implemented in the UI are automated and verified via `verify_member2.py`.

### 4. How does Task 4 connect to Member 1's tasks (Airport Ground & Hubs)?
- **Ground Movement Awareness:** Member 2's UI shows whether a flight is `BOARDING` or `TAXIING`. Ground controllers (Member 1) use this status to verify that the aircraft is occupying an allocated gate or pushback alley.
- **Airport Hub Selector:** Tab 2's flight scheduling form directly populates origin and destination choices from Member 1's `AIRPORT` master table.

### 5. How does Task 4 connect to Member 3's tasks (ATC Clearances & Safety Logs)?
- **Flight Readiness for Clearance:** When Member 2's dispatch portal transitions a flight to `TAXIING`, it appears on Member 3's ATC Clearance Console as ready for runway takeoff clearance.
- **Airborne Telemetry Link:** When Member 2 transitions a flight to `AIRBORNE`, Member 3's En-Route controller console immediately tracks the flight in the regional airspace sector.


---

## Task 5: End-to-End Testing & Constraint Verification Script (`verify_member2.py`)

### 1. What was done in this task?
1. **Automated Verification Harness (`verify_member2.py`):**
   - Engineered an automated Python test script executing 17 comprehensive unit, integration, and constraint tests covering every operational requirement of Member 2.
2. **Constraint Enforcement Validation:**
   - Programmatically validated that attempting to insert a circular flight (`origin_airport = dest_airport`) is immediately caught and rejected.
   - Programmatically validated that attempting to insert an inverted flight schedule (`scheduled_arrival <= scheduled_departure`) is rejected.
   - Validated that duplicate scheduling on the composite key `(flight_number, flight_date)` triggers a unique constraint rejection.
3. **End-to-End CRUD Lifecycle Execution:**
   - **INSERT:** Successfully created a test flight leg (`6E-TST-XXXX`) with realistic parameters.
   - **SELECT:** Queried the record back and verified data integrity across relational attributes.
   - **UPDATE:** Transitioned the test flight state to `AIRBORNE` and verified that actual departure timestamps were properly set.
   - **UPDATE:** Applied a 25-minute ground delay and verified timetable recalculation.
   - **DELETE:** Permanently deleted the test leg and confirmed that rowcount decreased cleanly.
4. **Analytical Query & View Testing:**
   - Executed and validated all 4 course demonstration queries (Carrier OTP, High-Density Corridors with `HAVING`, Correlated Subquery for delays > 30 minutes, Scalar Subquery for fleet capacity).
   - Validated the custom raw SQL query executor.
5. **Execution Results:** All 17 tests passed with a 100.0% success rate.

### 2. Why was this done?
- **DBS Syllabus Compliance:** Sections 8 and 15 of the DBS Project Instructions require verifying that the database correctly supports the application requirements and that students can demonstrate representative SQL queries, outputs, and constraint validation.
- **Robustness:** Automated regression testing ensures that changes made by Member 1 (ground tables) or Member 3 (clearance tables) never silently break Member 2's flight operations subsystem.

### 3. How does Task 5 connect to Member 2's other tasks?
- **Validates Tasks 1, 2, 3, and 4:** Task 5 is the test harness that exercises the DDL constraints of Task 1, the SQL logic of Task 2, the Python DAO methods of Task 3, and the operational workflows mirrored in Task 4's UI.
- **Provides Concrete Output Data for Task 6:** The query results and test outcomes generated during this task directly supply the execution outputs documented in Member 2's academic report.

### 4. How does Task 5 connect to Member 1's tasks (Airport Ground & Hubs)?
- **Airport Foreign Key Verification:** The test suite verifies that foreign-key references to Member 1's `AIRPORT` table (`DEL`, `BOM`, `BLR`) function correctly and enforce referential integrity.
- **Regression Guard for Hub Changes:** If Member 1 modifies the `AIRPORT` schema or drops an airport code, `verify_member2.py` immediately catches the break before submission.

### 5. How does Task 5 connect to Member 3's tasks (ATC Clearances & Safety Logs)?
- **Referential Constraint Defense:** The test suite verifies that flights can be queried and modified safely without causing orphaned records in Member 3's `FLIGHT_CLEARANCE` or `INCIDENT_LOG` tables.
- **Verification of Shared Flight Keys:** Ensures that `flight_id` surrogate keys generated in Member 2's insertion tests adhere to the foreign key contract expected by Member 3.


---

## Task 6: Academic Project Documentation & Report (`Member_2_Flight_Operations_Report.md`)

### 1. What was done in this task?
1. **Comprehensive Academic Report Compilation (`Member_2_Flight_Operations_Report.md`):**
   - Authored the formal project documentation for Member 2 strictly adhering to Section 14 of the official DBS Project Instructions.
   - Articulated the problem statement and system objectives specific to commercial fleet and flight operations.
   - Documented the attribute dictionary, primary keys, foreign keys, and referential integrity rules.
   - Provided a visual ASCII Entity-Relationship (ER) diagram illustrating internal relationships (`AIRLINE` 1:N `AIRCRAFT`, `AIRLINE` 1:N `FLIGHT`, `AIRCRAFT` 1:N `FLIGHT`) and cross-member relationships to `AIRPORT`, `GATE_ASSIGNMENT`, `FLIGHT_CLEARANCE`, and `INCIDENT_LOG`.
   - Developed a formal Normalization Analysis rigorously proving 1NF, 2NF, 3NF, and Boyce-Codd Normal Form (BCNF) compliance, proving why update/delete anomalies are prevented.
   - Documented the 4 syllabus demonstration queries along with actual tabular output datasets generated from the database.
   - Described the multi-page Streamlit application, transactional database access layer (`db.py`), parameterization, and error handling.
   - Compiled the 17-test verification results and concluded with key architectural observations.

### 2. Why was this done?
- **DBS Syllabus Compliance:** Section 14 of the DBS Project Instructions mandates submitting comprehensive documentation covering problem statement, objectives, functional modules, ER diagram, relational schema, normalization, important SQL queries with screenshots/outputs, and application interaction description.
- **Academic Rigor:** Proving normalization up to BCNF and presenting reproducible query outputs with business justifications ensures maximum scoring during course project viva and grading.

### 3. How does Task 6 connect to Member 2's other tasks?
- **Synthesizes Tasks 1 Through 5:** Task 6 documents the exact schema built in Task 1, the SQL queries crafted in Task 2, the data access layer created in Task 3, the user interface developed in Task 4, and the test metrics verified in Task 5.
- **Completes the Deliverable Chain:** Acts as the unified reference document binding all code, schemas, and queries together into a polished submission artifact.

### 4. How does Task 6 connect to Member 1's tasks (Airport Ground & Hubs)?
- **Shared Schema Documentation:** Details how Member 2's `FLIGHT` table consumes Member 1's `AIRPORT` master entities and provides the `flight_id` foreign key that Member 1's `GATE_ASSIGNMENT` table requires for terminal turnaround reservations.
- **Joint Report Integration:** Member 1 can take the ER diagram and schema definitions in this report and directly plug them into their combined group submission.

### 5. How does Task 6 connect to Member 3's tasks (ATC Clearances & Safety Logs)?
- **Clearance Subsystem Handshake:** Explains the relational coupling between Member 2's active flight legs and Member 3's `FLIGHT_CLEARANCE` and `INCIDENT_LOG` audit ledger.
- **Evaluation Preparedness:** Prepares the team for the joint presentation script specified in Section 14 of the Technical Blueprint, where Member 2 schedules a flight and transitions it so Member 3 can issue ATC clearances.
