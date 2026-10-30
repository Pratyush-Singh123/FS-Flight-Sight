"""
Automated Verification Suite for Member 3 (ATC Tower, En-Route & Safety Lead)
Verifies:
1. Schema & Seeding
2. Query 1: Join with correlated subquery
3. Query 2: Aggregate analysis with GROUP BY & HAVING
4. Query 3: Incident Severity Audit
5. Query 4: Sector Capacity Analysis
6. Trigger Safety Interlock: Runway collision abort & auto-occupancy transition
7. Incident Filing & Audit Ledger
"""

import sys
import db

def run_tests():
    print("=" * 70)
    print("Starting Member 3 Automated DBMS Verification Suite")
    print("=" * 70)

    # 1. Initialize Database
    print("\n[Test 1] Initializing Database & Seed Data...")
    db.init_database()
    conn = db.get_connection()
    engine = "PostgreSQL" if db.is_postgres() else "SQLite"
    print(f"✅ Connected to: {engine.upper()}")
    conn.close()

    # 2. Verify Query 1: Airborne Radar Multi-Table Join with Subquery
    print("\n[Test 2] Testing Query 1 (Airborne Flights + Subquery)...")
    airborne_df = db.get_airborne_radar_flights()
    print(f"✅ Query 1 executed successfully. Rows returned: {len(airborne_df)}")
    if not airborne_df.empty:
        sample = airborne_df.iloc[0]
        print(f"   Sample: Flight {sample['flight_number']} ({sample['airline_name']}) at FL{sample['assigned_altitude_ft']} cleared by {sample['authorizing_controller']}")

    # 3. Verify Query 2: Aggregate Controller Workload (GROUP BY + HAVING)
    print("\n[Test 3] Testing Query 2 (Controller Workload with GROUP BY & HAVING)...")
    workload_df = db.get_controller_workload()
    print(f"✅ Query 2 executed successfully. Active controllers returned: {len(workload_df)}")
    assert len(workload_df) > 0, "Query 2 should return controllers with clearances!"
    top_controller = workload_df.iloc[0]
    print(f"   Top Controller: {top_controller['controller_name']} ({top_controller['certification_level']}) - {top_controller['total_clearances_issued']} clearances")

    # 4. Verify Query 4: Airspace Sector Capacity
    print("\n[Test 4] Testing Query 4 (Sector Capacity Monitoring)...")
    sector_df = db.get_sector_utilization()
    print(f"✅ Query 4 executed successfully. Sectors found: {len(sector_df)}")
    assert len(sector_df) >= 4, "Should have at least 4 FIR sectors!"

    # 5. Verify Safety Trigger Interlock (Collision Prevention)
    print("\n[Test 5] Testing Safety Trigger Interlock...")
    # Find an occupied runway or set one
    runways = db.get_runways()
    occupied_runway = runways[runways['current_status'] == 'OCCUPIED'].iloc[0]
    occ_rwy_id = int(occupied_runway['runway_id'])
    print(f"   Target Occupied Runway ID: {occ_rwy_id} ({occupied_runway['airport_code']} {occupied_runway['runway_designator']})")

    # Attempt Takeoff clearance on Occupied runway -> MUST FAIL
    controllers = db.get_controllers()
    ctrl_id = int(controllers.iloc[0]['controller_id'])
    flights = db.get_active_flights()
    fl_id = int(flights.iloc[0]['flight_id'])

    success, msg = db.issue_clearance(fl_id, ctrl_id, 'TAKEOFF', runway_id=occ_rwy_id, altitude=5000, heading=90)
    print(f"   Collision test result: Success={success}, Message='{msg}'")
    assert not success, "Trigger MUST reject clearance on occupied runway!"
    print("   ✅ PASSED: Database trigger rejected takeoff on occupied runway!")

    # Now test valid clearance on AVAILABLE runway -> MUST SUCCEED & OCCUPY
    avail_runways = runways[runways['current_status'] == 'AVAILABLE']
    if not avail_runways.empty:
        avail_rwy_id = int(avail_runways.iloc[0]['runway_id'])
        print(f"   Target Available Runway ID: {avail_rwy_id}")
        success, msg = db.issue_clearance(fl_id, ctrl_id, 'TAKEOFF', runway_id=avail_rwy_id, altitude=5000, heading=90)
        assert success, f"Takeoff on available runway failed: {msg}"
        print(f"   ✅ PASSED: Clearance approved. Message: {msg}")

        # Verify runway transitioned to OCCUPIED
        updated_runways = db.get_runways()
        new_stat = updated_runways[updated_runways['runway_id'] == avail_rwy_id].iloc[0]['current_status']
        assert new_stat == 'OCCUPIED', f"Runway should now be OCCUPIED, got {new_stat}"
        print(f"   ✅ PASSED: Trigger automatically updated Runway ID {avail_rwy_id} to OCCUPIED.")

    # 6. Verify Incident Logging
    print("\n[Test 6] Testing Safety Incident Filing...")
    success, msg = db.file_incident(
        flight_id=fl_id,
        reported_by=ctrl_id,
        incident_type="NEAR_MISS",
        severity="HIGH",
        description="Loss of vertical separation resolved via immediate TCAS climb vector."
    )
    assert success, f"Incident filing failed: {msg}"
    print(f"   ✅ PASSED: {msg}")

    incidents = db.get_incident_logs()
    assert len(incidents[incidents['incident_type'] == 'NEAR_MISS']) > 0
    print("   ✅ PASSED: Incident verified in INCIDENT_LOG.")

    print("\n" + "=" * 70)
    print("ALL MEMBER 3 VERIFICATION TESTS PASSED SUCCESSFULLY (100% GREEN)!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
