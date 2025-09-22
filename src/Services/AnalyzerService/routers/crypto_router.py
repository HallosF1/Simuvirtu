from fastapi import APIRouter
from fastapi import Depends
from services.crypto_service import CryptoService
from auth.auth import verify_token

router = APIRouter(prefix="/analysis", tags=["Analysis"])
crypto_service = CryptoService()

@router.api_route("/{symbol}", methods=["GET","POST"])
def get_analysis_result(symbol: str, timeframe: str, limit: int, user=Depends(verify_token)):
    return crypto_service.signal_for_symbol(symbol, timeframe, limit)