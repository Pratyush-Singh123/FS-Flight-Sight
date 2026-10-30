# SkyFlow: Member 1 Negative Testing & Constraint Verification Log
## Deliverable & Step 6: Testing with Deliberately Bad Inputs

This log demonstrates that the DBMS engine enforces all data integrity and business rules at the schema level.

---

### Test Case 1: Temporal Inversion (Assigned End Time Before Start Time)
* **Goal:** Verify that a gate booking cannot end before it begins.
* **Bad SQL Input:**
  ```sql
  INSERT INTO gate_assignment (gate_id, flight_id, assigned_from, assigned_until, status)
  VALUES (1, 2, '2026-10-30 14:00:00', '2026-10-30 13:00:00', 'CONFIRMED');
  ```
* **PostgreSQL Engine Response:**
  ```text
  ERROR: new row for relation "gate_assignment" violates check constraint "chk_assignment_time"
  DETAIL: Failing row contains (41, 1, 2, 2026-10-30 14:00:00, 2026-10-30 13:00:00, CONFIRMED).
  SQLSTATE: 23514
  ```
* **Explanation:** Enforced by `CONSTRAINT chk_assignment_time CHECK (assigned_until > assigned_from)`.

---

### Test Case 2: Gate Double Booking (Temporal Overlap)
* **Goal:** Verify that two flights cannot occupy the same gate concurrently.
* **Context:** Gate `1` is already booked from `05:00:00` to `06:05:00`.
* **Bad SQL Input:**
  ```sql
  -- Attempting an overlapping booking from 05:30 to 06:30
  INSERT INTO gate_assignment (gate_id, flight_id, assigned_from, assigned_until, status)
  VALUES (1, 4, '2026-10-30 05:30:00', '2026-10-30 06:30:00', 'CONFIRMED');
  ```
* **PostgreSQL Engine Response:**
  ```text
  ERROR: GATE_DOUBLE_BOOKED: Gate ID 1 already has an active assignment overlapping with the requested window (2026-10-30 05:30:00 to 2026-10-30 06:30:00)
  CONTEXT: PL/pgSQL function check_gate_assignment_overlap() line 12 at RAISE
  SQLSTATE: P0001
  ```
* **Explanation:** Intercepted by our `BEFORE INSERT OR UPDATE` trigger `trg_prevent_gate_double_booking`.

---

### Test Case 3: Duplicate Runway Designator at the Same Airport
* **Goal:** Ensure an airport cannot have two runways with the exact same identifier.
* **Context:** Airport `'DEL'` already possesses runway `'10/28'`.
* **Bad SQL Input:**
  ```sql
  INSERT INTO runway (airport_code, runway_designator, length_m, width_m, current_status)
  VALUES ('DEL', '10/28', 3500, 45, 'AVAILABLE');
  ```
* **PostgreSQL Engine Response:**
  ```text
  ERROR: duplicate key value violates unique constraint "uq_airport_runway"
  DETAIL: Key (airport_code, runway_designator)=(DEL, 10/28) already exists.
  SQLSTATE: 23505
  ```
* **Explanation:** Enforced by composite candidate key `UNIQUE (airport_code, runway_designator)`.

---

### Test Case 4: Invalid Domain / Status Value
* **Goal:** Ensure status strings strictly adhere to the frozen project decisions.
* **Bad SQL Input:**
  ```sql
  UPDATE runway SET current_status = 'UNDER_REPAIR' WHERE runway_id = 1;
  ```
* **PostgreSQL Engine Response:**
  ```text
  ERROR: new row for relation "runway" violates check constraint "runway_current_status_check"
  DETAIL: Failing row contains (1, DEL, 10/28, 3810, 45, ASPHALT, UNDER_REPAIR).
  SQLSTATE: 23514
  ```
* **Explanation:** Enforced by `CHECK (current_status IN ('AVAILABLE', 'OCCUPIED', 'CLOSED'))`.

---

### Test Case 5: Referential Integrity Violation (Orphan Runway)
* **Goal:** Verify that a runway cannot be registered to a non-existent airport.
* **Bad SQL Input:**
  ```sql
  INSERT INTO runway (airport_code, runway_designator, length_m, width_m, current_status)
  VALUES ('XYZ', '01/19', 3000, 45, 'AVAILABLE');
  ```
* **PostgreSQL Engine Response:**
  ```text
  ERROR: insert or update on table "runway" violates foreign key constraint "runway_airport_code_fkey"
  DETAIL: Key (airport_code)=(XYZ) is not present in table "airport".
  SQLSTATE: 23503
  ```
* **Explanation:** Enforced by `REFERENCES airport(airport_code)`.
