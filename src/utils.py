import calendar
from datetime import date

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from pandas import Timestamp


def is_road_dry(daily_df: pd.DataFrame) -> bool:
    """
    Determine if the dirt road is dry enough to pass.

    Returns:
        bool: True if the road is dry, False if it's muddy
    """
    last_days = daily_df.sort_values("date_day").tail(2)
    rain_ok = (last_days["rain"] <= 5).all()
    humidity_ok = (last_days["relative_humidity_2m"] <= 90).all()
    return rain_ok and humidity_ok


def road_status_per_day(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Marks days as 'Mud' if there was recent rain, and extends muddy status
    if humidity remains high for the following days.

    Rules:
    - If rain > 5mm → the road becomes muddy.
    - After rain, the road stays muddy:
        - for at least 2 days, OR
        - as long as humidity stays above 90%.
    - Once it's been dry for 2+ days and humidity drops, the road becomes 'Dry' again.
    """
    df = daily_df.copy()
    df["date_day"] = pd.to_datetime(df["date_day"])
    df["road_status"] = "Dry"

    df["heavy_rain"] = df["rain"] > 5
    df["high_humidity"] = df["relative_humidity_2m"] > 90

    is_muddy = False
    days_since_rain = 99  # arbitrarily large to start

    for i in range(len(df)):
        if df.loc[i, "heavy_rain"]:
            is_muddy = True
            days_since_rain = 0
            df.loc[i, "road_status"] = "Mud"
        elif is_muddy:
            days_since_rain += 1
            if days_since_rain < 2 or df.loc[i, "high_humidity"]:
                df.loc[i, "road_status"] = "Mud"
            else:
                is_muddy = False
                df.loc[i, "road_status"] = "Dry"
        else:
            df.loc[i, "road_status"] = "Dry"

    return df



def plot_road_status_calendar_multi(status_df: pd.DataFrame):
    """
    Plot a calendar heatmap per month showing road status (Seco/Barro).

    Args:
        status_df (pd.DataFrame): DataFrame with 'date_day' and 'road_status'
    Returns:
        matplotlib.figure.Figure
    """
    status_df = status_df.copy()
    status_df["date_day"] = pd.to_datetime(status_df["date_day"])
    status_df["day"] = status_df["date_day"].dt.day
    status_df["month"] = status_df["date_day"].dt.month
    status_df["year"] = status_df["date_day"].dt.year

    unique_months = status_df[["year", "month"]].drop_duplicates().sort_values(["year", "month"])

    n_months = len(unique_months)
    ncols = min(3, n_months)
    nrows = (n_months + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(ncols * 5, nrows * 4))
    if n_months == 1:
        axes = np.array([[axes]])

    axes = axes.reshape((nrows, ncols))

    for idx, (i, row) in enumerate(unique_months.iterrows()):
        y, m = row["year"], row["month"]
        ax = axes[idx // ncols, idx % ncols]

        df_month = status_df[(status_df["year"] == y) & (status_df["month"] == m)]
        first_weekday, month_days = calendar.monthrange(y, m)
        grid = np.full((6, 7), "", dtype=object)
        status_dict = {}

        for _, r in df_month.iterrows():
            d = r["day"]
            weekday = (r["date_day"].weekday())
            week = (d + first_weekday - 1) // 7
            grid[week, weekday] = str(d)
            status_dict[str(d)] = r["road_status"]

        ax.set_xticks(np.arange(7))
        ax.set_yticks(np.arange(6))
        ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        ax.set_yticklabels([])
        ax.tick_params(top=False, bottom=False, left=False, right=False)
        ax.grid(False)

        for i in range(6):
            for j in range(7):
                day = grid[i, j]
                if day != "":
                    status = status_dict.get(day, "Desconocido")
                    color = {"Dry": "green", "Mud": "red"}.get(status, "lightgray")
                    rect = mpatches.Rectangle((j, i), 1, 1, facecolor=color, edgecolor="white")
                    ax.add_patch(rect)
                    ax.text(j + 0.5, i + 0.5, day, ha="center", va="center", color="white", fontsize=12)

        ax.set_xlim(0, 7)
        ax.set_ylim(6, 0)
        ax.set_title(f"{calendar.month_name[m]} {y}", fontsize=14)

    # Ocultar ejes vacíos si sobran
    for idx in range(n_months, nrows * ncols):
        ax = axes[idx // ncols, idx % ncols]
        ax.axis("off")

    plt.tight_layout()
    return fig



def estimate_next_dry_day(daily_df: pd.DataFrame) -> pd.Timestamp | None:
    """
    Recorre el dataframe y devuelve el primer día (a partir de hoy)
    en el que se espera que el camino esté seco.
    """
    today = pd.Timestamp.utcnow().date()

    for _, row in daily_df.iterrows():
        # Convertir row["date_day"] a date si es necesario
        if isinstance(row["date_day"], pd.Timestamp):
            row_date = row["date_day"].date()
        else:
            row_date = row["date_day"]

        # Comparar como datetime.date
        if row_date >= today:
            if row["rain"] <= 5 and row["relative_humidity_2m"] <= 90:
                return pd.to_datetime(row_date)

    return None






def get_road_surface(lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    way(around:15,{lat},{lon})[highway][surface];
    out tags;
    """
    response = requests.post(overpass_url, data={"data": query})
    data = response.json()

    if data["elements"]:
        surface = data["elements"][0]["tags"].get("surface", "unknown")
        return surface
    return "no road found"