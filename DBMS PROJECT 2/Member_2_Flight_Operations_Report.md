# SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)
## Academic Project Documentation: Subsystem Report for Member 2
**Course:** Database Management Systems (DBMS)  
**Lead:** Member 2 – Commercial Fleet & Flight Operations Lead  
**Entities Owned:** `AIRLINE`, `AIRCRAFT`, `FLIGHT`  
**Application Component:** Flight Operations & Commercial Dispatch Portal  

---

## 1. Project Title & Overview
**Project Title:** SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)  
**Subsystem Title:** Commercial Fleet, Aircraft Registry & Domestic Flight Operations Portal  
**Team Architecture:** 3 Members working in parallel across decoupled relational domains:
- **Member 1:** Airport Ground Infrastructure, Runways, and Terminal Gates.
- **Member 2 (Author):** Commercial Fleet Registry, Aircraft Airframes, and Flight Operations.
- **Member 3:** Airspace Sectors (FIRs), ATC Clearances, and Safety Audit Ledger.

---

## 2. Problem Statement
Commercial airlines and air traffic controllers coordinate high-volume domestic flight movements over shared national airspace corridors. Without a strictly normalized relational database management system:
1. Dispatchers can introduce schedule anomalies, such as scheduling flights where origin and destination are identical aerodromes, or recording arrival timestamps preceding departures.
2. Duplicate scheduling of commercial flight numbers on identical dates risks catastrophic mid-air and ground routing collisions.
3. Fleet data (passenger capacity, service ceiling, cruising speed) suffers from update and deletion anomalies when duplicated across flight legs.
4. Ground holds and en-route vector adjustments fail to compute accurate On-Time Performance (OTP) metrics or highlight route congestion bottlenecks across high-density corridors (e.g., Delhi–Mumbai, Mumbai–Bengaluru).

---

## 3. Subsystem Objectives
Member 2's subsystem achieves the following technical objectives:
1. **Relational Fleet Modeling:** Formulate 3NF/BCNF normalized schemas for airlines, civil aircraft airframes with DGCA `VT-` tail registrations, and domestic flight legs.
2. **Database-Level Constraint Enforcement:** Implement strict SQL domain and referential integrity constraints (`CHECK(origin <> dest)`, `CHECK(arrival > departure)`, `UNIQUE(flight_number, flight_date)`) so that scheduling corruption is rejected at the engine level.
3. **Flight Lifecycle State Machine:** Enforce chronological operational transitions (`SCHEDULED` ➔ `BOARDING` ➔ `TAXIING` ➔ `AIRBORNE` ➔ `LANDED` or `DIVERTED` / `CANCELLED`).
4. **Punctuality & Congestion Analytics:** Deliver complex relational queries calculating airline On-Time Performance (OTP) using the DGCA 15-minute standard, high-density corridor congestion reports with `HAVING`, and correlated subqueries identifying excessive delays.
5. **Interactive Dispatch Portal:** Provide a web-based user interface enabling dispatchers to search, schedule, update, cancel, and analyze domestic flights.

---

## 4. Subsystem Functional Modules
Member 2 owns two core functional modules:
1. **Flight Planning & Fleet Registry Module:**
   - Manages airline profiles (names, callsigns, dispatch contacts).
   - Manages aircraft fleet registry (airframe models, passenger capacities, service ceilings, speeds).
   - Manages domestic route schedules and initial leg dispatches.
2. **Flight Operations & Delay Analytics Module:**
   - Monitors live domestic flight statuses across Indian hubs.
   - Transitions operational lifecycle states.
   - Logs ground and departure delays.
   - Computes carrier-level OTP benchmarks and route density metrics.

---

## 5. Entities, Attributes & Relationship Matrix

### 5.1 Member 2 Entity Catalog
1. **`AIRLINE` (Commercial Operating Carrier):**
   - `airline_id` (INT, PK): Surrogate primary key.
   - `airline_name` (VARCHAR(100), UNIQUE, NOT NULL): Official commercial brand name.
   - `callsign_prefix` (VARCHAR(10), UNIQUE, NOT NULL): 3-letter ICAO designator (e.g., `'IGO'`, `'AIC'`).
   - `country_of_origin` (VARCHAR(50), NOT NULL, DEFAULT `'India'`): Legal jurisdiction.
   - `contact_email` (VARCHAR(100), UNIQUE, NOT NULL): Dispatch operations contact address.

2. **`AIRCRAFT` (Civil Airframe Fleet):**
   - `aircraft_reg_no` (VARCHAR(12), PK): Official DGCA civil tail registration (e.g., `'VT-ISN'`).
   - `model` (VARCHAR(50), NOT NULL): Aircraft model (e.g., `'A320neo'`, `'B787-8'`).
   - `manufacturer` (VARCHAR(50), NOT NULL): Airframe manufacturer (`'Airbus'`, `'Boeing'`).
   - `passenger_capacity` (INT, NOT NULL, CHECK > 0): Seating capacity.
   - `max_altitude_ft` (INT, NOT NULL, CHECK >= 1000 AND <= 60000): Certified service ceiling.
   - `cruising_speed_knots` (INT, NOT NULL, CHECK > 0): Standard true airspeed.
   - `airline_id` (INT, FK -> `AIRLINE.airline_id`, NOT NULL): Operating carrier.

3. **`FLIGHT` (Scheduled & Operational Flight Leg):**
   - `flight_id` (INT, PK): Surrogate primary key.
   - `flight_number` (VARCHAR(10), NOT NULL): Commercial flight label (e.g., `'6E-204'`).
   - `flight_date` (DATE, NOT NULL): Operational calendar date.
   - `airline_id` (INT, FK -> `AIRLINE.airline_id`, NOT NULL): Operating carrier.
   - `aircraft_reg_no` (VARCHAR(12), FK -> `AIRCRAFT.aircraft_reg_no`, NOT NULL): Assigned airframe.
   - `origin_airport` (VARCHAR(4), FK -> `AIRPORT.airport_code`, NOT NULL): Departure aerodrome.
   - `dest_airport` (VARCHAR(4), FK -> `AIRPORT.airport_code`, NOT NULL): Arrival aerodrome.
   - `scheduled_departure` (TIMESTAMP, NOT NULL): Planned off-block time.
   - `scheduled_arrival` (TIMESTAMP, NOT NULL): Planned touchdown time.
   - `actual_departure` (TIMESTAMP, NULLABLE): Recorded off-block timestamp.
   - `actual_arrival` (TIMESTAMP, NULLABLE): Recorded touchdown timestamp.
   - `current_status` (VARCHAR(20), NOT NULL, DEFAULT `'SCHEDULED'`): Finite state machine value.

### 5.2 Relationship Cardinality Specifications
| Parent Entity | Child Entity | Foreign Key Column | Cardinality | Business Rules |
| :--- | :--- | :--- | :--- | :--- |
| `AIRLINE` | `AIRCRAFT` | `airline_id` | 1 : N | An airline owns/leases multiple aircraft; each aircraft is registered to exactly one airline. |
| `AIRLINE` | `FLIGHT` | `airline_id` | 1 : N | An airline operates multiple flight legs; each flight leg belongs to exactly one airline. |
| `AIRCRAFT` | `FLIGHT` | `aircraft_reg_no`| 1 : N | An airframe operates sequential flight legs; each leg is operated by one airframe. |
| `AIRPORT` (M1) | `FLIGHT` | `origin_airport` | 1 : N | An airport originates many flights; each flight originates from one airport. |
| `AIRPORT` (M1) | `FLIGHT` | `dest_airport` | 1 : N | An airport terminates many flights; each flight terminates at one airport. |
| `FLIGHT` | `GATE_ASSIGNMENT` (M1)| `flight_id` | 1 : N | A flight occupies terminal gates for turnaround; gate assignments reference a flight. |
| `FLIGHT` | `FLIGHT_CLEARANCE` (M3)| `flight_id` | 1 : N | A flight receives multiple sequential clearance instructions from controllers. |
| `FLIGHT` | `INCIDENT_LOG` (M3)| `flight_id` | 1 : N | A flight may be referenced in safety incident investigation records. |

---

## 6. Entity-Relationship (ER) Diagram
```
                     ┌────────────────────────┐
                     │        AIRLINE         │
                     │ (airline_id [PK], ...) │
                     └───────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
               1 │ owns                          │ 1 operates
                 │                               │
                 ▼ N                             ▼ N
     ┌────────────────────────┐      ┌────────────────────────┐
     │        AIRCRAFT        │      │         FLIGHT         │
     │(aircraft_reg_no [PK],..)│      │    (flight_id [PK],    │
     └───────────┬────────────┘      │   flight_number, ...)  │
                 │ 1                 └───────────┬────────────┘
                 │ assigned                      │
                 ▼ N                             │
                 └───────────────────────────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
     ▼ N                         ▼ N                         ▼ N
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│     GATE_ASSIGNMENT     │ │    FLIGHT_CLEARANCE     │ │      INCIDENT_LOG       │
│  (Managed by Member 1)  │ │  (Managed by Member 3)  │ │  (Managed by Member 3)  │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

---

## 7. Normalization Analysis (1NF to 3NF / BCNF)

### First Normal Form (1NF)
* **Definition:** A relation is in 1NF if and only if all attribute values are atomic (indivisible) and there are no repeating groups or nested arrays.
* **Analysis:**
  - `FLIGHT` stores atomic attributes (`flight_number`, `flight_date`, `scheduled_departure`, `scheduled_arrival`, `current_status`).
  - Clearances and gate reservations are not stored in multi-valued arrays within `FLIGHT`, but decomposed into separate child relations (`FLIGHT_CLEARANCE`, `GATE_ASSIGNMENT`).
  - Aircraft specifications (`model`, `manufacturer`, `passenger_capacity`) are isolated into individual atomic columns in `AIRCRAFT`.
  - **Verdict:** Satisfies 1NF.

### Second Normal Form (2NF)
* **Definition:** A relation is in 2NF if it is in 1NF and every non-prime attribute is fully functionally dependent on the entire candidate key (no partial dependencies on a proper subset of a composite primary key).
* **Analysis:**
  - In `AIRLINE`, the primary key is single-attribute `airline_id`. All non-prime attributes (`airline_name`, `callsign_prefix`, `contact_email`) functionally depend on `airline_id`.
  - In `AIRCRAFT`, the primary key is single-attribute `aircraft_reg_no`. All attributes (`model`, `passenger_capacity`, `airline_id`) functionally depend on the entire tail number.
  - In `FLIGHT`, the primary key is surrogate `flight_id`. The candidate key is `(flight_number, flight_date)`. Since all non-prime attributes (`origin_airport`, `dest_airport`, `scheduled_departure`, `current_status`) depend on the whole flight leg and not on `flight_number` alone, no partial dependencies exist.
  - **Verdict:** Satisfies 2NF.

### Third Normal Form (3NF) & Boyce-Codd Normal Form (BCNF)
* **Definition:** A relation is in 3NF if it is in 2NF and no non-prime attribute is transitively dependent on any candidate key ($X \rightarrow Y \rightarrow Z$ where $X$ is a key and $Y$ is non-prime is disallowed). BCNF requires that for every functional dependency $X \rightarrow Y$, $X$ must be a superkey.
* **Analysis:**
  - In `FLIGHT`, we record `airline_id` and `aircraft_reg_no`. We intentionally do **not** store `airline_name`, `contact_email`, `aircraft_model`, or `passenger_capacity` inside `FLIGHT`.
  - If we had included `model` or `passenger_capacity` in `FLIGHT`, the dependency chain `flight_id -> aircraft_reg_no -> passenger_capacity` would represent a transitive dependency, causing update anomalies whenever an aircraft seating configuration is refurbished.
  - Decomposing fleet specifications into `AIRCRAFT` and carrier details into `AIRLINE` completely eliminates transitive dependencies.
  - In every functional dependency ($FD$) in Member 2's tables, the determinant is a superkey:
    - In `AIRLINE`: `airline_id` $\rightarrow$ `{airline_name, callsign_prefix, contact_email}` (Superkey).
    - In `AIRCRAFT`: `aircraft_reg_no` $\rightarrow$ `{model, manufacturer, passenger_capacity, airline_id}` (Superkey).
    - In `FLIGHT`: `flight_id` $\rightarrow$ `{flight_number, flight_date, origin, dest, scheduled_departure, ...}` (Superkey).
  - **Verdict:** Satisfies 3NF and BCNF.

---

## 8. Relational Schema & Integrity Constraints (PostgreSQL DDL)

```sql
-- Commercial Airlines
CREATE TABLE AIRLINE (
    airline_id SERIAL PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL UNIQUE,
    callsign_prefix VARCHAR(10) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50) NOT NULL DEFAULT 'India',
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

-- Aircraft Fleet Registry
CREATE TABLE AIRCRAFT (
    aircraft_reg_no VARCHAR(12) PRIMARY KEY,
    model VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(50) NOT NULL,
    passenger_capacity INT NOT NULL CHECK (passenger_capacity > 0),
    max_altitude_ft INT NOT NULL CHECK (max_altitude_ft >= 1000 AND max_altitude_ft <= 60000),
    cruising_speed_knots INT NOT NULL CHECK (cruising_speed_knots > 0),
    airline_id INT NOT NULL REFERENCES AIRLINE(airline_id) ON DELETE CASCADE
);

-- Domestic Scheduled Flights
CREATE TABLE FLIGHT (
    flight_id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
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
    CONSTRAINT uq_flight_number_date UNIQUE (flight_number, flight_date),
    CONSTRAINT chk_flight_airports_distinct CHECK (origin_airport <> dest_airport),
    CONSTRAINT chk_flight_schedule_chronology CHECK (scheduled_arrival > scheduled_departure)
);
```

---

## 9. Representative SQL Queries & Output Verification

### Query 1: Airline On-Time Performance (OTP) Summary
* **Concepts Demonstrated:** Multi-table `JOIN`, `CASE` conditional expressions, date interval arithmetic, aggregate functions (`COUNT`, `SUM`, `AVG`), `GROUP BY`, and `ORDER BY`.
* **SQL Statement:**
```sql
SELECT 
    al.airline_name,
    al.callsign_prefix,
    COUNT(f.flight_id) AS scheduled_legs,
    COUNT(f.actual_departure) AS departed_legs,
    SUM(CASE WHEN f.actual_departure IS NOT NULL AND f.actual_departure <= (f.scheduled_departure + INTERVAL '15 minutes') THEN 1 ELSE 0 END) AS on_time_count,
    SUM(CASE WHEN f.actual_departure IS NOT NULL AND f.actual_departure > (f.scheduled_departure + INTERVAL '15 minutes') THEN 1 ELSE 0 END) AS delayed_count,
    CASE 
        WHEN COUNT(f.actual_departure) > 0 
        THEN ROUND((SUM(CASE WHEN f.actual_departure <= (f.scheduled_departure + INTERVAL '15 minutes') THEN 1.0 ELSE 0.0 END) / COUNT(f.actual_departure)) * 100.0, 2)
        ELSE 0.00 
    END AS otp_rate_percentage,
    ROUND(COALESCE(AVG(CASE WHEN f.actual_departure > f.scheduled_departure THEN EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60.0 ELSE 0 END), 0.0), 1) AS avg_delay_mins
FROM AIRLINE al
LEFT JOIN FLIGHT f ON al.airline_id = f.airline_id
GROUP BY al.airline_id, al.airline_name, al.callsign_prefix
ORDER BY otp_rate_percentage DESC, scheduled_legs DESC;
```
* **Sample Execution Output:**
| Airline Name | Callsign | Scheduled | Departed | On-Time | Delayed | OTP Rate (%) | Avg Delay (mins) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| IndiGo | IGO | 4 | 1 | 1 | 0 | 100.00% | 5.0 |
| Vistara | VTI | 2 | 1 | 1 | 0 | 100.00% | 3.0 |
| AIX Connect | IAD | 1 | 1 | 1 | 0 | 100.00% | 2.0 |
| Air India | AIC | 3 | 1 | 0 | 1 | 0.00% | 42.0 |
| SpiceJet | SEJ | 2 | 1 | 0 | 1 | 0.00% | 50.0 |
| Akasa Air | AKJ | 2 | 0 | 0 | 0 | 0.00% | 0.0 |

---

### Query 2: High-Density Corridors & Bottleneck Congestion
* **Concepts Demonstrated:** `GROUP BY`, `HAVING` clause, aggregate functions (`COUNT`, `MIN`, `MAX`), string concatenation (`||`).
* **SQL Statement:**
```sql
SELECT 
    f.origin_airport || ' -> ' || f.dest_airport AS route_corridor,
    orig.city AS origin_city,
    dest.city AS dest_city,
    COUNT(f.flight_id) AS total_scheduled_flights,
    COUNT(DISTINCT f.airline_id) AS competing_airlines_count,
    COUNT(DISTINCT f.aircraft_reg_no) AS distinct_aircraft_assigned,
    MIN(f.scheduled_departure) AS earliest_departure,
    MAX(f.scheduled_departure) AS latest_departure
FROM FLIGHT f
JOIN AIRPORT orig ON f.origin_airport = orig.airport_code
JOIN AIRPORT dest ON f.dest_airport = dest.airport_code
GROUP BY f.origin_airport, f.dest_airport, orig.city, dest.city
HAVING COUNT(f.flight_id) >= 2
ORDER BY total_scheduled_flights DESC, route_corridor ASC;
```
* **Sample Execution Output:**
| Route Corridor | Origin City | Dest City | Total Flights | Competing Airlines | Distinct Aircraft | Earliest Dep | Latest Dep |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BOM -> DEL | Mumbai | New Delhi | 2 | 2 | 2 | 2026-11-01 08:30:00 | 2026-11-01 12:00:00 |
| DEL -> BOM | New Delhi | Mumbai | 2 | 2 | 2 | 2026-11-01 06:00:00 | 2026-11-01 14:00:00 |

---

### Query 3: Excessive Delays Investigation (Correlated Subquery)
* **Concepts Demonstrated:** Correlated Subquery with `WHERE flight_id IN (SELECT ...)`, epoch time arithmetic, multi-table joins.
* **SQL Statement:**
```sql
SELECT 
    f.flight_number,
    al.airline_name,
    al.contact_email AS dispatch_alert_email,
    f.aircraft_reg_no,
    ac.model AS aircraft_type,
    f.origin_airport || ' -> ' || f.dest_airport AS corridor,
    f.scheduled_departure,
    f.actual_departure,
    ROUND(EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60) AS delay_minutes
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
WHERE f.actual_departure IS NOT NULL
  AND f.flight_id IN (
      SELECT sub_f.flight_id 
      FROM FLIGHT sub_f 
      WHERE sub_f.actual_departure > (sub_f.scheduled_departure + INTERVAL '30 minutes')
  )
ORDER BY delay_minutes DESC;
```
* **Sample Execution Output:**
| Flight # | Airline | Dispatch Alert Email | Tail Reg | Aircraft Type | Corridor | Sched Dep | Actual Dep | Delay (min) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SG-103 | SpiceJet | ops@spicejet.com | VT-SGZ | B737-MAX8 | DEL -> PNQ | 06:45:00 | 07:35:00 | 50 min |
| AI-624 | Air India | dispatch@airindia.com | VT-CIO | A320neo | DEL -> HYD | 07:30:00 | 08:12:00 | 42 min |

---

### Query 4: Fleet Capacity vs. Industry Benchmark (Scalar Subquery)
* **Concepts Demonstrated:** Scalar Subquery in `WHERE` clause (`WHERE passenger_capacity > (SELECT AVG(...) FROM AIRCRAFT)`), multi-table join, arithmetic offset calculation.
* **SQL Statement:**
```sql
SELECT 
    ac.aircraft_reg_no,
    ac.model,
    ac.manufacturer,
    ac.passenger_capacity,
    al.airline_name,
    ROUND((ac.passenger_capacity - (SELECT AVG(passenger_capacity) FROM AIRCRAFT)), 1) AS seats_above_fleet_avg,
    COUNT(f.flight_id) AS total_assigned_flights
FROM AIRCRAFT ac
JOIN AIRLINE al ON ac.airline_id = al.airline_id
LEFT JOIN FLIGHT f ON ac.aircraft_reg_no = f.aircraft_reg_no
WHERE ac.passenger_capacity > (SELECT AVG(passenger_capacity) FROM AIRCRAFT)
GROUP BY ac.aircraft_reg_no, ac.model, ac.manufacturer, ac.passenger_capacity, al.airline_name
ORDER BY ac.passenger_capacity DESC;
```
* **Sample Execution Output:**
| Tail Reg | Model | Manufacturer | Capacity | Airline | Seats Above Fleet Avg | Assigned Flights |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| VT-ALQ | B777-300ER | Boeing | 342 | Air India | +128.9 | 1 |
| VT-TTB | B787-9 Dreamliner | Boeing | 299 | Vistara | +85.9 | 1 |
| VT-EXF | B787-8 Dreamliner | Boeing | 256 | Air India | +42.9 | 1 |
| VT-IFP | A321neo | Airbus | 222 | IndiGo | +8.9 | 1 |

---

## 10. Application & User Interface Architecture
The application is built using **Python and Streamlit** in a multi-page configuration:
- `app.py`: Overview dashboard, system health KPIs, DBMS engine detection, and 3-member WBS breakdown.
- `pages/2_Flight_Operations.py`: Dedicated portal for Member 2 containing 5 functional tabs:
  1. **Tab 1: Live Flight Dispatch Board & Multi-Filter Search (SELECT):** Real-time grid displaying flight legs with origin/destination cities, departure delay calculations, and an interactive flight inspector drawer.
  2. **Tab 2: Schedule New Flight Leg (INSERT):** Form with reactive dropdowns (selecting an airline limits aircraft options to that carrier) and client/server validation enforcing check constraints.
  3. **Tab 3: Flight State Transition & Delay Logger (UPDATE):** Interactive tool advancing flights across the operational lifecycle (`SCHEDULED` ➔ `BOARDING` ➔ `TAXIING` ➔ `AIRBORNE` ➔ `LANDED`), automatically generating timestamps, or applying delay minutes.
  4. **Tab 4: Flight Cancellation & Deletion (DELETE):** Supports both soft-cancellation (preserving audit history) and hard-deletion (guarded by foreign key integrity checks).
  5. **Tab 5: Operational Analytics & SQL Demonstrator:** Interactive OTP summary table and charts, high-density corridor sliders, excessive delay reports, and a live SQL query runner allowing evaluators to execute arbitrary SQL statements.

---

## 11. Database Connection & Transaction Layer
The data access layer (`db.py`) enforces strict database interaction standards:
- **Dual-Engine Architecture:** Runs against PostgreSQL when production connection strings are configured, or automatically against local SQLite (`skyflow_atc.db`) for immediate offline demonstration.
- **Parameterized Queries:** Every dynamic query uses parameter binding (`?` or `%s`) to eliminate SQL injection vulnerabilities.
- **Transaction Safety:** Encloses multi-statement operations in `try/except/finally` blocks with explicit `conn.commit()` on success and `conn.rollback()` on failure.
- **Foreign Key Enforcement:** Explicitly issues `PRAGMA foreign_keys = ON;` in SQLite to ensure referential integrity matches PostgreSQL behavior.

---

## 12. Verification & Test Results
Member 2's subsystem was validated using `verify_member2.py`.
- **Total Test Cases Executed:** 17 tests.
- **Pass Rate:** 17 / 17 (100.0%).
- **Key Validations Verified:**
  - Database connectivity and non-empty master tables.
  - Rejection of circular flight (`DEL -> DEL`).
  - Rejection of inverted schedule (`arrival <= departure`).
  - Rejection of duplicate flight on same date (`UNIQUE(flight_number, flight_date)`).
  - Clean INSERT, SELECT, UPDATE (state transition & delay adjustment), and DELETE execution.
  - Accurate calculation of all 4 course analytical SQL queries.
  - Arbitrary SQL execution through evaluator terminal.

---

## 13. Results, Observations & Conclusion
By implementing strict relational constraints, 3NF/BCNF normalization, and parameterized transactions:
1. All domain rules (such as preventing flights with identical origin and destination aerodromes) are enforced at the database engine level, guaranteeing data integrity.
2. The 3-member architecture successfully decoupled airport infrastructure (Member 1), flight scheduling (Member 2), and ATC clearances (Member 3), allowing independent development without blocking.
3. Complex queries utilizing `JOIN`, conditional `CASE` aggregation, `GROUP BY`, `HAVING`, and subqueries provide actionable operational insights into airline punctuality and airspace bottlenecks across India's domestic flight network.
