# SkyFlow ATCMS – Member 3 Activity & Change Log

This file records all modifications, file creations, schema developments, and implementation milestones executed for **Member 3 (Air Traffic Control Tower, En-Route & Safety Lead)** in accordance with project instructions and course requirements.

---

## Log Format
Each entry follows the structured format:
- **Timestamp:** ISO 8601 / IST date and time
- **Task ID & Name:** Member 3 designated work package
- **Files Modified / Created:** Exact relative paths
- **Change Details:** Summary of code, schema, query, or UI additions
- **Validation & Testing:** Evidence of syntax, constraint, trigger, or execution verification
- **Traceability:** Alignment with `DBS_Project Instructions.pdf` & `Air_Traffic_Control_DBMS_Project_Blueprint.md`

---

## Change Entries

### Entry #1: Repository Setup & Git Synchronization
- **Timestamp:** 2026-10-30T18:14:46+05:30
- **Task:** Repo Connection & Worktree Setup
- **Files Modified / Created:**
  - `.git/config`
  - `README.md`
- **Change Details:**
  - Disconnected stray home-directory `.git` to prevent path leakage.
  - Initialized git tracking for `/Users/pratyush/Downloads/DBMS Project`.
  - Linked remote `origin` to `https://github.com/Pratyush-Singh123/FS-Flight-Sight.git`.
  - Pulled and synchronized `main` branch with remote repository.
- **Traceability:** Project setup requirement.

### Entry #2: Project Environment Configuration & Change Log Initialization
- **Timestamp:** 2026-10-30T18:21:14+05:30
- **Task:** Environment & Logging Foundation
- **Files Modified / Created:**
  - `.gitignore`
  - `CHANGES_LOG.md`
  - `TASK_EXPLANATION_AND_INTEGRATION.md`
- **Change Details:**
  - Created `.gitignore` ignoring virtual environments (`.venv`), Python cache files, and SQLite database artifacts.
  - Created `CHANGES_LOG.md` to capture granular audit history of every code and database change.
  - Created `TASK_EXPLANATION_AND_INTEGRATION.md` to document functional explanations and inter-module contracts.
- **Traceability:** User requirement for change audit and task integration documentation.

### Entry #3: Member 3 SQL Schema, Triggers & Seed Dataset
- **Timestamp:** 2026-10-30T18:22:49+05:30
- **Task:** Database Architecture & SQL Module
- **Files Modified / Created:**
  - `sql/01_member3_schema.sql`
  - `sql/02_member3_seed.sql`
  - `sql/03_member3_queries.sql`
- **Change Details:**
  - Implemented `01_member3_schema.sql`: Defined DDL for `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT_CLEARANCE`, and `INCIDENT_LOG`. Added check constraints for altitude ranges (0 to 60,000 ft), compass headings (0 to 360 deg), certification levels, and incident severities. Implemented PL/pgSQL trigger `trg_fn_enforce_runway_safety` to intercept runway double-booking / incursions before clearance insertion.
  - Implemented `02_member3_seed.sql`: Populated realistic Indian FIRs (Delhi, Mumbai, Chennai, Kolkata, and TMAs), certified controllers (`AAI-ATCO-xxxx`), historical clearances, and incident records.
  - Implemented `03_member3_queries.sql`: Structured queries demonstrating core course rubrics: Query 1 (4-table join with correlated subquery for active airborne flights), Query 2 (Controller workload via `GROUP BY` and `HAVING`), Query 3 (Incident severity report with case logic), and Query 4 (Sector capacity utilization).
- **Traceability:** Meets Blueprint Section 4, 7, 9, 10, 11 and Course Instructions Section 5, 7, 8, 11.

### Entry #4: Python Database Engine & Transactional Trigger Adapter
- **Timestamp:** 2026-10-30T18:24:00+05:30
- **Task:** Backend Database Layer
- **Files Modified / Created:**
  - `db.py`
- **Change Details:**
  - Created `db.py` providing unified access for PostgreSQL (production) and SQLite (demonstration/offline fallback).
  - Emulated exact PL/pgSQL trigger mechanics inside SQLite (`trg_runway_clearance_safety_abort`, `trg_runway_clearance_occupy`, `trg_flight_status_takeoff`, `trg_flight_status_landing`).
  - Added transaction-safe clearance issuance API with error interceptors for runway collisions.
  - Implemented reporting and analytical query fetchers.
- **Traceability:** Meets Blueprint Section 12.3 & 13.

### Entry #6: Automated Test Suite & Multi-Member Sidebar Navigation
- **Timestamp:** 2026-10-30T18:29:22+05:30
- **Task:** Verification & System Cohesion
- **Files Modified / Created:**
  - `test_member3.py`
  - `pages/1_Airport_Ground_Control.py`
  - `pages/2_Flight_Operations.py`
  - `db.py`
- **Change Details:**
  - Created `test_member3.py` to automatically execute and validate:
    1. Database initialization and seeding.
    2. Query 1 (Airborne join with correlated subquery).
    3. Query 2 (Controller workload with `GROUP BY` and `HAVING`).
    4. Query 4 (Sector capacity monitoring).
    5. Trigger safety interlock (verified that takeoff clearance on occupied runway aborts with error; verified that takeoff clearance on available runway succeeds and transitions runway state to `OCCUPIED`).
    6. Safety incident filing into `INCIDENT_LOG`.
  - Created `pages/1_Airport_Ground_Control.py` and `pages/2_Flight_Operations.py` so that Streamlit sidebar navigation across all 3 members is smooth and integrated.
  - Refined `db.py` query placeholders and execution methods.
  - Executed test suite with 100% test pass rate.
  - Verified live Streamlit server launch (`HTTP 200 OK`).
- **Traceability:** Meets Course Instructions Section 10, 15, 16.



### Entry #7: 3-Member Unified Integration & Humane UX Overhaul
- **Timestamp:** 2026-10-30T19:15:30+05:30
- **Task:** Multi-Member Full System Integration & Humanized Interface Polish
- **Files Modified / Created:**
  - `db.py` (Master Unified Database Layer)
  - `app.py` (Integrated Operations Control Center - IOCC)
  - `pages/1_Airport_Ground_Control.py` (Harmonized Member 1 Ground Hub)
  - `pages/2_Flight_Operations.py` (Harmonized Member 2 Flight Ops Portal)
  - `pages/3_ATC_Clearance_Console.py` (Harmonized Member 3 ATC Radar Console)
  - `verify_all_modules.py` (Master 3-Member Verification Suite)
  - `sql/course_sql_queries_all_members.sql` (Consolidated Syllabus Query Catalog)
  - `sql/member1_ground_infrastructure.sql`
  - `sql/member2_flight_operations.sql`
- **Change Details:**
  - **Database Layer (`db.py`):** Unified all 11 relational entities (`AIRPORT`, `RUNWAY`, `GATE`, `GATE_ASSIGNMENT`, `AIRLINE`, `AIRCRAFT`, `FLIGHT`, `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT_CLEARANCE`, `INCIDENT_LOG`). Configured dual triggers: Member 1 Gate Overlap Prevention (`trg_prevent_gate_double_booking`) and Member 3 Runway Safety Interlock (`trg_runway_clearance_safety_abort`). Implemented cross-dialect SQL query translation enabling PostgreSQL date/interval expressions to execute natively on SQLite without external server dependencies.
  - **Humane Application Design:**
    * *IOCC Hub (`app.py`):* Redesigned with aviation color palettes, live telemetry banners, collaborative persona cards, and an interactive End-to-End Flight Lifecycle diagram illustrating cross-member data handoffs.
    * *Ground Control (`pages/1_Airport_Ground_Control.py`):* Enabled zero-config database connectivity, visual aerodrome status cards, and interactive gate conflict notifications.
    * *Flight Operations (`pages/2_Flight_Operations.py`):* Integrated airline dispatch schedules, status machine timelines, route density analytics, and OTP graphs.
    * *ATC Tower Console (`pages/3_ATC_Clearance_Console.py`):* Synchronized runway status reads and trigger collision feedback with plain-English safety warnings.
  - **Verification:** Created `verify_all_modules.py` validating 100% test passing across all 3 member domains, including both trigger safety interlocks and all complex queries.
- **Traceability:** Complete fulfillment of `DBS_Project Instructions.pdf` (Sections 1–17) and `Air_Traffic_Control_DBMS_Project_Blueprint.md` (Sections 1–14).
