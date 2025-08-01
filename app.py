import streamlit as st
import pyproj
import folium
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(page_title="EPSG Finder by Surabhi", layout="centered")

st.title("🗺️ EPSG & Coordinate System Finder")
st.markdown("Identify correct UTM zones, EPSG codes, and alternate projections from geographic coordinates.")

# ------------------------- Session State Init -----------------------
if "epsg_result" not in st.session_state:
    st.session_state.epsg_result = None

# ------------------------- Coordinate Format Selector -----------------------
format_option = st.selectbox(
    "Choose input coordinate format:",
    ["Decimal Degrees (DD)", "Degrees Minutes Seconds (DMS)"]
)

def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

st.markdown("### 📍 Input Coordinates (Single Point)")

if format_option == "Decimal Degrees (DD)":
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude (°)", format="%.6f", key="lat_dd")
    with col2:
        lon = st.number_input("Longitude (°)", format="%.6f", key="lon_dd")
else:
    st.markdown("#### Enter Latitude (DMS)")
    lat_deg = st.number_input("Degrees", key="lat_deg")
    lat_min = st.number_input("Minutes", key="lat_min")
    lat_sec = st.number_input("Seconds", key="lat_sec")
    lat_dir = st.selectbox("Direction", ["N", "S"], key="lat_dir")

    st.markdown("#### Enter Longitude (DMS)")
    lon_deg = st.number_input("Degrees", key="lon_deg")
    lon_min = st.number_input("Minutes", key="lon_min")
    lon_sec = st.number_input("Seconds", key="lon_sec")
    lon_dir = st.selectbox("Direction", ["E", "W"], key="lon_dir")

    lat = dms_to_dd(lat_deg, lat_min, lat_sec, lat_dir)
    lon = dms_to_dd(lon_deg, lon_min, lon_sec, lon_dir)

# ------------------------- Projection Logic -----------------------
def get_epsg(lat, lon):
    zone_number = int((lon + 180) / 6) + 1
    hemisphere = 'N' if lat >= 0 else 'S'
    epsg_code = 32600 + zone_number if lat >= 0 else 32700 + zone_number
    utm_zone = f"{zone_number}{hemisphere}"
    return utm_zone, epsg_code

def get_projection_info(lat, lon):
    wgs84 = pyproj.CRS("EPSG:4326")
    utm_zone, utm_epsg = get_epsg(lat, lon)
    utm = pyproj.CRS.from_epsg(utm_epsg)
    mercator = pyproj.CRS("EPSG:3857")
    return {
        "WGS84 (Geographic)": "EPSG:4326",
        f"UTM Zone {utm_zone}": f"EPSG:{utm_epsg}",
        "Web Mercator": "EPSG:3857",
        "Equal Earth": "EPSG:8857",
        "World Cylindrical Equal Area": "EPSG:54034"
    }

# ------------------------- Manual Button Logic -----------------------
if st.button("🔍 Find EPSG Code", key="manual_epsg"):
    if lat == 0 and lon == 0:
        st.warning("Please enter valid coordinates.")
        st.session_state.epsg_result = None
    else:
        projections = get_projection_info(lat, lon)
        st.session_state.epsg_result = {
            "lat": lat,
            "lon": lon,
            "projections": projections
        }

# Clear button
if st.button("❌ Clear Results"):
    st.session_state.epsg_result = None

# Display result
if st.session_state.epsg_result:
    lat = st.session_state.epsg_result["lat"]
    lon = st.session_state.epsg_result["lon"]
    projections = st.session_state.epsg_result["projections"]

    st.success(f"📌 Coordinates: ({lat:.6f}, {lon:.6f})")

    for name, code in projections.items():
        st.markdown(f"✅ {name}: **{code}**  [View](https://epsg.io/{code.split(':')[-1]})")

    st.markdown("### 🗺️ Location Map")
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip=f"EPSG:{get_epsg(lat, lon)[1]}").add_to(m)
    _ = st_folium(m, width=700, returned_objects=[])

# ------------------------- CSV Upload Section -----------------------
st.markdown("---")
st.markdown("### 📂 Upload CSV (Batch EPSG Lookup)")
st.info("Upload a CSV with `lat`, `lon` columns (decimal degrees format).")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.lower()

        if 'lat' in df.columns and 'lon' in df.columns:
            df = df[['lat', 'lon']].copy()
            df['UTM Zone'] = df.apply(lambda row: get_epsg(row['lat'], row['lon'])[0], axis=1)
            df['EPSG Code'] = df.apply(lambda row: get_epsg(row['lat'], row['lon'])[1], axis=1)
            df['EPSG Link'] = df['EPSG Code'].apply(lambda e: f"https://epsg.io/{e}")

            st.success(f"✅ Processed {len(df)} records.")
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download Result CSV", csv, "epsg_lookup_output.csv", "text/csv")
        else:
            st.error("CSV must have columns: 'lat', 'lon'")
    except Exception as e:
        st.error(f"Error processing file: {e}")

# ------------------------- Footer -----------------------
st.markdown("---")
st.markdown("""
Made with ❤️ by **Surabhi Gupta**  
🔗 [LinkedIn](https://www.linkedin.com/in/surabhiguptageo) · 📰 [Substack](https://geocloudinsights.substack.com)
""", unsafe_allow_html=True)
