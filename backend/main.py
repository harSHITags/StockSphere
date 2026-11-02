from fastapi import FastAPI,HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database.database import SessionLocal,engine
from sqlalchemy.orm import Session
from app.schemas.models import Product,UserCreate,LoginRequest,DescriptionRequest,InventoryAdviceRequest
import app.database.databaseModels as databaseModels
from pwdlib import PasswordHash
import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from google import genai
from app.routers.products import router as products_router
import time
from app.dependencies import get_db, get_current_user, get_current_admin
from app.routers.ai import router as ai_router


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer(auto_error=False)

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is missing from .env")


password_hash = PasswordHash.recommended()

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


app=FastAPI()
app.include_router(products_router)
app.include_router(ai_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("STEP 1: Creating tables...")
databaseModels.Base.metadata.create_all(bind=engine)
print("STEP 2: Tables created")



products=[
    Product(id=1 ,name="mobile", description="Samsung" ,price="8999", quantity=377),
    Product(id=2, name="laptop", description="HP", price="45999", quantity=120),
    Product(id=3, name="tablet", description="Apple iPad", price="32999", quantity=85) ,
    Product(id=4, name="headphones", description="Boat", price="1499", quantity=250),
    Product(id=5, name="smartwatch", description="Noise", price="2499", quantity=175),
    Product(id=6, name="keyboard", description="Logitech", price="1999", quantity=90),
]



def init_db():
      db=SessionLocal()

      count=db.query(databaseModels.Product).count()

      if count==0:

          for product in products:
               db.add(databaseModels.Product(**product.model_dump()))

      db.commit()

print("STEP 3: Initializing database...")
init_db()
print("STEP 4: Database initialized")


#Register endpoint
@app.post("/register")
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
@app.post("/login")
def login_user(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
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











