import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

JWT_ISSUER = "http://localhost:5246"
JWT_AUDIENCE = "http://localhost:5246" 
JWT_KEY = "wB1Ccg+nThX9ZVFaKqA6IRFptTBL7sT1FbT+gKxqT6Y4hPKV7Mtxu9hfq3WkRrMJ8lbdvq1KSoTYCVhJpXwsyA=="

ALLOWED_HS = {"HS512", "HS384", "HS256"}

def verify_token(credentials=Depends(security)):
    token = credentials.credentials
    try:
        hdr = jwt.get_unverified_header(token)
        alg = hdr.get("alg")
        if alg not in ALLOWED_HS:
            raise HTTPException(status_code=401, detail=f"Unsupported alg: {alg}")

        payload = jwt.decode(
            token,
            JWT_KEY,                        
            algorithms=list(ALLOWED_HS),    
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,          
            leeway=300                      
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
