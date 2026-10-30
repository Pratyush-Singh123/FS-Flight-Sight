"""
SkyFlow ATCMS - Commercial Fleet & Flight Operations Portal (Page 2)
Owned by: Member 2 (Commercial Fleet & Flight Operations Lead)
Course: Database Management Systems (DBMS)

Tables Managed: AIRLINE, AIRCRAFT, FLIGHT
Core Functionality:
1. Live Flight Dispatch Board (SELECT & Multi-Filter Search)
2. Flight Scheduling Portal (INSERT with Constraint Enforcement)
3. Operational State Transition & Delay Logger (UPDATE)
4. Flight Cancellation & Removal (DELETE with Referential Integrity Checks)
5. Real-Time Operations Analytics & Course SQL Demonstrator (Reports & Queries)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import db

st.set_page_config(
    page_title="Flight Operations Portal - Member 2",
    page_icon="🛫",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .page-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-airborne { background-color: #DEF7EC; color: #03543F; }
    .status-scheduled { background-color: #E1EFFE; color: #1E429F; }
    .status-boarding { background-color: #FEF08A; color: #854D0E; }
    .status-landed { background-color: #F3F4F6; color: #374151; }
    .status-cancelled { background-color: #FDE8E8; color: #9B1C1C; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">🛫 Flight Operations & Dispatch Portal</div>', unsafe_allow_html=True)
st.caption("SkyFlow ATCMS Subsystem | **Member 2 Scope:** Airlines, Aircraft Fleet & Domestic Route Scheduling")

# Top KPI Metric Cards
all_flights = db.get_flights()
total_flights = len(all_flights)
airborne_count = sum(1 for f in all_flights if f["current_status"] == "AIRBORNE")
boarding_count = sum(1 for f in all_flights if f["current_status"] in ("BOARDING", "TAXIING"))
otp_data = db.get_otp_analytics()

# Calculate overall average OTP
avg_otp = 0.0
avg_delay = 0.0
if otp_data:
    rates = [o["otp_rate_percentage"] for o in otp_data if o["departed_legs"] > 0]
    avg_otp = sum(rates) / len(rates) if rates else 100.0
    delays = [o["avg_delay_mins"] for o in otp_data if o["departed_legs"] > 0]
    avg_delay = sum(delays) / len(delays) if delays else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Scheduled Domestic Legs", total_flights)
kpi2.metric("Active Airborne Aircraft", airborne_count)
kpi3.metric("Fleet-wide Average OTP", f"{avg_otp:.1f}%", help="On-Time Performance within 15-minute buffer")
kpi4.metric("Average Departure Delay", f"{avg_delay:.1f} mins")

st.markdown("---")

# Main Functional Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Dispatch Board & Search",
    "➕ Schedule New Flight (INSERT)",
    "⏱️ Lifecycle & Delay Updater (UPDATE)",
    "❌ Cancel / Remove Flight (DELETE)",
    "📊 Operations Analytics & SQL Lab"
])

# ============================================================================
# TAB 1: FLIGHT DISPATCH BOARD & MULTI-FILTER SEARCH (SELECT)
# ============================================================================
with tab1:
    st.subheader("📋 Live Indian Airspace Flight Dispatch Board")
    st.markdown("Query, filter, and inspect commercial flight operations across 12 domestic hub aerodromes.")

    # Filter Controls
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
    
    with f_col1:
        search_query = st.text_input("🔍 Search Flight / Reg No.", placeholder="e.g. 6E-204 or VT-ISN")
    
    with f_col2:
        status_options = ["ALL", "SCHEDULED", "BOARDING", "TAXIING", "AIRBORNE", "LANDED", "DIVERTED", "CANCELLED"]
        selected_status = st.selectbox("Status Filter", status_options)
        
    with f_col3:
        airports = db.get_airports()
        apt_codes = ["ALL"] + [a["airport_code"] for a in airports]
        selected_origin = st.selectbox("Origin Airport", apt_codes)
        
    with f_col4:
        selected_dest = st.selectbox("Destination Airport", apt_codes)
        
    with f_col5:
        airlines = db.get_airlines()
        airline_map = {a["airline_name"]: a["airline_id"] for a in airlines}
        airline_filter_options = ["ALL"] + list(airline_map.keys())
        selected_airline_name = st.selectbox("Operating Carrier", airline_filter_options)
        selected_airline_id = airline_map.get(selected_airline_name, 0) if selected_airline_name != "ALL" else None

    # Fetch Filtered Data
    filtered_flights = db.get_flights(
        search=search_query if search_query else None,
        status=selected_status,
        origin=selected_origin,
        dest=selected_dest,
        airline_id=selected_airline_id
    )

    if filtered_flights:
        # Display as styled dataframe
        table_records = []
        for f in filtered_flights:
            table_records.append({
                "ID": f["flight_id"],
                "Flight #": f["flight_number"],
                "Date": f["flight_date"],
                "Airline": f["airline_name"],
                "Tail Reg": f["aircraft_reg_no"],
                "Aircraft Model": f["aircraft_model"],
                "Route": f"{f['origin_airport']} ({f['origin_city']}) ➔ {f['dest_airport']} ({f['dest_city']})",
                "Sched Dep": str(f["scheduled_departure"])[:16],
                "Sched Arr": str(f["scheduled_arrival"])[:16],
                "Status": f["current_status"],
                "Delay (min)": int(f.get("departure_delay_minutes", 0))
            })
        
        df_display = pd.DataFrame(table_records)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered_flights)} matching flight leg(s) from relational database.")
        
        # Flight Details Drawer
        with st.expander("🔎 Detailed Flight Inspector"):
            inspect_id = st.selectbox("Select Flight to Inspect", [f["ID"] for f in table_records], format_func=lambda x: f"Flight ID {x}: " + next(t["Flight #"] + " (" + t["Route"] + ")" for t in table_records if t["ID"] == x))
            selected_f = next(f for f in filtered_flights if f["flight_id"] == inspect_id)
            
            c_ins1, c_ins2, c_ins3 = st.columns(3)
            with c_ins1:
                st.markdown(f"**Flight Number:** `{selected_f['flight_number']}`")
                st.markdown(f"**Operating Carrier:** {selected_f['airline_name']} (`{selected_f['callsign_prefix']}`)")
                st.markdown(f"**Status:** `{selected_f['current_status']}`")
            with c_ins2:
                st.markdown(f"**Assigned Airframe:** `{selected_f['aircraft_reg_no']}` ({selected_f['aircraft_model']})")
                st.markdown(f"**Seating Capacity:** {selected_f['passenger_capacity']} seats")
                st.markdown(f"**Departure Delay:** {int(selected_f.get('departure_delay_minutes', 0))} minutes")
            with c_ins3:
                st.markdown(f"**Origin Aerodrome:** {selected_f['origin_airport']} - {selected_f['origin_airport_name']}")
                st.markdown(f"**Destination Aerodrome:** {selected_f['dest_airport']} - {selected_f['dest_airport_name']}")
                st.markdown(f"**Actual Off-Ground:** `{selected_f['actual_departure'] or 'Pending'}`")
    else:
        st.warning("No flight legs match your search filters.")


# ============================================================================
# TAB 2: SCHEDULE NEW FLIGHT (INSERT & CONSTRAINTS)
# ============================================================================
with tab2:
    st.subheader("➕ Schedule New Commercial Flight Leg")
    st.markdown("Register a new domestic flight leg into the system. **Strict database constraints are enforced.**")

    with st.form("schedule_flight_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            new_flt_num = st.text_input("Flight Number *", placeholder="e.g. 6E-901, AI-302", help="Commercial flight identifier")
            new_flt_date = st.date_input("Operational Date *", value=date(2026, 11, 1))
            
            # Carrier selector
            carrier_dict = {a["airline_name"]: a["airline_id"] for a in airlines}
            selected_carrier_name = st.selectbox("Operating Carrier *", list(carrier_dict.keys()))
            selected_carrier_id = carrier_dict[selected_carrier_name]
            
        with c2:
            # Aircraft selector filtered by carrier
            carrier_aircraft = db.get_aircraft(airline_id=selected_carrier_id)
            if carrier_aircraft:
                ac_labels = [f"{ac['aircraft_reg_no']} ({ac['model']} - {ac['passenger_capacity']} seats)" for ac in carrier_aircraft]
                ac_map = {ac_labels[i]: carrier_aircraft[i]["aircraft_reg_no"] for i in range(len(carrier_aircraft))}
                selected_ac_label = st.selectbox("Assigned Aircraft (DGCA Fleet) *", ac_labels)
                selected_ac_reg = ac_map[selected_ac_label]
            else:
                st.error("No aircraft registered for selected airline!")
                selected_ac_reg = None

            apt_list = db.get_airports()
            apt_code_list = [a["airport_code"] for a in apt_list]
            apt_display_map = {a["airport_code"]: f"{a['airport_code']} - {a['city']} ({a['airport_name']})" for a in apt_list}

            new_origin = st.selectbox("Origin Airport *", apt_code_list, format_func=lambda x: apt_display_map[x], index=0)
            new_dest = st.selectbox("Destination Airport *", apt_code_list, format_func=lambda x: apt_display_map[x], index=1)

        with c3:
            sched_dep_time = st.time_input("Scheduled Departure Time *", value=time(14, 0))
            sched_arr_time = st.time_input("Scheduled Arrival Time *", value=time(16, 15))
            initial_status = st.selectbox("Initial Flight Status", ["SCHEDULED", "BOARDING"])

        st.markdown("""
        > [!NOTE]
        > **Relational Constraints Enforced:**
        > 1. `origin_airport <> dest_airport` (Rejection of circular routes).
        > 2. `scheduled_arrival > scheduled_departure` (Chronological causality).
        > 3. `UNIQUE(flight_number, flight_date)` (Zero duplicate flight legs on identical dates).
        """)

        submitted = st.form_submit_button("🚀 Submit Flight Schedule to Database", use_container_width=True)

        if submitted:
            # Construct timestamps
            dep_dt = datetime.combine(new_flt_date, sched_dep_time)
            arr_dt = datetime.combine(new_flt_date, sched_arr_time)
            
            # If arrival time is earlier than departure time on the same date, handle overnight or flag error
            if arr_dt <= dep_dt:
                # Could be overnight or constraint violation
                pass
                
            dep_str = dep_dt.strftime("%Y-%m-%d %H:%M:%S")
            arr_str = arr_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            if not new_flt_num.strip():
                st.error("Validation Error: Flight number cannot be empty.")
            elif not selected_ac_reg:
                st.error("Validation Error: Please select a valid aircraft.")
            else:
                success, msg = db.add_flight(
                    flight_number=new_flt_num,
                    flight_date_val=str(new_flt_date),
                    airline_id=selected_carrier_id,
                    aircraft_reg_no=selected_ac_reg,
                    origin_airport=new_origin,
                    dest_airport=new_dest,
                    scheduled_departure=dep_str,
                    scheduled_arrival=arr_str,
                    current_status=initial_status
                )
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ============================================================================
# TAB 3: LIFECYCLE & DELAY UPDATER (UPDATE)
# ============================================================================
with tab3:
    st.subheader("⏱️ Flight Operational Lifecycle & Delay Manager")
    st.markdown("Transition flight operational states (`SCHEDULED` ➔ `BOARDING` ➔ `TAXIING` ➔ `AIRBORNE` ➔ `LANDED`) or record ground delays.")

    active_flights = db.get_flights()
    if active_flights:
        flt_options = {
            f["flight_id"]: f"{f['flight_number']} ({f['origin_airport']} ➔ {f['dest_airport']}) | Status: {f['current_status']} | Tail: {f['aircraft_reg_no']}"
            for f in active_flights
        }
        selected_fid = st.selectbox("Select Target Flight Leg", list(flt_options.keys()), format_func=lambda x: flt_options[x])
        curr_f = next(f for f in active_flights if f["flight_id"] == selected_fid)

        col_curr, col_act = st.columns([1, 2])
        
        with col_curr:
            st.markdown("#### Current State")
            st.info(f"""
            - **Flight:** `{curr_f['flight_number']}`
            - **Current Status:** `{curr_f['current_status']}`
            - **Scheduled Dep:** `{str(curr_f['scheduled_departure'])[:16]}`
            - **Actual Dep:** `{str(curr_f['actual_departure'])[:16] if curr_f['actual_departure'] else 'None'}`
            - **Delay:** `{int(curr_f.get('departure_delay_minutes', 0))} minutes`
            """)

        with col_act:
            st.markdown("#### Operational Action")
            action_mode = st.radio("Choose Action", ["Advance Flight Lifecycle State", "Log Ground / Departure Delay Minutes"], horizontal=True)
            
            if action_mode == "Advance Flight Lifecycle State":
                lifecycle_states = ["SCHEDULED", "BOARDING", "TAXIING", "AIRBORNE", "LANDED", "DIVERTED", "CANCELLED"]
                current_idx = lifecycle_states.index(curr_f["current_status"]) if curr_f["current_status"] in lifecycle_states else 0
                next_status = st.selectbox("Target Lifecycle State", lifecycle_states, index=min(current_idx + 1, len(lifecycle_states) - 1))
                
                auto_dep_time = None
                auto_arr_time = None
                
                if next_status == "AIRBORNE" and not curr_f["actual_departure"]:
                    st.caption("ℹ️ Transitioning to AIRBORNE will automatically record the actual departure timestamp.")
                    auto_dep_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elif next_status == "LANDED" and not curr_f["actual_arrival"]:
                    st.caption("ℹ️ Transitioning to LANDED will automatically record touchdown timestamp.")
                    auto_arr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if st.button("🔄 Execute State Transition (UPDATE)", type="primary"):
                    succ, res_msg = db.update_flight_status(
                        flight_id=selected_fid,
                        new_status=next_status,
                        actual_departure=auto_dep_time,
                        actual_arrival=auto_arr_time
                    )
                    if succ:
                        st.success(f"✅ {res_msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {res_msg}")
                        
            else:
                delay_input = st.number_input("Departure Delay to Log (Minutes)", min_value=5, max_value=300, value=25, step=5)
                if st.button("⏱️ Apply Delay & Recalculate Schedule (UPDATE)", type="primary"):
                    succ, res_msg = db.apply_departure_delay(selected_fid, delay_input)
                    if succ:
                        st.success(f"✅ {res_msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {res_msg}")
    else:
        st.warning("No flight legs currently available to update.")


# ============================================================================
# TAB 4: CANCEL / REMOVE FLIGHT (DELETE)
# ============================================================================
with tab4:
    st.subheader("❌ Cancel or Delete Flight Leg")
    st.markdown("""
    Perform removal or formal operational cancellation of flight legs.
    **Database Referential Integrity:** Deletion is guarded against violating foreign-key constraints on terminal gate assignments or ATC clearance ledgers.
    """)

    all_cancel_flights = db.get_flights()
    if all_cancel_flights:
        del_dict = {
            f["flight_id"]: f"ID {f['flight_id']}: {f['flight_number']} ({f['origin_airport']} ➔ {f['dest_airport']}) | Status: {f['current_status']}"
            for f in all_cancel_flights
        }
        del_fid = st.selectbox("Select Flight Leg to Cancel / Remove", list(del_dict.keys()), format_func=lambda x: del_dict[x])
        target_f = next(f for f in all_cancel_flights if f["flight_id"] == del_fid)

        c_del1, c_del2 = st.columns(2)
        with c_del1:
            st.warning(f"**Target Flight:** `{target_f['flight_number']}` on `{target_f['flight_date']}`")
            st.markdown(f"- **Carrier:** {target_f['airline_name']}\n- **Route:** {target_f['origin_airport']} ➔ {target_f['dest_airport']}\n- **Current Status:** `{target_f['current_status']}`")

        with c_del2:
            st.markdown("#### Select Deletion Policy")
            del_policy = st.radio(
                "Deletion Method",
                [
                    "Soft Cancel (Recommended: sets status to CANCELLED, preserves audit trail)",
                    "Hard Delete (Issues SQL DELETE FROM FLIGHT, strictly checked against FK dependencies)"
                ]
            )
            
            is_hard = "Hard Delete" in del_policy
            
            if st.button("⚠️ Confirm Cancellation / Deletion", type="primary" if is_hard else "secondary"):
                succ, res_msg = db.cancel_or_delete_flight(flight_id=del_fid, hard_delete=is_hard)
                if succ:
                    st.success(f"✅ {res_msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {res_msg}")
    else:
        st.info("No flights available in database.")


# ============================================================================
# TAB 5: OPERATIONS ANALYTICS & COURSE SQL DEMONSTRATOR
# ============================================================================
with tab5:
    st.subheader("📊 Operational Analytics & Course SQL Demonstrator")
    st.markdown("Live aggregate reports, On-Time Performance (OTP) analytics, and SQL syllabus query demonstrations.")

    sub_view = st.selectbox(
        "Choose Report / Demonstration View",
        [
            "1. Carrier On-Time Performance (OTP) Analysis",
            "2. High-Density Flight Corridors & Bottleneck Report",
            "3. Excessive Delays Audit Log (>30 min Correlated Subquery)",
            "4. Fleet Capacity Benchmark vs Industry Average (Scalar Subquery)",
            "5. Interactive SQL Query Terminal (Live Course Evaluator Console)"
        ]
    )

    if "1. Carrier On-Time Performance" in sub_view:
        st.markdown("#### 🏆 Carrier Punctuality & OTP Benchmark (DGCA 15-Minute Rule)")
        st.markdown("""
        **DBMS Syllabus Concepts Demonstrated:** Multi-table `JOIN`, `CASE` conditional aggregation,
        arithmetic interval calculations, `COUNT`, `SUM`, `AVG`, `GROUP BY`, and `ORDER BY`.
        """)
        
        otp_records = db.get_otp_analytics()
        if otp_records:
            df_otp = pd.DataFrame(otp_records)
            df_otp_display = df_otp.rename(columns={
                "airline_name": "Operating Airline",
                "callsign_prefix": "Callsign",
                "scheduled_legs": "Total Scheduled",
                "departed_legs": "Total Departed",
                "on_time_count": "On-Time (<= 15 min)",
                "delayed_count": "Delayed (> 15 min)",
                "otp_rate_percentage": "OTP Rate (%)",
                "avg_delay_mins": "Avg Delay (mins)"
            })
            st.dataframe(df_otp_display, use_container_width=True, hide_index=True)
            
            # Interactive Bar Chart
            st.markdown("##### 📈 Airline OTP Comparison Chart")
            chart_data = df_otp[df_otp["departed_legs"] > 0][["airline_name", "otp_rate_percentage"]].set_index("airline_name")
            st.bar_chart(chart_data)

    elif "2. High-Density Flight Corridors" in sub_view:
        st.markdown("#### 🛣️ High-Density Airspace Corridors & Route Congestion")
        st.markdown("""
        **DBMS Syllabus Concepts Demonstrated:** Multi-table `JOIN`, string concatenation (`||`),
        `GROUP BY` origin and destination, aggregate functions (`COUNT`, `MIN`, `MAX`), and `HAVING COUNT(*) >= N`.
        """)
        min_f = st.slider("Filter Minimum Scheduled Flights per Corridor", min_value=1, max_value=5, value=1)
        routes = db.get_route_density_analytics(min_flights=min_f)
        if routes:
            df_routes = pd.DataFrame(routes)
            st.dataframe(df_routes, use_container_width=True, hide_index=True)
        else:
            st.info("No routes meet the minimum flight threshold.")

    elif "3. Excessive Delays Audit Log" in sub_view:
        st.markdown("#### ⚠️ Excessive Departure Delays Investigation")
        st.markdown("""
        **DBMS Syllabus Concepts Demonstrated:** Correlated Subquery `WHERE flight_id IN (SELECT ... WHERE delay > threshold)`,
        timestamp arithmetic, and multi-table relational joins with dispatch contact emails.
        """)
        thresh = st.slider("Delay Threshold in Minutes", min_value=15, max_value=60, value=30, step=5)
        delays = db.get_excessive_delays(threshold_minutes=thresh)
        if delays:
            st.dataframe(pd.DataFrame(delays), use_container_width=True, hide_index=True)
        else:
            st.success(f"No flights currently delayed beyond {thresh} minutes!")

    elif "4. Fleet Capacity Benchmark" in sub_view:
        st.markdown("#### ✈️ Fleet Seating Capacity vs. Industry Average")
        st.markdown("""
        **DBMS Syllabus Concepts Demonstrated:** Scalar Subquery in `WHERE` clause:
        `WHERE ac.passenger_capacity > (SELECT AVG(passenger_capacity) FROM AIRCRAFT)`.
        """)
        cap_report = db.get_fleet_capacity_report()
        if cap_report:
            st.dataframe(pd.DataFrame(cap_report), use_container_width=True, hide_index=True)
        else:
            st.info("No aircraft above average capacity.")

    elif "5. Interactive SQL Query Terminal" in sub_view:
        st.markdown("#### 💻 Interactive SQL Query Terminal")
        st.markdown("Run custom SQL queries directly against the active relational database.")

        sample_queries = {
            "Query 1: Airline OTP Aggregation": """SELECT 
    al.airline_name,
    COUNT(f.flight_id) AS scheduled_legs,
    SUM(CASE WHEN f.actual_departure IS NOT NULL THEN 1 ELSE 0 END) AS departed_legs
FROM AIRLINE al
LEFT JOIN FLIGHT f ON al.airline_id = f.airline_id
GROUP BY al.airline_name;""",
            "Query 2: High-Density Corridors (HAVING Clause)": """SELECT 
    f.origin_airport || ' -> ' || f.dest_airport AS corridor,
    COUNT(f.flight_id) AS flight_count
FROM FLIGHT f
GROUP BY f.origin_airport, f.dest_airport
HAVING COUNT(f.flight_id) >= 2;""",
            "Query 3: Scalar Subquery - Aircraft Above Average Capacity": """SELECT 
    aircraft_reg_no, model, passenger_capacity
FROM AIRCRAFT
WHERE passenger_capacity > (SELECT AVG(passenger_capacity) FROM AIRCRAFT);""",
            "Query 4: Active Airborne Radar Telemetry": """SELECT 
    f.flight_number, al.airline_name, f.aircraft_reg_no, f.origin_airport, f.dest_airport, f.current_status
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
WHERE f.current_status = 'AIRBORNE';"""
        }

        chosen_sample = st.selectbox("Load Sample Syllabus Query", list(sample_queries.keys()))
        sql_input = st.text_area("SQL Statement", value=sample_queries[chosen_sample], height=160)

        if st.button("⚡ Execute SQL Query", type="primary"):
            success, result = db.execute_raw_sql(sql_input)
            if success:
                st.success("Query executed successfully!")
                if isinstance(result, dict) and "data" in result:
                    st.dataframe(pd.DataFrame(result["data"]), use_container_width=True)
                else:
                    st.info(str(result))
            else:
                st.error(f"SQL Error: {result}")
