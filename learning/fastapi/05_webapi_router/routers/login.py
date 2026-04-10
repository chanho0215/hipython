from pathlib import Path

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/auth", tags=["auth"])

LOGIN_HTML_PATH = Path(__file__).resolve().parent.parent / "login.html"

USERS = {
    "admin": "1234",
    "student": "abcd",
}


@router.get("/login")
def login_page():
    return FileResponse(LOGIN_HTML_PATH)


@router.post("/login")
def login(username: str = Form(), password: str = Form()):
    if username not in USERS:
        raise HTTPException(status_code=401, detail="User does not exist.")
    if USERS[username] != password:
        raise HTTPException(status_code=401, detail="Incorrect password.")
    return {"message": f"{username} login success"}
