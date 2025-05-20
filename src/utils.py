import pandas as pd
import requests


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
    Return a copy of daily_df with a column indicating road status.

    Returns:
        pd.DataFrame with added column 'road_status' = 'Seco' / 'Barro'
    """
    df = daily_df.copy()
    df["date_day"] = pd.to_datetime(df["date_day"])

    # Criterio de 'Barro': lluvia > 5 mm o humedad > 90%
    df["barro_flag"] = (df["rain"] > 5) | (df["relative_humidity_2m"] > 90)

    # Rolling ventana de 2 días para ver si el día actual o anterior fue problemático
    df["barro_rolling"] = df["barro_flag"].rolling(window=2, min_periods=1).max()

    df["road_status"] = df["barro_rolling"].apply(lambda x: "Barro" if x else "Seco")
    return df


import calendar

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
                    color = "green" if status == "Seco" else "red" if status == "Barro" else "lightgray"
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
from datetime import date

import pandas as pd
from pandas import Timestamp


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