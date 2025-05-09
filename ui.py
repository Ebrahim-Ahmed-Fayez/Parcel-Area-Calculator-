import streamlit as st
from pyproj import CRS, Transformer
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Parcel Area Calculator", layout="centered")
st.title("Parcel Area Calculator 📐")
st.markdown("Enter the coordinates of four corner points as comma-separated DMS (deg,min,sec) and select the hemisphere.")

# Convert DMS string to decimal degrees
def dms_to_decimal(dms_str, sign):
    deg, mins, secs = [float(x.strip()) for x in dms_str.split(',')]
    dd = deg + mins/60 + secs/3600
    return -dd if sign in ['W', 'S'] else dd

# Collect user inputs
points_dd = []  # list of (lat, lon)
for i in range(1, 5):
    st.subheader(f"Point #{i}")
    lon_dms = st.text_input(f"Longitude DMS (deg,min,sec) P{i}", placeholder="e.g. 28,13,30.28", key=f"lon_dms_{i}")
    lon_dir = st.selectbox(f"Hemisphere P{i}", options=["E", "W"], key=f"lon_dir_{i}")
    lat_dms = st.text_input(f"Latitude DMS (deg,min,sec) P{i}", placeholder="e.g. 26,57,42.46", key=f"lat_dms_{i}")
    lat_dir = st.selectbox(f"Hemisphere P{i}", options=["N", "S"], key=f"lat_dir_{i}")

    if lon_dms and lat_dms:
        lon_dd = dms_to_decimal(lon_dms, lon_dir)
        lat_dd = dms_to_decimal(lat_dms, lat_dir)
        points_dd.append((lat_dd, lon_dd))

if st.button("Calculate Area"):
    try:
        # Project to UTM
        center_lon = sum(lon for lat, lon in points_dd) / len(points_dd)
        utm_zone = int((center_lon + 180) / 6) + 1
        utm_crs = CRS.from_proj4(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs")
        transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)

        # Build polygon and compute area
        projected = [transformer.transform(lon, lat) for lat, lon in points_dd]
        polygon = Polygon(projected)
        area_m2 = abs(polygon.area)

        # Convert units
        area_km2 = area_m2 / 1e6
        area_feddan = area_m2 / 4200
        area_qirat = area_m2 / 175

        # Display results
        st.subheader("Results")
        st.markdown(f"- **Area (m²):** {area_m2:,.2f}")
        st.markdown(f"- **Area (km²):** {area_km2:,.6f}")
        st.markdown(f"- **Area (feddan):** {area_feddan:,.4f}")
        st.markdown(f"- **Area (qirat):** {area_qirat:,.2f}")

        # Generate KML for Google Earth
        coords_str = "".join([f"{lon},{lat},0\n" for lat, lon in points_dd] + [f"{points_dd[0][1]},{points_dd[0][0]},0\n"])
        kml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\">
  <Placemark>
    <name>Parcel Outline</name>
    <Style>
      <LineStyle><color>ff0000ff</color><width>2</width></LineStyle>
      <PolyStyle><fill>0</fill></PolyStyle>
    </Style>
    <Polygon>
      <outerBoundaryIs>
        <LinearRing>
          <coordinates>
{coords_str}          </coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>
  </Placemark>
</kml>"""
        b = io.BytesIO(kml.encode('utf-8'))
        st.download_button("Download KML for Google Earth", data=b, file_name="parcel.kml", mime="application/vnd.google-earth.kml+xml")

        # Plot detailed diagram
        fig, ax = plt.subplots(figsize=(6, 6))
        x, y = polygon.exterior.xy
        ax.plot(x, y, '-', linewidth=2, marker='o', markersize=8, color='royalblue')
        for idx, (px, py) in enumerate(projected):
            ax.text(px, py, f"P{idx+1}", fontsize=10, fontweight='bold', ha='center', va='bottom', backgroundcolor='white')
            lat, lon = points_dd[idx]
            ax.text(px, py, f"({lat:.5f}, {lon:.5f})", fontsize=8, ha='center', va='top', backgroundcolor='white')
        n = len(projected)
        for idx in range(n):
            x1, y1 = projected[idx]
            x2, y2 = projected[(idx+1) % n]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            ax.text(mx, my, f"{dist:.2f} m", fontsize=8, ha='center', va='center', backgroundcolor='white', color='green')
        ax.set_aspect('equal', 'box')
        ax.set_title('Parcel Outline with Details', fontsize=14)
        ax.axis('off')
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: {e}")
