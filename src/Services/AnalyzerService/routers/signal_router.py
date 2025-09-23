from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio, json
from services.signals_service import SignalsService
from auth.auth import verify_token

router = APIRouter(prefix="/signals", tags=["Analysis"])
svc = SignalsService()

@router.get("/{symbol}/latest")
def latest(symbol: str, _=Depends(verify_token)):
    sym = symbol.strip().upper()
    if not sym.endswith(("USDT", "USDC", "TRY")):
        sym = sym + "USDT"
    svc.ensure_ingestor(symbol)
    s = svc.latest.get(symbol)
    if not s:
        raise HTTPException(404, "No Signal")
    return s

@router.get("/{symbol}/stream")
async def stream(symbol: str, _=Depends(verify_token)):
    sym = symbol.strip().upper()
    if not sym.endswith(("USDT","USDC","TRY")):
        sym += "USDT"

    svc.ensure_ingestor(sym)

    async def gen():
        prev_dir = None
        try:
            while True:
                f = svc.features(sym)
                d = svc.decide(f, sym)
                curr = d["dir"]

                if curr in ("LONG","SHORT") and curr != prev_dir:
                    prev_dir = curr
                    payload = {"ts": svc.now(), "symbol": sym, "features": f, **d}

                    fc = svc.forecast(sym, f, horizon=3.0, side_hint=curr) if f else None
                    if fc and f and f.get("mid"):
                        mid = f["mid"]
                        fc["delta_abs"] = round(mid - fc["proj_price"], 8)
                        fc["delta_pct"] = round((mid - fc["proj_price"]) / mid, 6)
                        payload["forecast"] = fc
                    elif fc:
                        payload["forecast"] = fc

                    yield f"data: {json.dumps(payload)}\n\n"

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            return

    return StreamingResponse(gen(), media_type="text/event-stream")