"""JWT validation helpers shared by the HTTP authentication middleware."""
import jwt
from src.core.config import JWT_SECRET

def decode_access_token(token: str) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise jwt.InvalidTokenError("Token is missing sub")
    return user_id
