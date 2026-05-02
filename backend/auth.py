import hashlib
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

security_scheme = HTTPBearer()


# Hash a plaintext password (we use SHA256 here - fine for a demo)
def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


# Check if the entered password matches the stored hash
def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# Create a JWT token for a user
def create_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Verify and decode a JWT token
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# FastAPI dependency to get current logged in user from the Bearer token
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security_scheme)):
    payload = decode_token(creds.credentials)
    return {
        "user_id": int(payload["sub"]),
        "username": payload["username"],
    }

