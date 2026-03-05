from pydantic import BaseModel, Field

class PredictInput(BaseModel):
    city: str = Field(..., example="Seoul")
    datetime: str = Field(..., example="2012-12-19 17:00:00")
    season: int = Field(..., example=4)
    holiday: int = Field(..., example=0)
    workingday: int = Field(..., example=1)
    weather: int = Field(..., example=1)
    temp: float = Field(..., example=10.66)
    atemp: float = Field(..., example=11.365)
    humidity: float = Field(..., example=56.0)
    windspeed: float = Field(..., example=26.0027)

class PredictOutput(BaseModel):
    predicted_count: float

class WeatherInput(BaseModel):
    city: str
    date: str
    hour: int