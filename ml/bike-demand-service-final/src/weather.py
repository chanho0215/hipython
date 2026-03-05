import requests
import pandas as pd

def geocode(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if "results" not in data or not data["results"]:
        raise ValueError("도시를 찾을 수 없습니다.")
    item = data["results"][0]
    return item["latitude"], item["longitude"], item["name"]

def fetch_weather(city: str, date: str, hour: int):
    lat, lon, resolved = geocode(city)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
        "start_date": date,
        "end_date": date,
        "timezone": "auto"
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if r.status_code != 200 or "hourly" not in data:
        reason = data.get("reason", "hourly 데이터가 없습니다.")
        raise ValueError(f"날씨 API 오류: {reason}")

    hourly = pd.DataFrame({
        "time": data["hourly"]["time"],
        "temp": data["hourly"]["temperature_2m"],
        "humidity": data["hourly"]["relative_humidity_2m"],
        "atemp": data["hourly"]["apparent_temperature"],
        "windspeed": data["hourly"]["wind_speed_10m"]
    })
    hourly["time"] = pd.to_datetime(hourly["time"])

    target = pd.to_datetime(f"{date} {hour:02d}:00:00")
    row = hourly.iloc[(hourly["time"] - target).abs().argsort()[:1]].iloc[0]

    return {
        "city": resolved,
        "time": str(row["time"]),
        "temp": float(row["temp"]),
        "humidity": float(row["humidity"]),
        "atemp": float(row["atemp"]),
        "windspeed": float(row["windspeed"]),
    }