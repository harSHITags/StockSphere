from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.database import databaseModels
from app.schemas.models import UserCreate, LoginRequest

from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import os
import jwt

load_dotenv()

router = APIRouter(
    tags=["Authentication"]
)

password_hash = PasswordHash.recommended()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30