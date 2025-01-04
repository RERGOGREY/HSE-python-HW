import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime


def get_season(month, latitude):
    if latitude > 0:
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    else:  
        if month in [12, 1, 2]:
            return "summer"
        elif month in [3, 4, 5]:
            return "autumn"
        elif month in [6, 7, 8]:
            return "winter"
        else:
            return "spring"

def fetch_current_weather(city, api_key):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        latitude = data["coord"]["lat"]
        month = datetime.now().month
        season = get_season(month, latitude)
        temp = data["main"]["temp"]
        return temp, season
    except requests.exceptions.RequestException as e:
        return None, None

st.title("Анализ погоды и аномалий")

uploaded_file = st.file_uploader("Загрузите файл с историческими данными (CSV)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Загруженные данные:")
    st.write(df.head())

    city = st.selectbox("Выберите город", df["city"].unique())

    city_data = df[df["city"] == city]

    st.subheader(f"Описательная статистика для города {city}")
    st.write(city_data.describe())

    st.subheader("Временной ряд температур с выделением аномалий")
    mean_temp = city_data["temperature"].mean()
    std_temp = city_data["temperature"].std()
    city_data["is_anomaly"] = ~city_data["temperature"].between(mean_temp - 2 * std_temp, mean_temp + 2 * std_temp)
    fig = px.scatter(city_data, x="timestamp", y="temperature", color="is_anomaly", title="Температурные аномалии")
    st.plotly_chart(fig)

    st.subheader("Сезонные профили")
    if "latitude" not in city_data.columns:
        city_data["latitude"] = 0

    city_data["season"] = city_data["timestamp"].apply(
        lambda x: get_season(datetime.strptime(x, "%Y-%m-%d").month, city_data["latitude"].iloc[0])
    )
    season_stats = city_data.groupby("season")["temperature"].agg(["mean", "std"]).reset_index()
    st.write(season_stats)

    fig_season = px.bar(season_stats, x="season", y="mean", error_y="std", title="Средняя температура по сезонам")
    st.plotly_chart(fig_season)

st.subheader("Текущая температура")
api_key = st.text_input("Введите API-ключ OpenWeatherMap")

if api_key:
    if city:
        temp, season = fetch_current_weather(city, api_key)
        if temp is None:
            st.error("Ошибка: Неверный API-ключ. Убедитесь, что вы указали правильный ключ.")
        else:
            st.write(f"Текущая температура в {city}: {temp}°C")
            st.write(f"Сезон: {season}")
            
            if season in season_stats["season"].values:
                seasonal_mean = season_stats.loc[season_stats["season"] == season, "mean"].values[0]
                seasonal_std = season_stats.loc[season_stats["season"] == season, "std"].values[0]

                st.write(f"Средняя температура для сезона {season}: {seasonal_mean}°C")
                st.write(f"Стандартное отклонение для сезона {season}: {seasonal_std}°C")
                st.write(f"Границы: {seasonal_mean - 2 * seasonal_std}°C до {seasonal_mean + 2 * seasonal_std}°C")

                lower_bound = seasonal_mean - 2 * seasonal_std
                upper_bound = seasonal_mean + 2 * seasonal_std
                is_anomaly = not (lower_bound <= temp <= upper_bound)
                status = "Аномальная" if is_anomaly else "Нормальная"
                st.write(f"Текущая температура: {status}")
            else:
                st.warning("Нет исторических данных для текущего сезона.")
    else:
        st.warning("Выберите город для анализа.")
else:
    st.warning("Введите API-ключ, чтобы увидеть текущую температуру.")



