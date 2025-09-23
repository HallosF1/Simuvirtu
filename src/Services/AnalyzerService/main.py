from fastapi import FastAPI
from routers.crypto_router import router as crypto_router
from routers.signal_router import router as signal_router
from services.signals_service import SignalsService
from contextlib import asynccontextmanager

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await SignalsService.shutdown()

app.include_router(crypto_router)
app.include_router(signal_router)