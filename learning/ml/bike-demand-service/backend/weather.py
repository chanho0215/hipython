import requests
import pandas as pd

def get_coordinates(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    res = requests.get(url, params=params, timeout=10)
    data = res.json()

    if "results" not in data or not data["results"]:
        raise ValueError("도시를 찾을 수 없습니다.")

    result = data["results"][0]
    return result["latitude"], result["longitude"], result["name"]

def get_weather(city: str, date: str, hour: int):
    lat, lon, resolved_name = get_coordinates(city)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
        "start_date": date,
        "end_date": date,
        "timezone": "auto"
    }

    res = requests.get(url, params=params, timeout=10)
    data = res.json()

    # 에러 응답 체크
    if res.status_code != 200 or "hourly" not in data:
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
    target_time = pd.to_datetime(f"{date} {hour:02d}:00:00")

    row = hourly.iloc[(hourly["time"] - target_time).abs().argsort()[:1]]

    return {
        "city": resolved_name,
        "time": str(row["time"].values[0]),
        "temp": float(row["temp"].values[0]),
        "humidity": float(row["humidity"].values[0]),
        "atemp": float(row["atemp"].values[0]),
        "windspeed": float(row["windspeed"].values[0])
    }