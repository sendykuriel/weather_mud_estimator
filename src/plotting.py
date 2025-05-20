import glob
import os
from datetime import datetime, timedelta

import contextily as cx
import geopandas as gpd
import imageio
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from shapely.geometry import Point


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

import glob
import os

import contextily as cx
import geopandas as gpd
import imageio
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point


def create_rain_gif_with_map(hourly_df: pd.DataFrame, output_path="rain_frames/rain.gif") -> str:
    """
    Create a rain animation over a real map using contextily + geopandas.

    Args:
        hourly_df: DataFrame with ['date', 'lat', 'lon', 'rain']
        output_path: where to save the gif

    Returns:
        path to gif
    """
    os.makedirs("rain_frames", exist_ok=True)
    hourly_df["date"] = pd.to_datetime(hourly_df["date"])
    frames = []

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(
        hourly_df,
        geometry=gpd.points_from_xy(hourly_df["lon"], hourly_df["lat"]),
        crs="EPSG:4326"
    ).to_crs(epsg=3857)  # Web Mercator for tile overlays

    for timestamp, group in gdf.groupby("date"):
        fig, ax = plt.subplots(figsize=(7, 7))

        group.plot(
            ax=ax,
            column="rain",
            cmap="Blues",
            markersize=group["rain"] * 20,
            legend=True,
            vmin=0,
            vmax=10
        )

        cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik)
        ax.set_title(f"Rain at {timestamp.strftime('%Y-%m-%d %H:%M')}")
        ax.axis("off")

        frame_path = f"rain_frames/frame_{timestamp.strftime('%Y%m%d_%H%M')}.png"
        plt.savefig(frame_path, bbox_inches="tight")
        frames.append(imageio.v2.imread(frame_path))
        plt.close()

    imageio.mimsave(output_path, frames, duration=0.6)

    for f in glob.glob("rain_frames/*.png"):
        os.remove(f)

    return output_path




def create_rain_gif_cloud_style(hourly_df: pd.DataFrame, output_path="rain_frames/rain_cloud.gif", hours_back=72) -> str:
    """
    Create a radar-style animated GIF of interpolated rain clouds over OpenStreetMap.
    
    Args:
        hourly_df: must include ['date', 'lat', 'lon', 'rain']
        output_path: path for saving the final .gif
        hours_back: how many hours into the past to include (default 72h = 3 days)
    
    Returns:
        str: Path to the saved gif file
    """
    os.makedirs("rain_frames", exist_ok=True)

    # Normalize time and filter
    hourly_df["date"] = pd.to_datetime(hourly_df["date"])
    hourly_df["rounded_time"] = hourly_df["date"].dt.floor("2h")
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)
    hourly_df = hourly_df[hourly_df["rounded_time"] >= cutoff]
    hourly_df.to_clipboard()

    # GeoDataFrame conversion
    gdf = gpd.GeoDataFrame(
        hourly_df,
        geometry=gpd.points_from_xy(hourly_df["lon"], hourly_df["lat"]),
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    frames = []
    x_all = gdf.geometry.x
    y_all = gdf.geometry.y
    buffer = 20000

    global_xmin = x_all.min() - buffer
    global_xmax = x_all.max() + buffer
    global_ymin = y_all.min() - buffer
    global_ymax = y_all.max() + buffer

    grid_x, grid_y = np.mgrid[
        global_xmin:global_xmax:200j,
        global_ymin:global_ymax:200j
    ]

    for timestamp, group in gdf.groupby("rounded_time"):
        if len(group) < 4:
            continue

        fig, ax = plt.subplots(figsize=(7, 7))

        x = group.geometry.x.values
        y = group.geometry.y.values
        z = group["rain"].values
        z = np.clip(z, 0.1, 10)  # ensure visible cloud

        grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic', fill_value=0)

        im = ax.imshow(
            grid_z.T,
            extent=(global_xmin, global_xmax, global_ymin, global_ymax),
            origin='lower',
            cmap='Blues',
            alpha=0.7,
            vmin=0,
            vmax=10
        )

        cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik)
        ax.set_xlim(global_xmin, global_xmax)
        ax.set_ylim(global_ymin, global_ymax)
        ax.set_title(f"Rain at {timestamp.strftime('%Y-%m-%d %H:%M')}")
        ax.axis("off")

        frame_path = f"rain_frames/frame_{timestamp.strftime('%Y%m%d_%H%M')}.png"
        plt.savefig(frame_path)
        plt.close()

        try:
            frame = imageio.v2.imread(frame_path)
            frames.append(frame)
        except Exception as e:
            print(f"⚠️ Error reading {frame_path}: {e}")

    if len(frames) == 0:
        raise ValueError("❌ No valid frames generated.")

    first_shape = frames[0].shape
    if not all(f.shape == first_shape for f in frames):
        raise ValueError("❌ Frame size mismatch. Cannot save GIF.")

    imageio.mimsave(output_path, frames, duration=1.0)

    for f in glob.glob("rain_frames/*.png"):
        os.remove(f)

    return output_path
