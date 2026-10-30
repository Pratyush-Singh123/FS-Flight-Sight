# SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)

**Course:** Database Management Systems (DBMS)  
**Domain:** Air Traffic Control (ATC) & Domestic Aviation Network (India)  
**Team Architecture:** 3 Members (Collaborative Parallel Architecture)  
**Repository:** [FS-Flight-Sight](https://github.com/Pratyush-Singh123/FS-Flight-Sight)  

---

## ✈️ System Overview

**SkyFlow** is a comprehensive relational database-driven aviation platform modeling real-world air traffic operations across 12 major Indian airport hubs and Flight Information Regions (FIRs).

The system integrates ground aerodrome movements, commercial fleet scheduling, and air traffic control tower clearances into a single unified platform built upon a **frozen, normalized relational schema (BCNF)** with automated transactional safety triggers.

---

## 👥 3-Member Collaborative Work Breakdown

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SKYFLOW INTEGRATED RELATIONAL ARCHITECTURE                             │
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

1. **Member 1: Ground Infrastructure & Terminal Movement Lead**
   - **Scope:** 12 Indian international hubs, physical paved runways, terminal aerobridges, and turnaround schedules.
   - **Entities:** `AIRPORT`, `RUNWAY`, `GATE`, `GATE_ASSIGNMENT`
   - **Key Feature:** Automated Gate Double-Booking Prevention Trigger.
   - **UI:** `pages/1_Airport_Ground_Control.py`

2. **Member 2: Commercial Fleet & Flight Operations Lead**
   - **Scope:** Operating airline carriers, aircraft fleet with DGCA `VT-` tail registrations, route density, and scheduling.
   - **Entities:** `AIRLINE`, `AIRCRAFT`, `FLIGHT`
   - **Key Feature:** On-Time Performance (OTP) analytics and lifecycle state machine transitions (`SCHEDULED` ➔ `BOARDING` ➔ `TAXIING` ➔ `AIRBORNE` ➔ `LANDED`).
   - **UI:** `pages/2_Flight_Operations.py`

3. **Member 3: Air Traffic Control Tower, En-Route Radar & Safety Lead**
   - **Scope:** Indian FIR airspace sectors (Delhi, Mumbai, Chennai, Kolkata), licensed ATC controllers, digital clearances, and safety incident logging.
   - **Entities:** `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT_CLEARANCE`, `INCIDENT_LOG`
   - **Key Feature:** Automated Runway Safety Collision Interlock Trigger & Black-box audit trail.
   - **UI:** `pages/3_ATC_Clearance_Console.py`

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (tested on macOS / Linux / Windows)
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/Pratyush-Singh123/FS-Flight-Sight.git
cd FS-Flight-Sight

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install streamlit pandas psycopg2-binary
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser to view the **SkyFlow Integrated Operations Control Center (IOCC)**.

---

## 🧪 Automated Verification Suite

Run the end-to-end multi-member test suite to verify all schema rules, triggers, constraints, and analytical queries:

```bash
python verify_all_modules.py
```

**Verification Results:**
- ✅ Master Schema & Seed Integrity (11 tables populated with realistic Indian aviation data)
- ✅ Gate Overlap Prevention Trigger (blocked double-booked gate assignments)
- ✅ Flight Scheduling Constraints (enforced `origin <> dest` and `arrival > departure`)
- ✅ Runway Collision Prevention Safety Trigger (intercepted takeoff on occupied runway)
- ✅ Auto State Transitions (cleared takeoff auto-updated runway to `OCCUPIED` and flight to `AIRBORNE`)
- ✅ Safety Incident Filing into `INCIDENT_LOG`
- ✅ All Complex Queries (Multi-Table Joins, Correlated Subqueries, `GROUP BY`, `HAVING`)

---

## 📂 Project Repository Structure

```
FS-Flight-Sight/
├── app.py                          # Integrated Operations Control Center (IOCC)
├── db.py                           # Master Database Engine (PostgreSQL + SQLite dual-engine)
├── pages/
│   ├── 1_Airport_Ground_Control.py # Member 1: Aerodrome Surface & Terminal Movement
│   ├── 2_Flight_Operations.py      # Member 2: Commercial Fleet & Route Dispatch
│   └── 3_ATC_Clearance_Console.py  # Member 3: Tower Radar, Clearances & Safety Logs
├── sql/
│   ├── 00_master_schema_and_seed.sql      # Full PostgreSQL schema, triggers & seed
│   ├── course_sql_queries_all_members.sql # Consolidated syllabus query catalog
│   ├── member1_ground_infrastructure.sql  # Member 1 queries & views
│   ├── member2_flight_operations.sql      # Member 2 queries & views
│   ├── 01_member3_schema.sql              # Member 3 DDL & PL/pgSQL triggers
│   ├── 02_member3_seed.sql                # Member 3 FIR & controller seed data
│   └── 03_member3_queries.sql             # Member 3 workload & radar queries
├── verify_all_modules.py           # Comprehensive 3-member verification test suite
├── CHANGES_LOG.md                  # Complete audit log of every modification
├── TASK_EXPLANATION_AND_INTEGRATION.md # Detailed architecture, BCNF analysis & viva guide
└── README.md                       # Main repository guide
```

---

## 🎓 Course Syllabus Concept Mapping

| Syllabus Requirement | SkyFlow Implementation |
| :--- | :--- |
| **SELECT & Filtering** | Filtering flights by status, origin, and destination in `pages/2_Flight_Operations.py` |
| **Multi-Table Joins** | 4-table join connecting `FLIGHT`, `AIRLINE`, `AIRCRAFT`, and `AIRPORT` |
| **Aggregate Functions** | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` in fleet capacity reports |
| **GROUP BY & HAVING** | Member 1 Peak Hour Runway Congestion (`HAVING COUNT(*) >= 1`), Member 3 Controller Workload (`HAVING COUNT(*) > 0`) |
| **Correlated Subqueries** | Member 3 latest clearance lookup (`MAX(clearance_id)`), Member 2 excessive delay analysis |
| **Relational Views** | `view_airport_ground_dashboard`, `VIEW_FLIGHT_DISPATCH_BOARD`, `VIEW_AIRLINE_FLEET_SUMMARY` |
| **Triggers & Stored Logic** | Gate double-booking prevention trigger, Runway takeoff/landing collision safety interlock trigger |
| **Normalization** | All 11 tables normalized to **Boyce-Codd Normal Form (BCNF)** |
| **User Interface** | Multi-page Streamlit portal with human-centric design, live telemetry, and interactive controls |
