import streamlit as st
from pyproj import CRS, Transformer
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

st.set_page_config(page_title="Parcel Area Calculator", layout="centered")
st.title("Parcel Area Calculator 📐")
st.markdown("Enter four corner points of your land parcel by specifying degrees, minutes, and seconds (numeric inputs).")

# Convert DMS to decimal degrees
def dms_to_decimal(deg, mins, secs, sign):
    dd = float(deg) + float(mins) / 60 + float(secs) / 3600
    return -dd if sign == '-' else dd

# Input collection
points_dd = []  # list of (lat, lon) in decimal degrees
for i in range(1, 5):
    st.subheader(f"Point #{i}")
    lon_deg = st.number_input(f"Lon ° (P{i})", min_value=0, max_value=180, step=1, key=f"lon_deg_{i}")
    lon_min = st.number_input(f"Lon ' (P{i})", min_value=0, max_value=59, step=1, key=f"lon_min_{i}")
    lon_sec = st.number_input(f"Lon \" (P{i})", min_value=0.0, max_value=59.999, step=0.001, format="%.3f", key=f"lon_sec_{i}")
    lon_sign = st.selectbox(f"E/W (P{i})", options=["E", "W"], key=f"lon_sign_{i}")

    lat_deg = st.number_input(f"Lat ° (P{i})", min_value=0, max_value=90, step=1, key=f"lat_deg_{i}")
    lat_min = st.number_input(f"Lat ' (P{i})", min_value=0, max_value=59, step=1, key=f"lat_min_{i}")
    lat_sec = st.number_input(f"Lat \" (P{i})", min_value=0.0, max_value=59.999, step=0.001, format="%.3f", key=f"lat_sec_{i}")
    lat_sign = st.selectbox(f"N/S (P{i})", options=["N", "S"], key=f"lat_sign_{i}")

    lon_dd = dms_to_decimal(lon_deg, lon_min, lon_sec, '-' if lon_sign=='W' else '+')
    lat_dd = dms_to_decimal(lat_deg, lat_min, lat_sec, '-' if lat_sign=='S' else '+')
    points_dd.append((lat_dd, lon_dd))

if st.button("Calculate Area"):
    try:
        # UTM projection
        center_lon = sum(lon for lat, lon in points_dd) / len(points_dd)
        utm_zone = int((center_lon + 180) / 6) + 1
        crs_utm = CRS.from_proj4(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs")
        transformer = Transformer.from_crs("EPSG:4326", crs_utm, always_xy=True)

        # Project points and build polygon
        projected = [transformer.transform(lon, lat) for lat, lon in points_dd]
        polygon = Polygon(projected)
        area_m2 = abs(polygon.area)

        # Unit conversions
        area_km2 = area_m2 / 1e6
        area_feddan = area_m2 / 4200
        area_qirat = area_m2 / 175

        # Display areas
        st.subheader("Results")
        st.markdown(f"- **Area (m²):** {area_m2:,.2f}")
        st.markdown(f"- **Area (km²):** {area_km2:,.6f}")
        st.markdown(f"- **المساحة (فدان):** {area_feddan:,.4f}")
        st.markdown(f"- **المساحة (قيراط):** {area_qirat:,.2f}")

        # Plot detailed diagram
        fig, ax = plt.subplots(figsize=(6, 6))
        x, y = polygon.exterior.xy
        ax.plot(x, y, '-', linewidth=2, marker='o', markersize=8, color='royalblue')

        # Annotate points with label and coords
        for idx, (px, py) in enumerate(projected):
            # Label
            ax.text(px, py, f"P{idx+1}", fontsize=10, fontweight='bold', color='navy',
                    ha='center', va='bottom', backgroundcolor='white')
            # Coordinates
            lat, lon = points_dd[idx]
            coord_text = f"({lat:.5f}, {lon:.5f})"
            ax.text(px, py, coord_text, fontsize=8, color='dimgray', ha='center', va='top')

        # Annotate all segment distances, including last to first
        num_pts = len(projected)
        for idx in range(num_pts):
            x1, y1 = projected[idx]
            x2, y2 = projected[(idx+1) % num_pts]
            # midpoint
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            ax.text(mx, my, f"{dist:.2f} m", fontsize=8, color='green',
                    ha='center', va='center', backgroundcolor='white')

        ax.set_aspect('equal', 'box')
        ax.set_title('Parcel Outline with Details', fontsize=14)
        ax.axis('off')
        st.pyplot(fig)

    except Exception as err:
        st.error(f"Error: {err}")
