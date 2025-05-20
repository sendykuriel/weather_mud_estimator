from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def plot_weather_custom(df: pd.DataFrame):
    """
    Plot temperature, humidity and rain with 3 Y-axes and shaded background for forecast vs history.

    Args:
        df (pd.DataFrame): Hourly dataframe with 'date', 'temperature_2m', 'relative_humidity_2m', 'rain'
    """
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax2 = ax1.twinx()
    ax3 = ax1.twinx()

    # Offset third Y-axis to the right
    ax3.spines["right"].set_position(("axes", 1.1))

    # Plot each variable
    ax1.plot(df["date"], df["temperature_2m"], label="Temperature (°C)", color="tab:red")
    ax2.plot(df["date"], df["relative_humidity_2m"], label="Humidity (%)", color="tab:blue")
    ax3.plot(df["date"], df["rain"], label="Rain (mm)", color="tab:green")

    # Labels
    ax1.set_ylabel("Temperature (°C)", color="tab:red")
    ax2.set_ylabel("Humidity (%)", color="tab:blue")
    ax3.set_ylabel("Rain (mm)", color="tab:green")

    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax3.tick_params(axis="y", labelcolor="tab:green")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate()

    # 🎯 Shade background
    now = pd.Timestamp.utcnow()
    ax1.axvspan(df["date"].min(), now, facecolor="lightgray", alpha=0.3, label="Past")
    ax1.axvspan(now, df["date"].max(), facecolor="white", alpha=0.1, label="Forecast")

    # Legend
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.92))

    plt.title("Weather Forecast: Temperature, Humidity, Rain")
    plt.tight_layout()
    return fig
def plot_daily_summary(daily_df: pd.DataFrame):
    """
    Plot daily temperature, humidity and rain with multi Y axes, shading past days and marking heavy rain.

    Args:
        daily_df (pd.DataFrame): Aggregated daily weather data

    Returns:
        matplotlib.figure.Figure
    """
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax2 = ax1.twinx()
    ax3 = ax1.twinx()
    ax3.spines["right"].set_position(("axes", 1.1))

    dates = pd.to_datetime(daily_df["date_day"])

    ax1.plot(dates, daily_df["temperature_2m"], label="Temperature (°C)", color="tab:red", marker="o")
    ax2.plot(dates, daily_df["relative_humidity_2m"], label="Humidity (%)", color="tab:blue", marker="o")
    ax3.plot(dates, daily_df["rain"], label="Rain (mm)", color="tab:green", marker="o")

    ax1.set_ylabel("Temperature (°C)", color="tab:red")
    ax2.set_ylabel("Humidity (%)", color="tab:blue")
    ax3.set_ylabel("Rain (mm)", color="tab:green")

    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax3.tick_params(axis="y", labelcolor="tab:green")

    now = pd.Timestamp.utcnow().normalize()

    # ✅ Fondo gris hasta el día de hoy
    ax1.axvspan(dates.min(), now, facecolor="lightgray", alpha=0.3)

    # ✅ Línea vertical punteada en días con lluvia fuerte (> 10 mm)
    for i, rain in enumerate(daily_df["rain"]):
        if rain >= 10:
            ax1.axvline(dates[i], color="purple", linestyle="--", linewidth=1)

    ax1.set_title("Daily Summary")
    fig.autofmt_xdate()
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.92))
    plt.tight_layout()
    return fig
