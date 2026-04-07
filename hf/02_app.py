from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI!"}

@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# 터미널에서 실행
# uvicorn 02_app:app --reload --host 127.0.0.1 --port 8080
# 브라우저, 포스트맨에서
# http://localhost:8080/
