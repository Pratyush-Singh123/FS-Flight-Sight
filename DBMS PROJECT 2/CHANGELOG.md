# SkyFlow ATCMS - Member 2 Change Log (Audit Ledger)

This document tracks every single file creation, modification, schema update, query addition, and implementation change performed by **Member 2 (Commercial Fleet & Flight Operations Lead)**.

---

## Task Index
- [Task 1: Member 2 Relational Schema, Constraints & Indian Fleet Seed Data](#task-1-member-2-relational-schema-constraints--indian-fleet-seed-data)
- [Task 2: Member 2 Advanced SQL Queries, Views & Analytical Logic](#task-2-member-2-advanced-sql-queries-views--analytical-logic)
- [Task 3: Dual-Mode Database Connection & Data Access Layer (`db.py`)](#task-3-dual-mode-database-connection--data-access-layer-dbpy)
- [Task 4: Streamlit Multi-Page UI Implementation (`app.py` & `pages/2_Flight_Operations.py`)](#task-4-streamlit-multi-page-ui-implementation-apppy--pages2_flight_operationspy)
- [Task 5: End-to-End Testing & Verification Script (`verify_member2.py`)](#task-5-end-to-end-testing--verification-script-verify_member2py)
- [Task 6: Academic Project Documentation & Report (`Member_2_Flight_Operations_Report.md`)](#task-6-academic-project-documentation--report-member_2_flight_operations_reportmd)

---

## Log Entries

### Task 1: Member 2 Relational Schema, Constraints & Indian Fleet Seed Data
* **Timestamp:** 2026-10-30 18:23:10
* **Author:** Member 2 (Commercial Fleet & Flight Operations Lead)
* **Files Created/Modified:**
  - `member2_flight_ops_schema.sql` (Created):
    - DDL for `AIRLINE`: surrogate PK `airline_id`, unique `airline_name`, `callsign_prefix`, and `contact_email`.
    - DDL for `AIRCRAFT`: PK `aircraft_reg_no`, check constraints on `passenger_capacity > 0`, `max_altitude_ft BETWEEN 1000 AND 60000`, `cruising_speed_knots > 0`, and FK to `AIRLINE(airline_id) ON DELETE CASCADE`.
    - DDL for `FLIGHT`: PK `flight_id`, unique `(flight_number, flight_date)`, FKs to `AIRLINE`, `AIRCRAFT`, origin `AIRPORT`, dest `AIRPORT`. Check constraints `origin_airport <> dest_airport`, `scheduled_arrival > scheduled_departure`, status check constraint.
    - 5 Performance B-Tree Indexes on flight search paths (`idx_flight_dates`, `idx_flight_status`, `idx_flight_carrier`, `idx_flight_aircraft`, `idx_aircraft_carrier`).
    - Seed data: 6 major Indian carriers (IndiGo, Air India, SpiceJet, Akasa Air, Vistara, AIX Connect), 13 DGCA-registered aircraft (`VT-` series), and 14 realistic scheduled/active flight legs covering prime corridors (`DEL-BOM`, `BOM-DEL`, `DEL-BLR`, `BOM-BLR`, etc.) with varying delay distributions.
* **Scope:** Delivers standalone and integrated relational definitions for Member 2's domain.


### Task 2: Member 2 Advanced SQL Queries, Views & Analytical Logic
* **Timestamp:** 2026-10-30 18:24:18
* **Author:** Member 2 (Commercial Fleet & Flight Operations Lead)
* **Files Created/Modified:**
  - `member2_queries_and_views.sql` (Created):
    - View 1: `VIEW_FLIGHT_DISPATCH_BOARD` (Consolidated multi-table join view with departure delay computations).
    - View 2: `VIEW_AIRLINE_FLEET_SUMMARY` (Carrier-level aggregate metrics: count of aircraft, total seats, average seats, maximum altitude ceiling, and average speed).
    - View 3: `VIEW_CARRIER_OTP_ANALYTICS` (Standardized On-Time Performance analytical view using 15-minute buffer).
    - Query 1: Airline On-Time Performance (OTP) summary report using `COUNT`, `SUM(CASE ...)`, date intervals, and percentage calculation.
    - Query 2: High-Density Airspace Corridors & Bottleneck Analysis using `GROUP BY`, `HAVING COUNT(*) >= 2`, `MIN`, `MAX`, and multi-table joins.
    - Query 3: Excessive Delays Investigation using a Correlated Subquery (`WHERE flight_id IN (SELECT ...)`), timestamp arithmetic, and carrier contacts.
    - Query 4: Aircraft Fleet Utilization vs. Industry Average using a Scalar Subquery (`WHERE passenger_capacity > (SELECT AVG(...) ...)`).
    - Query 5: Active Airborne Flight Vectors with Airframe Specs.
    - DML operation templates for INSERT, UPDATE, and DELETE.
* **Scope:** Fulfills all syllabus requirements for complex SQL querying, aggregation, filtering, subqueries, and database views.

### Task 3: Dual-Mode Database Connection & Data Access Layer (`db.py`)
* **Timestamp:** 2026-10-30 18:27:35
* **Author:** Member 2 (Commercial Fleet & Flight Operations Lead)
* **Files Created/Modified:**
  - `db.py` (Created):
    - Multi-engine connectivity adapter supporting PostgreSQL (via environment variables `DATABASE_URL` / `PG_CONNECTION_STRING`) and zero-configuration local SQLite (`skyflow_atc.db`).
    - Automatic initialization and verification of all 11 SkyFlow ATCMS tables and initial seed records.
    - Full Member 2 Data Access Object (DAO) methods:
      - `get_airlines()`: Lists registered Indian carriers.
      - `get_aircraft(airline_id)`: Fetches airline-filtered fleet records with registration details.
      - `get_airports()`: Fetches 12 major Indian hubs.
      - `get_flights(search, status, origin, dest, airline_id)`: Multi-criteria flight filter with joined carrier and aerodrome metadata.
      - `get_flight_by_id(flight_id)`: Detailed flight leg lookup.
      - `add_flight(...)`: INSERT operation enforcing domain rules (`origin <> dest`, `arrival > departure`, unique constraints).
      - `update_flight_status(...)`: UPDATE operation transitioning operational lifecycle states.
      - `apply_departure_delay(...)`: UPDATE operation computing delay timestamps and advancing status.
      - `cancel_or_delete_flight(...)`: Safe DELETE / cancellation preserving referential integrity against gate assignments and clearance logs.
      - `get_otp_analytics()`: Computes carrier On-Time Performance using 15-minute buffer.
      - `get_route_density_analytics()`: Identifies high-density corridors using `GROUP BY` and `HAVING`.
      - `get_excessive_delays()`: Correlated subquery fetching flights delayed > 30 minutes.
      - `get_fleet_capacity_report()`: Scalar subquery benchmarking aircraft against average seating capacity.
      - `execute_raw_sql(sql_query)`: Custom SQL query runner for live evaluator demonstration.
* **Scope:** Provides a robust, thread-safe, transactional data access layer connecting application UI with relational database engines.

### Task 4: Streamlit Multi-Page UI Implementation (`app.py` & `pages/2_Flight_Operations.py`)
* **Timestamp:** 2026-10-30 18:33:55
* **Author:** Member 2 (Commercial Fleet & Flight Operations Lead)
* **Files Created/Modified:**
  - `app.py` (Created):
    - Main multi-page entry point providing system health metrics, active DBMS engine display, 3-member WBS breakdown, and relational catalog status.
  - `pages/2_Flight_Operations.py` (Created):
    - Full Member 2 Flight Operations & Dispatch Portal featuring 5 functional tabs:
      - Tab 1: Dispatch Board & Multi-Filter Search with Flight Inspector (SELECT).
      - Tab 2: Schedule New Flight Form with client-side & DB constraint validation (INSERT).
      - Tab 3: Operational State Transition Pipeline & Delay Logger (UPDATE).
      - Tab 4: Flight Cancellation & Deletion with Foreign Key Guard (DELETE).
      - Tab 5: Operations Analytics, Carrier OTP Charting, High-Density Corridors, and Live SQL Query Terminal (REPORTS).
  - `pages/1_Airport_Ground_Control.py` (Created):
    - Coordination stub for Member 1 (Airport Ground & Hub Management).
  - `pages/3_ATC_Clearance_Console.py` (Created):
    - Coordination stub for Member 3 (ATC Tower Clearances & Safety Logs).
* **Scope:** Delivers a modern, fully functional user interface connected directly to the database layer as required by Section 9 of the DBS Project Instructions.

### Task 5: End-to-End Testing & Verification Script (`verify_member2.py`)
* **Timestamp:** 2026-10-30 18:36:10
* **Author:** Member 2 (Commercial Fleet & Flight Operations Lead)
* **Files Created/Modified:**
  - `verify_member2.py` (Created):
    - Automated test harness covering 17 granular checks across 4 test categories:
      1. Database connectivity and schema counts for `AIRLINE`, `AIRCRAFT`, and `FLIGHT`.
      2. Domain integrity constraint rejection tests:
         - Circular flight (`origin_airport == dest_airport`) rejection.
         - Inverted schedule chronology (`scheduled_arrival <= scheduled_departure`) rejection.
         - Unique key duplicate rejection (`flight_number, flight_date`).
      3. Full CRUD verification:
         - Dynamic INSERT of parameterized test flight leg.
         - Multi-column SELECT verification.
         - State transition UPDATE to `AIRBORNE` with actual timestamp injection.
         - Schedule adjustment UPDATE applying a 25-minute ground delay.
         - Hard DELETE removal with foreign-key clean-up.
      4. Complex analytical SQL query execution:
         - Query 1: On-Time Performance (OTP) summary.
         - Query 2: High-density routes grouping (`GROUP BY` & `HAVING`).
         - Query 3: Excessive departure delays correlated subquery.
         - Query 4: Fleet capacity scalar subquery.
         - Raw SQL execution terminal test.
* **Test Results:** 17/17 Tests Passed (100.0% Success Rate).
* **Scope:** Provides automated verification for continuous integration and live evaluator demonstration.

### Task 6: Academic Project Documentation & Report (`Member_2_Flight_Operations_Report.md`)
* **Timestamp:** 2026-10-30 18:40:40
* **Author:** Member 2 (Commercial Fleet & Flight Operations Lead)
* **Files Created/Modified:**
  - `Member_2_Flight_Operations_Report.md` (Created):
    - Comprehensive academic project documentation tailored specifically to Member 2's domain in accordance with Section 14 of the DBS Project Instructions.
    - Full problem statement, system objectives, and functional module breakdown.
    - Attribute dictionary, primary/foreign key mappings, and cardinality matrix.
    - Visual Entity-Relationship (ER) diagram representing Member 2's entities and foreign-key ties to Member 1 and Member 3.
    - Formal Normalization Analysis proving 1NF, 2NF, 3NF, and BCNF compliance with functional dependency proofs.
    - PostgreSQL DDL and constraint definitions.
    - 4 complex SQL demonstration queries with representative tabular execution outputs.
    - Application architecture walkthrough and description of database interaction layer.
    - Complete summary of test results and observations.
* **Scope:** Provides course documentation for Member 2's project submission.
