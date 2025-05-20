import folium
import pandas as pd
import streamlit as st
from src.plotting import plot_daily_summary, plot_weather_custom
from src.utils import (estimate_next_dry_day, get_road_surface, is_road_dry,
                       plot_road_status_calendar_multi, road_status_per_day)
from src.weather_data import generate_hourly_rain_data_cloud, get_weather_data
from streamlit_folium import st_folium

# --- Init state ---
if "weather_fetched" not in st.session_state:
    st.session_state.weather_fetched = False

st.title("Weather Forecast Dashboard")

# 📍 Predefined locations
locations = {
    "Uri Land": {"lat": -35.081202, "lon": -59.033928},
    "Zapiola": {"lat": -35.06099547526981, "lon": -59.04251008235054},
    "Areco": {"lat": -34.256575, "lon": -59.487683},
    "Campana": {"lat": -34.17767498263812, "lon": -58.966297516567025},
}

selected_location = st.selectbox("Choose a location:", list(locations.keys()))
default_lat = locations[selected_location]["lat"]
default_lon = locations[selected_location]["lon"]

lat = st.number_input("Latitude", value=default_lat, format="%.6f")
lon = st.number_input("Longitude", value=default_lon, format="%.6f")
days = st.slider("Days of past data", 1, 90, 30)

# --- Button triggers data load ---
if st.button("Get Weather"):
    st.session_state.weather_fetched = True

# --- Main logic ---
if st.session_state.weather_fetched:
    hourly_df, daily_df = get_weather_data(lat, lon, past_days=days)
    road_surface = get_road_surface(lat, lon)
    next_dry_day = None
    
    from src.plotting import create_rain_gif_cloud_style

    if st.button("Generate Rain Cloud GIF"):
        gif_df = generate_hourly_rain_data_cloud(lat, lon)  # o tu dataframe real
        gif_path = create_rain_gif_cloud_style(gif_df, hours_back=72)
        st.image(gif_path, caption="Rain Radar Animation (last 3 days)")





    if is_road_dry(daily_df) and road_surface == "unpaved":
        st.success("✅ El camino de tierra está seco. Podés pasar.")
    elif road_surface != "unpaved":
        st.warning("⚠️ El camino no es de tierra. No se necesita estimación.")
        st.text(f"El Camino es de: {road_surface}")
    else:
        st.error("🚫 El camino de tierra está embarrado. Mejor evitarlo.")
        next_dry_day = estimate_next_dry_day(daily_df)

    if next_dry_day:
        formatted_date = next_dry_day.strftime("%A %d %B").capitalize()
        st.info(f"🟡 Se estima que estará transitable a partir de **{formatted_date}**.")

    st.subheader("Daily Summary")
    fig_daily = plot_daily_summary(daily_df)
    st.pyplot(fig_daily)

    st.subheader("Histórico del estado del camino")
    status_df = road_status_per_day(daily_df)
    fig_status = plot_road_status_calendar_multi(status_df)
    st.pyplot(fig_status)

    st.subheader("Hourly Data (Custom Plot)")
    fig = plot_weather_custom(hourly_df)
    st.pyplot(fig)

    st.subheader("Location Map")
    m = folium.Map(location=[lat, lon], zoom_start=14)
    folium.Marker([lat, lon], tooltip="Ubicación seleccionada").add_to(m)
    st_folium(m, width=700, height=500)
    


# --- Footer ---
st.text("Created by uri zen")
github_url = "https://github.com/sendykuriel"
st.write("Check out my GitHub (%s)" % github_url)
st.text("Data provided by Open-Meteo.com")
