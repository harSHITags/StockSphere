from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.database import databaseModels
from app.schemas.models import PurchaseCreate

router = APIRouter(
    prefix="/purchases",
    tags=["Purchases"]
)

@router.post("/")
def create_purchase(
    purchase: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    if not purchase.items:
        raise HTTPException(
            status_code=400,
            detail="Purchase must contain at least one item"
        )

    product_ids = [item.product_id for item in purchase.items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate products are not allowed"
        )

    products = db.query(databaseModels.Product).filter(
        databaseModels.Product.id.in_(product_ids),
        databaseModels.Product.user_id == current_user.id
    ).with_for_update().all()

    product_map = {product.id: product for product in products}

    for item in purchase.items:
        if item.product_id not in product_map:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

    try:
        new_purchase = databaseModels.Purchase(
            supplier_name=purchase.supplier_name,
            user_id=current_user.id
        )

        db.add(new_purchase)
        db.flush()

        total_cost = 0

        for item in purchase.items:
            product = product_map[item.product_id]

            purchase_item = databaseModels.PurchaseItem(
                purchase_id=new_purchase.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_cost=item.unit_cost
            )

            product.quantity += item.quantity

            total_cost += item.quantity * item.unit_cost

            db.add(purchase_item)

        db.commit()
        db.refresh(new_purchase)

        return {
            "message": "Purchase recorded successfully",
            "purchase_id": new_purchase.id,
            "supplier_name": new_purchase.supplier_name,
            "total_cost": round(total_cost, 2)
        }

  except Exception as e:
    db.rollback()
    print("Purchase error:", str(e))
    raise HTTPException(
        status_code=500,
        detail="Unable to record purchase"
    )