import streamlit as st
import db

st.set_page_config(page_title="Flight Operations | SkyFlow", page_icon="🛫", layout="wide")

st.title("🛫 Commercial Fleet & Flight Operations (Member 2)")
st.info("📌 **Owner:** Member 2 (Commercial Fleet & Flight Operations Lead)")

st.markdown("""
### Operational Scope
- Airline carriers, aircraft registrations (`VT-` tail numbers), and route scheduling.
- **Assigned Tables:** `AIRLINE`, `AIRCRAFT`, `FLIGHT`
- **Current Integration:** Flight lifecycles (`SCHEDULED` ➔ `BOARDING` ➔ `AIRBORNE` ➔ `LANDED`) transition dynamically upon clearances issued by Member 3.
""")

st.divider()

# Live Flight Schedule View
st.subheader("Current Flight Operations Registry")
flights = db.get_all_flights()
st.dataframe(flights, hide_index=True, use_container_width=True)
