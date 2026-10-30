"""
SkyFlow ATCMS - Member 2 Automated Verification & Test Suite (verify_member2.py)
Domain: Commercial Fleet & Flight Operations Subsystem

Validates:
1. Schema & Table Integrity (AIRLINE, AIRCRAFT, FLIGHT).
2. Database Constraint Rejections (Circular route, Inverted schedule, Unique flight number).
3. Member 2 CRUD Database Operations (INSERT, SELECT, UPDATE, DELETE).
4. Analytical Queries (Carrier OTP, High-Density Corridors, Correlated & Scalar Subqueries).
"""

import sys
from datetime import datetime, date, timedelta
import db

def run_tests():
    print("=" * 75)
    print("SKYFLOW ATCMS: MEMBER 2 AUTOMATED TEST & VERIFICATION SUITE")
    print("Domain: Commercial Fleet & Flight Operations (Member 2)")
    print("=" * 75)

    passed_count = 0
    total_tests = 0

    def assert_test(name: str, condition: bool, details: str = ""):
        nonlocal passed_count, total_tests
        total_tests += 1
        if condition:
            print(f" [PASS] Test {total_tests:02d}: {name}")
            passed_count += 1
        else:
            print(f" [FAIL] Test {total_tests:02d}: {name} - {details}")

    # TEST 1: Database Status & Tables
    print("\n--- 1. DATABASE CONNECTIVITY & SCHEMA VERIFICATION ---")
    status = db.get_database_status()
    assert_test("Database Connected", status["connected"] is True, f"Engine: {status['engine']}")
    assert_test("AIRLINE Table Populated", status["counts"].get("AIRLINE", 0) >= 4, f"Count: {status['counts'].get('AIRLINE')}")
    assert_test("AIRCRAFT Table Populated", status["counts"].get("AIRCRAFT", 0) >= 6, f"Count: {status['counts'].get('AIRCRAFT')}")
    assert_test("FLIGHT Table Populated", status["counts"].get("FLIGHT", 0) >= 5, f"Count: {status['counts'].get('FLIGHT')}")

    # TEST 2: Domain Constraints Enforcement
    print("\n--- 2. DATABASE INTEGRITY CONSTRAINT ENFORCEMENT ---")
    
    # 2.1 Rejection of circular flight (origin == dest)
    succ, msg = db.add_flight(
        flight_number="TEST-001",
        flight_date_val="2026-11-15",
        airline_id=1,
        aircraft_reg_no="VT-ISN",
        origin_airport="DEL",
        dest_airport="DEL", # Circular route!
        scheduled_departure="2026-11-15 10:00:00",
        scheduled_arrival="2026-11-15 12:00:00"
    )
    assert_test("Rejection of Circular Route (origin = dest)", succ is False and "same aerodrome" in msg.lower(), f"Response: {msg}")

    # 2.2 Rejection of inverted schedule (arrival <= departure)
    succ, msg = db.add_flight(
        flight_number="TEST-002",
        flight_date_val="2026-11-15",
        airline_id=1,
        aircraft_reg_no="VT-ISN",
        origin_airport="DEL",
        dest_airport="BOM",
        scheduled_departure="2026-11-15 14:00:00",
        scheduled_arrival="2026-11-15 12:00:00" # Arrival before departure!
    )
    assert_test("Rejection of Inverted Schedule (arrival <= departure)", succ is False and "strictly after" in msg.lower(), f"Response: {msg}")

    # TEST 3: CRUD Operations Execution
    print("\n--- 3. MEMBER 2 CRUD OPERATIONS (INSERT, SELECT, UPDATE, DELETE) ---")
    
    # 3.1 INSERT Operation
    test_flight_no = f"6E-TST-{int(datetime.now().timestamp()) % 10000}"
    test_date = "2026-11-20"
    succ, msg = db.add_flight(
        flight_number=test_flight_no,
        flight_date_val=test_date,
        airline_id=1,
        aircraft_reg_no="VT-ISN",
        origin_airport="DEL",
        dest_airport="BOM",
        scheduled_departure="2026-11-20 06:00:00",
        scheduled_arrival="2026-11-20 08:15:00",
        current_status="SCHEDULED"
    )
    assert_test("INSERT Operation: Schedule New Flight", succ is True, f"Response: {msg}")

    # 3.2 Duplicate flight rejection (UNIQUE constraint)
    succ_dup, msg_dup = db.add_flight(
        flight_number=test_flight_no,
        flight_date_val=test_date,
        airline_id=1,
        aircraft_reg_no="VT-ISN",
        origin_airport="DEL",
        dest_airport="BOM",
        scheduled_departure="2026-11-20 09:00:00",
        scheduled_arrival="2026-11-20 11:15:00"
    )
    assert_test("Rejection of Duplicate (flight_number, flight_date)", succ_dup is False, f"Response: {msg_dup}")

    # 3.3 SELECT Operation
    flights = db.get_flights(search=test_flight_no)
    created_flight = flights[0] if flights else None
    assert_test("SELECT Operation: Retrieve Inserted Flight", created_flight is not None and created_flight["flight_number"] == test_flight_no)

    if created_flight:
        fid = created_flight["flight_id"]
        
        # 3.4 UPDATE Operation (State Transition)
        succ_upd, msg_upd = db.update_flight_status(
            flight_id=fid,
            new_status="AIRBORNE",
            actual_departure="2026-11-20 06:10:00"
        )
        assert_test("UPDATE Operation: Status Transition to AIRBORNE", succ_upd is True, f"Response: {msg_upd}")
        
        # 3.5 UPDATE Operation (Delay Logging)
        succ_dly, msg_dly = db.apply_departure_delay(flight_id=fid, delay_minutes=25)
        assert_test("UPDATE Operation: Apply Departure Delay (25 min)", succ_dly is True, f"Response: {msg_dly}")

        # 3.6 DELETE / Cancellation Operation
        succ_del, msg_del = db.cancel_or_delete_flight(flight_id=fid, hard_delete=True)
        assert_test("DELETE Operation: Permanent Removal of Test Leg", succ_del is True, f"Response: {msg_del}")

    # TEST 4: Complex SQL Syllabus Queries & Analytics
    print("\n--- 4. COMPLEX SQL QUERIES & ANALYTICAL METRICS ---")
    
    # 4.1 On-Time Performance (OTP)
    otp_data = db.get_otp_analytics()
    assert_test("Query 1 (JOIN, Aggregates, CASE): Carrier OTP", len(otp_data) >= 4 and "otp_rate_percentage" in otp_data[0])

    # 4.2 Route Density (GROUP BY + HAVING)
    routes = db.get_route_density_analytics(min_flights=1)
    assert_test("Query 2 (GROUP BY, HAVING): High-Density Corridors", len(routes) > 0 and "route_corridor" in routes[0])

    # 4.3 Excessive Delays (Correlated Subquery)
    delays = db.get_excessive_delays(threshold_minutes=30)
    assert_test("Query 3 (Correlated Subquery): Flights Delayed > 30 Mins", isinstance(delays, list))

    # 4.4 Fleet Capacity (Scalar Subquery)
    cap = db.get_fleet_capacity_report()
    assert_test("Query 4 (Scalar Subquery): Aircraft Above Avg Capacity", len(cap) > 0 and "seats_above_fleet_avg" in cap[0])

    # 4.5 Evaluator SQL Terminal Execution
    succ_sql, sql_res = db.execute_raw_sql("SELECT COUNT(*) AS total_carriers FROM AIRLINE")
    assert_test("Raw SQL Demonstrator Engine", succ_sql is True and sql_res["data"][0]["total_carriers"] >= 4)

    # SUMMARY
    print("\n" + "=" * 75)
    print(f"VERIFICATION SUMMARY: {passed_count}/{total_tests} Tests Passed ({(passed_count/total_tests)*100:.1f}%)")
    print("=" * 75)
    
    return passed_count == total_tests

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
