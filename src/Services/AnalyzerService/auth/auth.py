# auth.py
import jwt  # PyJWT==2.8.0
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

JWT_ISSUER = "http://localhost:5246"
JWT_AUDIENCE = "http://localhost:5246"   # token'ında aud var (TokenService'de set edilmiş)
JWT_KEY = "wB1Ccg+nThX9ZVFaKqA6IRFptTBL7sT1FbT+gKxqT6Y4hPKV7Mtxu9hfq3WkRrMJ8lbdvq1KSoTYCVhJpXwsyA=="

ALLOWED_HS = {"HS512", "HS384", "HS256"}  # HS512 başta

def verify_token(credentials=Depends(security)):
    token = credentials.credentials
    try:
        hdr = jwt.get_unverified_header(token)
        alg = hdr.get("alg")
        if alg not in ALLOWED_HS:
            raise HTTPException(status_code=401, detail=f"Unsupported alg: {alg}")

        # aud doğrulamak istiyorsan audience=JWT_AUDIENCE ver; emin değilsen verify_aud=False kullan.
        payload = jwt.decode(
            token,
            JWT_KEY,                        # .NET'teki SigninKey ile HARFİ HARFİNE aynı string; base64 decode YOK
            algorithms=list(ALLOWED_HS),    # HS512 dahil
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,          # aud token'da var; istersen verify_aud=False yapabilirsin
            leeway=300                      # 5 dk tolerans (nbf/exp saat farkı)
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid signature")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except jwt.ImmatureSignatureError:
        raise HTTPException(status_code=401, detail="Token not yet valid (nbf)")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
