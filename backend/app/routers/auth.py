from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.database import databaseModels
from app.schemas.models import UserCreate, LoginRequest

from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt

from app.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


router = APIRouter(
    tags=["Authentication"]
)

password_hash = PasswordHash.recommended()



#Register endpoint
@router.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if username already exists
    existing_user = db.query(databaseModels.User).filter(
        databaseModels.User.username == user.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(databaseModels.User).filter(
        databaseModels.User.email == user.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = password_hash.hash(user.password)

    # Create the new user
    new_user = databaseModels.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }

#Token generation
def create_access_token(username: str):
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expires_at
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


#Log IN Endpoints
@router.post("/login")
def login_user(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
    print("🔥 LOGIN FUNCTION EXECUTED", flush=True)
    # Find the user by username
    existing_user = db.query(databaseModels.User).filter(
        databaseModels.User.username == user.username
    ).first()

    # Reject invalid credentials
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Compare entered password with stored hash
    password_is_correct = password_hash.verify(
        user.password,
        existing_user.hashed_password
    )

    if not password_is_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(existing_user.username) 

    return {
        "access_token": access_token,
        "token_type": "bearer"
        }

