from fastapi import APIRouter
from services.crypto_service import CryptoService

router = APIRouter(prefix="/analysis", tags=["Analysis"])
crypto_service = CryptoService()

@router.post("/{symbol}")
def get_analysis_result(symbol: str, timeframe: str, limit: int):
    return crypto_service.signal_for_symbol(symbol, timeframe, limit)