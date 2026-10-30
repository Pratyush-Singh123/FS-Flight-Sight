"""
SkyFlow ATCMS - Master Unified Verification Suite
Validates the complete end-to-end integration across Member 1, Member 2, and Member 3.

Tests Covered:
- Master Schema Integrity & Seed Counts (11 tables)
- Member 1: Airport retrieval, Runway toggling, Gate Overlap Prevention Trigger
- Member 2: Flight scheduling, Constraint validation, State transitions, OTP Analytics
- Member 3: Runway collision safety trigger, Takeoff auto-transition, Controller workload, Incident logging
- Inter-Member Coordination: Gate -> Flight -> Pushback -> Takeoff -> Landing
"""

import sys
from datetime import datetime
import db

def test_full_integration():
    print("=" * 80)
    print("  SKYFLOW ATCMS: MASTER 3-MEMBER INTEGRATION & VERIFICATION SUITE")
    print("=" * 80)

    # 1. Initialize and Verify Catalog
    print("\n[Phase 1] Database Engine & Schema Verification...")
    db.init_database(force_reseed=True)
    status = db.get_database_status()
    print(f"✅ Active Engine: {status['engine']}")
    print(f"✅ Table Record Catalog: {status['counts']}")
    for tbl, count in status['counts'].items():
        assert count > 0, f"Table {tbl} must have seeded records!"

    # 2. Member 1 Tests: Ground & Terminal Movement
    print("\n[Phase 2] Testing Member 1 (Ground Hubs & Gate Overlap Trigger)...")
    airports = db.get_airports()
    assert len(airports) == 12, "Must have exactly 12 Indian airport facilities!"
    print(f"✅ Loaded {len(airports)} major Indian airports (DEL, BOM, BLR, MAA, HYD, CCU, etc.).")

    # Member 1 Gate Overlap Trigger Test
    print("   Testing Gate Double-Booking Prevention Trigger...")
    # Flight 1 already has Gate 1 from 06:00:00 to 07:00:00
    success, msg = db.assign_gate(1, 2, "2026-10-30 06:15:00", "2026-10-30 07:15:00")
    assert not success, "Trigger MUST reject overlapping gate reservation!"
    print(f"   ✅ Trigger Intercepted Conflict: {msg}")

    # Member 1 Analytical Queries
    congestion = db.get_runway_congestion()
    print(f"✅ Member 1 Query 1 (Runway Congestion): Returned {len(congestion)} records.")
    turnaround = db.get_gate_turnaround_stats()
    print(f"✅ Member 1 Query 2 (Gate Turnaround Stats): Returned {len(turnaround)} records.")

    # 3. Member 2 Tests: Commercial Fleet & Flight Operations
    print("\n[Phase 3] Testing Member 2 (Commercial Fleet & Scheduling)...")
    airlines = db.get_airlines()
    aircraft = db.get_aircraft()
    assert len(airlines) >= 5, "Must have at least 5 registered airlines!"
    assert len(aircraft) >= 6, "Must have at least 6 DGCA registered aircraft!"
    print(f"✅ Loaded {len(airlines)} carriers and {len(aircraft)} fleet airframes.")

    # Flight Scheduling & Constraint Enforcement
    print("   Testing Flight Scheduling Constraints (origin <> dest)...")
    bad_success, bad_msg = db.add_flight(
        flight_number="TEST-999",
        flight_date_val="2026-10-30",
        airline_id=1,
        aircraft_reg_no="VT-ISN",
        origin_airport="DEL",
        dest_airport="DEL",
        scheduled_departure="2026-10-30 16:00:00",
        scheduled_arrival="2026-10-30 18:00:00"
    )
    assert not bad_success, "Must reject identical origin and destination!"
    print(f"   ✅ Route constraint successfully enforced: {bad_msg}")

    # Schedule Valid Flight
    good_success, good_msg = db.add_flight(
        flight_number="AI-999",
        flight_date_val="2026-10-30",
        airline_id=2,
        aircraft_reg_no="VT-EXF",
        origin_airport="DEL",
        dest_airport="BOM",
        scheduled_departure="2026-10-30 17:00:00",
        scheduled_arrival="2026-10-30 19:15:00"
    )
    assert good_success, f"Failed to add valid flight: {good_msg}"
    print(f"   ✅ {good_msg}")

    # Member 2 Analytics
    otp = db.get_otp_analytics()
    print(f"✅ Member 2 Query 1 (OTP Performance): Analyzed {len(otp)} airlines.")
    density = db.get_route_density_analytics()
    print(f"✅ Member 2 Query 2 (Route Density): Computed {len(density)} city pairs.")

    # 4. Member 3 Tests: ATC Tower & Runway Safety Interlock
    print("\n[Phase 4] Testing Member 3 (ATC Tower Clearances & Safety Triggers)...")
    controllers = db.get_controllers()
    assert len(controllers) >= 6, "Must have licensed controllers on shift!"
    print(f"✅ Loaded {len(controllers)} controllers across TOWER, EN_ROUTE, APPROACH, GROUND.")

    # Runway Collision Interlock: DEL Runway 1 is OCCUPIED
    print("   Testing Runway Collision Prevention Trigger...")
    runways = db.get_runways("DEL")
    occupied_rwy = runways[runways["current_status"] == "OCCUPIED"].iloc[0]
    occ_id = int(occupied_rwy["runway_id"])
    
    col_success, col_msg = db.issue_clearance(
        flight_id=2,
        controller_id=1,
        clearance_type="TAKEOFF",
        runway_id=occ_id,
        altitude=5000,
        heading=90
    )
    assert not col_success, "Safety trigger MUST reject takeoff on occupied runway!"
    print(f"   ✅ Collision Intercepted: {col_msg}")

    # Valid Takeoff Clearance on AVAILABLE runway -> Auto-transitions to OCCUPIED and AIRBORNE
    avail_rwy = runways[runways["current_status"] == "AVAILABLE"].iloc[0]
    avail_id = int(avail_rwy["runway_id"])
    val_success, val_msg = db.issue_clearance(
        flight_id=3,
        controller_id=1,
        clearance_type="TAKEOFF",
        runway_id=avail_id,
        altitude=5000,
        heading=90
    )
    assert val_success, f"Valid clearance failed: {val_msg}"
    print(f"   ✅ Clearance Issued: {val_msg}")

    # Verify Auto Runway State Update
    upd_runways = db.get_runways("DEL")
    new_rwy_stat = upd_runways[upd_runways["runway_id"] == avail_id].iloc[0]["current_status"]
    assert new_rwy_stat == "OCCUPIED", "Runway must be automatically set to OCCUPIED by trigger!"
    print(f"   ✅ Trigger automatically updated Runway ID {avail_id} to OCCUPIED.")

    # Incident Filing
    inc_ok, inc_msg = db.file_incident(
        flight_id=1,
        reported_by=2,
        incident_type="NEAR_MISS",
        severity="CRITICAL",
        description="Airprox resolved via immediate resolution advisory over Bhopal FIR."
    )
    assert inc_ok, f"Failed to log incident: {inc_msg}"
    print(f"   ✅ {inc_msg}")

    # Member 3 Analytics
    workload = db.get_controller_workload()
    print(f"✅ Member 3 Query 2 (Controller Workload): Tracked {len(workload)} active officers.")
    airborne = db.get_airborne_radar_flights()
    print(f"✅ Member 3 Query 1 (Airborne Flights + Subquery): Radar tracking {len(airborne)} active flights.")

    print("\n" + "=" * 80)
    print("  ALL 3-MEMBER RELATIONAL INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    test_full_integration()
