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
from app.routers.auth import router as auth_router


app=FastAPI()
app.include_router(products_router)
app.include_router(ai_router)
app.include_router(auth_router)

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












