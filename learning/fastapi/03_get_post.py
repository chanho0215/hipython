from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# GET : 루트
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI!"}

# GET : 데이터 조회
@app.get("/hello")
def say_hello():
    return {"message": "안녕하세요"}


# POST : 데이터 전송
@app.post("/echo")
def echo(data: dict):
    return {"dict": data}
  
@app.get("/test1")
def root1():
  return {"name":"둘리사우르스"}

@app.get("/test2")
def root2():
  return["둘리","또치","도우너"]

#문자열도 된다
@app.get("/test3")
def root3():
  return "<h1>안녕?</h1>"

#숫자도 된다
@app.get("/test4")
def root4():
  return 2000


#경로 매개변수, 핸들러
#@app.get("/items/{item_id}")
#def read_item(item_id: int):
#  item_id = item_id*2
  
#  print(f'{item_id}를 받았습니다')
  
#  return {"ID":item_id}

# 쿼리 매개변수 > ? 뒤에 온다
# http://127.0.0.1:8080/items/3?discount=true
@app.get("/items/{item_id}")
def get_item(item_id: int, discount:bool ):
  item_msg = f"{discount} 할인여부"
  return item_msg

# http://127.0.0.1:8080/items/3/orders/2
@app.get("/items/{item_id}/orders/{order_id}")
def get_item_orders(item_id:int, order_id:int):
  print("get_item_orders")
  return {"item_id":item_id, "order_id":order_id}

# /stocks/005930/history?days=60&market=kospi
# @app.get("/stocks/{ticker}/history")
# def get_stock_info(
#     ticker: str, days: int, market: str):
#     return {
#         "ticker": ticker,
#         "market": market,
#         "days": days,
#         "message": "구현 예정입니다."
#     }
    

class StockRequest(BaseModel):
    days: int
    market: str

@app.post("/stocks/{ticker}/history")
def get_stock_info(
    ticker: str,
    data: StockRequest
):
    return {
        "ticker": ticker,
        "market": data.market,
        "days": data.days,
        "message": "구현 예정입니다."
    }

class News(BaseModel):
  title: str
  content: str
  views: int = 0

@app.post("/news")
def get_news(data: News):
  return {"news":data.title, "view": f"{data.views}회 조회되었습니다"}

