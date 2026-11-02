from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import engine
from app.database import databaseModels

from app.routers.products import router as products_router
from app.routers.ai import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.orders import router as orders_router
from app.routers.purchases import router as purchases_router


app=FastAPI()
app.include_router(products_router)
app.include_router(ai_router)
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(purchases_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

databaseModels.Base.metadata.create_all(bind=engine)














