from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, get_current_user, get_current_admin
from app.database import databaseModels
from app.schemas.models import Product

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("/")
def get_all_products(
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    db_products = (
        db.query(databaseModels.Product)
        .filter(databaseModels.Product.user_id == current_user.id)
        .all()
    )

    return db_products


@router.get("/{id}")
def get_product_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    db_product = (
        db.query(databaseModels.Product)
        .filter(
            databaseModels.Product.id == id,
            databaseModels.Product.user_id == current_user.id
        )
        .first()
    )

    if db_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return db_product



@router.post("/")
def add_product(
    product: Product,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    # Step 1: Find this user's highest product number
    last_number = db.query(
        func.max(databaseModels.Product.user_product_number)
    ).filter(
        databaseModels.Product.user_id == current_user.id
    ).scalar()

    # Step 2: Generate the next number for this user
    next_number = (last_number or 0) + 1

    # Step 3: Create the product
    new_product = databaseModels.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        quantity=product.quantity,
        user_id=current_user.id,
        user_product_number=next_number
    )

    # Step 4: Save it to the database
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product



@router.put("/{id}")
def update_products(
    id: int,
    product: Product,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    db_product = (
        db.query(databaseModels.Product)
        .filter(
            databaseModels.Product.id == id,
            databaseModels.Product.user_id == current_user.id
        )
        .first()
    )

    if db_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db_product.name = product.name
    db_product.description = product.description
    db_product.price = product.price
    db_product.quantity = product.quantity

    db.commit()
    db.refresh(db_product)

    return db_product



@router.delete("/{id}")
def delete_products(
    id: int,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_admin)
):
    db_product = (
        db.query(databaseModels.Product)
        .filter(
            databaseModels.Product.id == id,
            databaseModels.Product.user_id == current_user.id
        )
        .first()
    )

    if db_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(db_product)
    db.commit()

    return {"message": "Product successfully removed"}

