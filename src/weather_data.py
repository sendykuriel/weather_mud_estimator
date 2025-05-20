from datetime import datetime, timedelta

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry


def get_weather_data(lat: float, lon: float, timezone: str = "America/Sao_Paulo", past_days: int = 30):
    """
    Fetch weather forecast from Open-Meteo API for a given location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        timezone (str): Timezone string.
        past_days (int): Number of past days to include.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (hourly_df, daily_df)
    """
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "relative_humidity_2m"
        ],
        "current": "rain",
        "timezone": timezone,
        "past_days": past_days
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    time_index = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )

    hourly_df = pd.DataFrame({
        "date": time_index,
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "precipitation_probability": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation": hourly.Variables(2).ValuesAsNumpy(),
        "rain": hourly.Variables(3).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(4).ValuesAsNumpy()
    })

    # Daily summary
    hourly_df["date_day"] = hourly_df["date"].dt.date
    daily_df = hourly_df.groupby("date_day").agg({
        "temperature_2m": "mean",
        "relative_humidity_2m": "mean",
        "precipitation_probability": "mean",
        "precipitation": "sum",
        "rain": "sum"
    }).reset_index()

    return hourly_df, daily_df




def generate_hourly_rain_data(lat: float, lon: float) -> pd.DataFrame:
    """
    Generate synthetic rain data every 2 hours for the last 20 hours at a single location.

    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location

    Returns:
        pd.DataFrame: DataFrame with columns ['date', 'lat', 'lon', 'rain']
    """
    timestamps = [datetime.utcnow() - timedelta(hours=2 * i) for i in range(9, -1, -1)]

    data = {
        "date": timestamps,
        "lat": [lat] * len(timestamps),
        "lon": [lon] * len(timestamps),
        "rain": np.random.exponential(2.5, size=len(timestamps))  # or 0s if dry
    }

    return pd.DataFrame(data)

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_hourly_rain_data_cloud(lat: float, lon: float, n_points=30) -> pd.DataFrame:
    """
    Generate synthetic rain data with multiple spatial points per timestamp.
    
    Args:
        lat (float): center latitude
        lon (float): center longitude
        n_points (int): number of points per timestamp
    
    Returns:
        pd.DataFrame with columns: date, lat, lon, rain
    """
    timestamps = [datetime.utcnow() - timedelta(hours=2 * i) for i in range(60, -1, -1)]

    data = []

    for t in timestamps:
        for _ in range(n_points):
            lat_ = lat + np.random.uniform(-0.5, 0.5)
            lon_ = lon + np.random.uniform(-0.5, 0.5)
            rain = np.clip(np.random.normal(4, 2), 0, 10)  # bounded normal
            data.append({"date": t, "lat": lat_, "lon": lon_, "rain": rain})
    return pd.DataFrame(data)
