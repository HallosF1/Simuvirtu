from fastapi import FastAPI
from routers.crypto_router import router

app = FastAPI()

app.include_router(router)