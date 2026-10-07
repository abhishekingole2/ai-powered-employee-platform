import jwt
import os
from typing import Callable
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserDB


bearer_scheme = HTTPBearer()
load_dotenv()
password_hash = PasswordHash.recommended()


SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not configured")




def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(data: dict) -> str:
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = (
        db.query(UserDB)
        .filter(UserDB.id == int(user_id))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists"
        )

    return user

def require_role(*allowed_roles: str):
    def role_checker(
        current_user: UserDB = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

        return current_user

    return role_checker