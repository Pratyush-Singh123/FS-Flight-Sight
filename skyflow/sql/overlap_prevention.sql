-- =====================================================================
-- SkyFlow Database System
-- Deliverable 3: Overlap Prevention Logic
-- Prevents double-booking: Same gate cannot have overlapping assignments
-- =====================================================================

-- ---------------------------------------------------------------------
-- Option A (PostgreSQL Advanced): EXCLUDE Constraint with GiST
-- ---------------------------------------------------------------------
-- Syntax:
-- CREATE EXTENSION IF NOT EXISTS btree_gist;
-- ALTER TABLE gate_assignment ADD CONSTRAINT no_gate_overlap
--   EXCLUDE USING gist (gate_id WITH =, tsrange(assigned_from, assigned_until) WITH &&);
--
-- Why Option A is often tricky in college submissions:
-- 1. Requires superuser privileges to run `CREATE EXTENSION btree_gist`.
-- 2. Range types (`tsrange`) and exclusion operators (`&&`) are PostgreSQL-specific
--    and not part of standard CSE relational calculus / ANSI SQL taught in 3rd semester.

-- ---------------------------------------------------------------------
-- Option B (Recommended for 3rd Sem CSE): BEFORE Trigger with Overlap Check
-- ---------------------------------------------------------------------
-- Overlap Condition:
-- Two intervals [A_start, A_end] and [B_start, B_end] overlap if and only if:
--   A_start < B_end AND A_end > B_start
--
-- This function checks if another assignment for the same gate overlaps with
-- the candidate record being inserted or updated.

CREATE OR REPLACE FUNCTION check_gate_assignment_overlap()
RETURNS TRIGGER AS $$
DECLARE
    overlap_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO overlap_count
    FROM gate_assignment
    WHERE gate_id = NEW.gate_id
      AND assignment_id <> COALESCE(NEW.assignment_id, -1)
      AND status <> 'CANCELLED'
      AND (NEW.assigned_from < assigned_until AND NEW.assigned_until > assigned_from);

    IF overlap_count > 0 THEN
        RAISE EXCEPTION 'GATE_DOUBLE_BOOKED: Gate ID % already has an active assignment overlapping with the requested window (% to %)',
            NEW.gate_id, NEW.assigned_from, NEW.assigned_until;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Bind the trigger to gate_assignment
DROP TRIGGER IF EXISTS trg_prevent_gate_double_booking ON gate_assignment;

CREATE TRIGGER trg_prevent_gate_double_booking
BEFORE INSERT OR UPDATE ON gate_assignment
FOR EACH ROW
EXECUTE FUNCTION check_gate_assignment_overlap();
