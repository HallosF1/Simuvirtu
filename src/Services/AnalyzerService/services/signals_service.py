import time, json, asyncio, math
from collections import deque
from typing import Dict, Deque, Tuple
import websockets
from collections import defaultdict

class SignalsService:
    def __init__(self):
        self.trades: Dict[str, Deque[Tuple[float,float,float,str]]] = {}
        self.book: Dict[str, dict] = {}
        self.latest: Dict[str, dict] = {}
        self.running_ingestors: Dict[str, asyncio.Task] = {}
        self.last_error: Dict[str, str] = {}
        self.WINDOW = 20
        self.LEVELS = 5
        
        self.state = {}          
        self.last_switch = {}    
        self.streak = defaultdict(lambda: {"up": 0, "down": 0, "exit": 0})  

        self.MIN_HOLD = 2.0      
        self.K_ENTER = 4         
        self.K_EXIT  = 3         
        self.MOM_MIN = 1e-5      
        self.Z_LONG_IN  = 0.8; self.Z_LONG_OUT  = 0.5
        self.Z_SHORT_IN = 0.8; self.Z_SHORT_OUT = 0.5
        self.Z_STRONG   = 1.2; self.MOM_STRONG = 3e-5

    def now(self) -> float:
        return time.time()

    async def _ingest_symbol(self, symbol: str):
        sym = symbol.lower()
        url = f"wss://stream.binance.com:9443/stream?streams={sym}@depth5@100ms/{sym}@trade"
        print(f"[ingestor] starting {symbol} -> {url}")
        while True:
            try:
                async with websockets.connect(url, max_size=None) as ws:
                    async for msg in ws:
                        m = json.loads(msg)
                        stream = m["stream"]
                        d = m["data"]

                        if stream.endswith("@trade"):
                            side  = "buy" if d.get("m") is False else "sell"
                            price = float(d["p"]); qty = float(d["q"])
                            self.trades.setdefault(symbol, deque(maxlen=5000)) \
                                       .append((self.now(), price, qty, side))
                        elif "@depth5" in stream:
                            b_arr = d.get("bids") or d.get("b")
                            a_arr = d.get("asks") or d.get("a")
                            if not b_arr or not a_arr:
                                continue
                            def _take(px_qty):
                                if len(px_qty) >= 2:
                                    return float(px_qty[0]), float(px_qty[1])
                                p, q = px_qty 
                                return float(p), float(q)
                            bids = [_take(x) for x in b_arr[:5]]
                            asks = [_take(x) for x in a_arr[:5]]
                            self.book[symbol] = {"bids": bids, "asks": asks}

                self.last_error.pop(symbol, None)

            except Exception as e:
                self.last_error[symbol] = repr(e)
                print(f"[ingestor] {symbol} error: {e}; reconnecting in 1s")
                await asyncio.sleep(1.0)  

    def ensure_ingestor(self, symbol: str):
        t = self.running_ingestors.get(symbol)
        if t is None or t.done() or t.cancelled():
            task = asyncio.create_task(self._ingest_symbol(symbol))
            self.running_ingestors[symbol] = task
            print(f"[ingestor] scheduled task for {symbol}")

    def _gc(self, sym: str):
        cutoff = self.now() - self.WINDOW
        dq = self.trades.setdefault(sym, deque(maxlen=5000))
        while dq and dq[0][0] < cutoff:
            dq.popleft()

    def features(self, sym: str):
        b = self.book.get(sym)
        if not b:
            return None
        bid_sz = [s for _, s in b["bids"][:self.LEVELS]]
        ask_sz = [s for _, s in b["asks"][:self.LEVELS]]
        sb, sa = (sum(bid_sz) or 1e-9), (sum(ask_sz) or 1e-9)
        obi = sb / (sb + sa)
        mid = (b["bids"][0][0] + b["asks"][0][0]) / 2

        self._gc(sym)
        dq = self.trades.get(sym, deque())
        buy  = sum(q for _, _, q, s in dq if s == "buy")
        sell = sum(q for _, _, q, s in dq if s == "sell")
        tp = buy / ((buy + sell) or 1e-9)

        mom = 0.0
        if len(dq) >= 2:
            (t1, p1, _, _), (t2, p2, _, _) = dq[0], dq[-1]
            mom = (p2 - p1) / max(t2 - t1, 1e-9)

        return {"obi": obi, "tp": tp, "mid": mid, "mom": mom}

    def decide(self, f: dict, sym: str):
        if sym not in self.state:
            self.state[sym] = "NEUTRAL"
            self.last_switch[sym] = self.now()
            self.streak[sym] = {"up": 0, "down": 0, "exit": 0}

        if not f:
            return {"dir": self.state[sym], "score": 0.0}

        now = self.now()
        cur = self.state[sym]
        last = self.last_switch.get(sym, 0.0)
        held = now - last

        now = self.now()
        cur = self.state.get(sym, "NEUTRAL")
        last = self.last_switch.get(sym, 0.0)
        held = now - last

        z_obi = f.get("z_obi", (f["obi"] - 0.5) * 10.0)
        z_tp  = f.get("z_tp",  (f["tp"]  - 0.5) * 10.0)
        mom   = f.get("mom", 0.0)

        go_long   = (z_obi > self.Z_LONG_IN  and z_tp > self.Z_LONG_IN  and mom >  self.MOM_MIN)
        go_short  = (z_obi < -self.Z_SHORT_IN and z_tp < -self.Z_SHORT_IN and mom < -self.MOM_MIN)
        exit_long = (z_obi < self.Z_LONG_OUT or z_tp < self.Z_LONG_OUT or mom <= 0)
        exit_shrt = (z_obi > -self.Z_SHORT_OUT or z_tp > -self.Z_SHORT_OUT or mom >= 0)

        strong_long  = (z_obi > self.Z_STRONG and z_tp > self.Z_STRONG and mom >  self.MOM_STRONG)
        strong_short = (z_obi < -self.Z_STRONG and z_tp < -self.Z_STRONG and mom < -self.MOM_STRONG)

        st = self.streak[sym] 

        new_state = cur
        if cur == "NEUTRAL":
            if strong_long:
                new_state = "LONG"; st["up"]=st["down"]=st["exit"]=0
            elif strong_short:
                new_state = "SHORT"; st["up"]=st["down"]=st["exit"]=0
            else:
                if go_long:
                    st["up"] += 1; st["down"] = 0
                    if st["up"] >= self.K_ENTER:
                        new_state = "LONG"; st["up"]=st["down"]=st["exit"]=0
                elif go_short:
                    st["down"] += 1; st["up"] = 0
                    if st["down"] >= self.K_ENTER:
                        new_state = "SHORT"; st["up"]=st["down"]=st["exit"]=0
                else:
                    st["up"] = max(0, st["up"]-1)
                    st["down"] = max(0, st["down"]-1)

        elif cur == "LONG":
            if held < self.MIN_HOLD:
                pass
            else:
                if exit_long:
                    st["exit"] += 1
                    if st["exit"] >= self.K_EXIT:
                        new_state = "NEUTRAL"; st["exit"]=0; st["up"]=st["down"]=0
                else:
                    st["exit"] = max(0, st["exit"]-1)

        elif cur == "SHORT":
            if held < self.MIN_HOLD:
                pass
            else:
                if exit_shrt:
                    st["exit"] += 1
                    if st["exit"] >= self.K_EXIT:
                        new_state = "NEUTRAL"; st["exit"]=0; st["up"]=st["down"]=0
                else:
                    st["exit"] = max(0, st["exit"]-1)

        if new_state != cur:
            self.state[sym] = new_state
            self.last_switch[sym] = now

        score = 0.5 * f["obi"] + 0.5 * f["tp"]
        if self.state[sym] == "SHORT": score = 1 - score
        if self.state[sym] == "NEUTRAL": score = 0.0
        return {"dir": self.state[sym], "score": round(score, 3)}

    def _recent_mids(self, sym: str, seconds: float = 10.0):
        dq = self.trades.get(sym)
        b = self.book.get(sym)
        if not dq or not b:
            return []
        t_cut = self.now() - seconds
        out = []
        best_bid = b["bids"][0][0]; best_ask = b["asks"][0][0]
        last_mid = (best_bid + best_ask) / 2
        for ts, _, _, _ in dq:
            if ts >= t_cut:
                out.append((ts, last_mid))  
        return out

    def _linreg_slope(self, series):
        if len(series) < 5:
            return 0.0, 0.0
        t0 = series[0][0]
        xs = [t - t0 for t, _ in series]
        ys = [y for _, y in series]
        n = len(xs)
        sx = sum(xs); sy = sum(ys)
        sxx = sum(x*x for x in xs); sxy = sum(x*y for x, y in zip(xs, ys))
        denom = (n * sxx - sx * sx)
        if abs(denom) < 1e-12:
            return 0.0, 0.0
        slope = (n * sxy - sx * sy) / denom  
        y_mean = sy / n
        ss_tot = sum((y - y_mean)**2 for y in ys) or 1e-12
        intercept = (sy - slope * sx) / n
        y_hat = [intercept + slope * x for x in xs]
        ss_res = sum((y - yh)**2 for y, yh in zip(ys, y_hat))
        r2 = max(0.0, 1.0 - ss_res / ss_tot)
        return slope, r2

    def _vol_sigma(self, series):
        if len(series) < 6:
            return 0.0
        mids = [y for _, y in series]
        rets = [mids[i] - mids[i-1] for i in range(1, len(mids))]
        mu = sum(rets) / len(rets)
        var = sum((r - mu)**2 for r in rets) / max(1, (len(rets) - 1))
        return math.sqrt(var)

    def forecast(self, sym: str, f: dict, horizon: float = 3.0, side_hint: str | None = None):
        if not f:
            return None

        series = self._recent_mids(sym, seconds=max(6.0, horizon*3))
        if len(series) < 5:
            return None

        slope, r2 = self._linreg_slope(series)

        obi = f.get("obi", 0.5); tp = f.get("tp", 0.5)
        if side_hint == "SHORT":
            strength = max(0.0, 0.5 - obi) + max(0.0, 0.5 - tp)
            bias = -1.0  
        elif side_hint == "LONG":
            strength = max(0.0, obi - 0.5) + max(0.0, tp - 0.5)
            bias = +1.0
        else:
            strength = 0.0; bias = 0.0

        alpha = 0.5  
        beta  = 0.15 
        v = alpha * slope + beta * bias * abs(slope)

        last = f.get("last", f.get("mid"))
        proj = last + v * horizon

        sigma = self._vol_sigma(series) 
        band = 1.0 * sigma * math.sqrt(max(horizon, 1e-6))
        low, high = proj - band, proj + band

        conf = max(0.0, min(1.0, 0.6 * r2 + 0.4 * min(1.0, strength * 2)))

        return {"proj_price": round(proj, 6), "band": [round(low, 6), round(high, 6)], "confidence": round(conf, 2)}

    async def shutdown(self):
        tasks = [t for t in self.running_ingestors.values() if t and not t.done()]
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.running_ingestors.clear()
