from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User
from auth import verify_password, create_token

router = APIRouter(prefix="/api", tags=["auth"])


# Pydantic model for login request body
class LoginRequest(BaseModel):
    username: str
    password: str


# Pydantic model for login response
class LoginResponse(BaseModel):
    token: str
    username: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # Find the user by username
    user = db.query(User).filter(User.username == body.username).first()

    # Check if user exists and password matches
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong username or password")

    # Create and return the token
    token = create_token(user.id, user.username)
    return LoginResponse(token=token, username=user.username)

