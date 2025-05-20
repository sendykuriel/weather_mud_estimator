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

