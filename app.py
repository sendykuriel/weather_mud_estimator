import pandas as pd
import streamlit as st
from src.plotting import plot_daily_summary, plot_weather_custom
from src.utils import (estimate_next_dry_day, is_road_dry,
                       plot_road_status_calendar_multi, road_status_per_day)
from src.weather_data import get_weather_data

st.title("Weather Forecast Dashboard")

# 📍 Diccionario de ubicaciones predefinidas
locations = {
    "Uri Land": {"lat": -35.081202, "lon": -59.033928},
    "Zapiola": {"lat": -35.06099547526981, "lon": -59.04251008235054},
    "Areco": {"lat": -34.256575, "lon": -59.487683},
}

selected_location = st.selectbox("Choose a location:", list(locations.keys()))
default_lat = locations[selected_location]["lat"]
default_lon = locations[selected_location]["lon"]

lat = st.number_input("Latitude", value=default_lat, format="%.6f")
lon = st.number_input("Longitude", value=default_lon, format="%.6f")
days = st.slider("Days of past data", 1, 90, 30)

if st.button("Get Weather"):
    hourly_df, daily_df = get_weather_data(lat, lon, past_days=days)

    if is_road_dry(daily_df):
        st.success("✅ El camino de tierra está seco. Podés pasar.")
    else:
        st.error("🚫 El camino de tierra está embarrado. Mejor evitarlo.")
        
        next_dry_day = estimate_next_dry_day(daily_df)
        
    if next_dry_day:
        formatted_date = next_dry_day.strftime("%A %d %B").capitalize()
        st.info(f"🟡 Se estima que estará transitable a partir de **{formatted_date}**.")
    else:
        st.warning("🔮 No se puede estimar aún una fecha clara de recuperación.")


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


st.text("Created by uri zen")
github_url = "https://github.com/sendykuriel"
st.write("Check out my GitHub (%s)" % github_url)
st.text("Data provided by Open-Meteo.com")
