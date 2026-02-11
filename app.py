import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ---------------------------------------
# Page Configuration
# ---------------------------------------
st.set_page_config(page_title="Weather Intelligence Dashboard", layout="wide")

st.title("🌍 Weather Intelligence Dashboard")

# ---------------------------------------
# Sidebar Controls
# ---------------------------------------
st.sidebar.header("⚙️ Controls")

location = st.sidebar.text_input("Enter City Name", "Hyderabad")

today = datetime.now()
default_start = today - timedelta(days=7)

date_range = st.sidebar.date_input(
    "Select Historical Date Range",
    [default_start.date(), today.date()]
)

# ---------------------------------------
# Get Coordinates
# ---------------------------------------
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    response = requests.get(url)
    data = response.json()

    if "results" in data:
        return data["results"][0]["latitude"], data["results"][0]["longitude"]
    return None, None


# ---------------------------------------
# Get Historical Data
# ---------------------------------------
def get_historical_weather(lat, lon, start_date, end_date):

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"precipitation_sum,wind_speed_10m_max"
        f"&timezone=auto"
    )

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame({
        "Date": pd.to_datetime(data["daily"]["time"]),
        "Max Temp (°C)": data["daily"]["temperature_2m_max"],
        "Min Temp (°C)": data["daily"]["temperature_2m_min"],
        "Rainfall (mm)": data["daily"]["precipitation_sum"],
        "Max Wind Speed (km/h)": data["daily"]["wind_speed_10m_max"]
    })

    df["Average Temp (°C)"] = (
        df["Max Temp (°C)"] + df["Min Temp (°C)"]
    ) / 2

    df["Moving Avg (3 Days)"] = (
        df["Average Temp (°C)"].rolling(window=3).mean()
    )

    return df


# ---------------------------------------
# Get Forecast Data
# ---------------------------------------
def get_forecast(lat, lon):

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"precipitation_sum,wind_speed_10m_max"
        f"&timezone=auto"
    )

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame({
        "Date": pd.to_datetime(data["daily"]["time"]),
        "Max Temp (°C)": data["daily"]["temperature_2m_max"],
        "Min Temp (°C)": data["daily"]["temperature_2m_min"],
        "Rainfall (mm)": data["daily"]["precipitation_sum"],
        "Max Wind Speed (km/h)": data["daily"]["wind_speed_10m_max"]
    })

    df["Average Temp (°C)"] = (
        df["Max Temp (°C)"] + df["Min Temp (°C)"]
    ) / 2

    return df


# ---------------------------------------
# Main Logic
# ---------------------------------------
if location and len(date_range) == 2:

    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")

    lat, lon = get_coordinates(location)

    if lat is None:
        st.error("❌ Location not found. Try another city.")
    else:

        # ==============================
        # Historical Section
        # ==============================
        st.subheader(f"📊 Historical Weather - {location}")

        df_hist = get_historical_weather(lat, lon, start_date, end_date)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Avg Temp",
                    f"{df_hist['Average Temp (°C)'].mean():.1f} °C")
        col2.metric("Highest Temp",
                    f"{df_hist['Max Temp (°C)'].max():.1f} °C")
        col3.metric("Total Rainfall",
                    f"{df_hist['Rainfall (mm)'].sum():.1f} mm")
        col4.metric("Max Wind Speed",
                    f"{df_hist['Max Wind Speed (km/h)'].max():.1f} km/h")

        fig_hist = px.line(
            df_hist,
            x="Date",
            y=[
                "Max Temp (°C)",
                "Min Temp (°C)",
                "Average Temp (°C)",
                "Moving Avg (3 Days)"
            ],
            markers=True
        )

        st.plotly_chart(fig_hist, use_container_width=True)
        st.dataframe(df_hist)

        # ==============================
        # Forecast Section
        # ==============================
        st.subheader("🔮 Upcoming Forecast (Next 7–10 Days)")

        df_forecast = get_forecast(lat, lon)

        col5, col6 = st.columns(2)

        col5.metric("Forecast Avg Temp",
                    f"{df_forecast['Average Temp (°C)'].mean():.1f} °C")
        col6.metric("Forecast Total Rainfall",
                    f"{df_forecast['Rainfall (mm)'].sum():.1f} mm")

        fig_forecast = px.line(
            df_forecast,
            x="Date",
            y=[
                "Max Temp (°C)",
                "Min Temp (°C)",
                "Average Temp (°C)"
            ],
            markers=True
        )

        st.plotly_chart(fig_forecast, use_container_width=True)
        st.dataframe(df_forecast)

else:
    st.warning("Please select a valid date range.")
