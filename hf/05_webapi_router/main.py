from fastapi import FastAPI
from routers.items import router as items_router
from routers.login import router as login_router
from routers.file_upload import router as file_upload_router

app = FastAPI()
app.include_router(items_router)
app.include_router(login_router)
app.include_router(file_upload_router)