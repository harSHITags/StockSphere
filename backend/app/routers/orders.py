from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.database import databaseModels
from app.schemas.models import OrderCreate

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.post("/")
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    # 1. Prevent empty orders
    if not order.items:
        raise HTTPException(
            status_code=400,
            detail="Order must contain at least one item"
        )

    # 2. Prevent duplicate product entries
    product_ids = [item.product_id for item in order.items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate products are not allowed"
        )

    # 3. Fetch products belonging to the logged-in user
    products = db.query(databaseModels.Product).filter(
        databaseModels.Product.id.in_(product_ids),
        databaseModels.Product.user_id == current_user.id
    ).all()

    product_map = {product.id: product for product in products}

    # 4. Validate product availability
    for item in order.items:
        product = product_map.get(item.product_id)

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )

    try:
        # 5. Create the order
        new_order = databaseModels.Order(
            customer_name=order.customer_name,
            user_id=current_user.id,
            status="completed"
        )

        db.add(new_order)
        db.flush()

        # 6. Create order items and deduct inventory
        for item in order.items:
            product = product_map[item.product_id]

            order_item = databaseModels.OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price
            )

            product.quantity -= item.quantity

            db.add(order_item)

        # 7. Save everything
        db.commit()
        db.refresh(new_order)

        return {
            "message": "Order placed successfully",
            "order_id": new_order.id,
            "customer_name": new_order.customer_name,
            "status": new_order.status
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to process order"
        )

@router.get("/")
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    orders = (
        db.query(databaseModels.Order)
        .filter(
            databaseModels.Order.user_id == current_user.id
        )
        .order_by(databaseModels.Order.created_at.desc())
        .all()
    )

    return orders


@router.get("/{order_id}")
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    order = (
        db.query(databaseModels.Order)
        .filter(
            databaseModels.Order.id == order_id,
            databaseModels.Order.user_id == current_user.id
        )
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    items = []

    total_amount = 0

    for item in order.items:
        subtotal = item.quantity * item.unit_price
        total_amount += subtotal

        items.append({
            "product_id": item.product_id,
            "product_name": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": subtotal
        })

    return {
        "order_id": order.id,
        "customer_name": order.customer_name,
        "status": order.status,
        "created_at": order.created_at,
        "items": items,
        "total_amount": total_amount
    }

@router.put("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    # 1. Find the order belonging to this user
    order = (
        db.query(databaseModels.Order)
        .filter(
            databaseModels.Order.id == order_id,
            databaseModels.Order.user_id == current_user.id
        )
        .with_for_update()
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # 2. Check whether order is already cancelled
    if order.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Order is already cancelled"
        )

    try:
        # 3. Restore the stock
        for item in order.items:
            product = (
                db.query(databaseModels.Product)
                .filter(
                    databaseModels.Product.id == item.product_id
                )
                .with_for_update()
                .first()
            )

            if product is not None:
                product.quantity += item.quantity

        # 4. Update order status
        order.status = "cancelled"

        # 5. Save changes
        db.commit()

        return {
            "message": "Order cancelled successfully",
            "order_id": order.id,
            "status": order.status
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to cancel order"
        )