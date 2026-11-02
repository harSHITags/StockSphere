from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_db
from app.database import databaseModels
from app.schemas.models import DescriptionRequest, InventoryAdviceRequest
from sqlalchemy.orm import Session
from google import genai
from app.core.config import GEMINI_API_KEY

router = APIRouter(
    prefix="/products",
    tags=["AI Services"]
)

client = genai.Client(
    api_key=GEMINI_API_KEY
)


@router.post("/generate-description")
def generate_product_description(
    request: DescriptionRequest,
    current_user: databaseModels.User = Depends(get_current_user)
):
    prompt = f"""
    Write a clear, professional product description for an inventory
    management application.

    Product name: {request.name}
    Category: {request.category}

    Requirements:
    - Keep it between 40 and 70 words.
    - Describe the product naturally.
    - Do not invent specifications or features not provided.
    - Return only the description.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        if not response.text:
            raise HTTPException(
                status_code=502,
                detail="AI returned an empty description."
            )

        return {"description": response.text.strip()}

    except HTTPException:
        raise

    except Exception as e:
       print("Gemini API error:", repr(e))
    raise HTTPException(
        status_code=502,
        detail="Unable to generate a description. Check backend logs."
      )

#inventory endpoint

@router.post("/inventory-advice")
def get_inventory_advice(
    request: InventoryAdviceRequest,
    db: Session = Depends(get_db),
    current_user: databaseModels.User = Depends(get_current_user)
):
    # 1. Fetch only the logged-in user's products
    products = (
        db.query(databaseModels.Product)
        .filter(
            databaseModels.Product.user_id == current_user.id
        )
        .all()
    )

    # 2. Prepare a summary for Gemini
    inventory = []

    for product in products:
        quantity = int(product.quantity)

        if quantity == 0:
            status = "Out of stock"
        elif quantity <= request.low_stock_threshold:
            status = "Low stock"
        else:
            status = "Healthy"

        inventory.append({
            "name": product.name,
            "quantity": quantity,
            "price": float(product.price),
            "status": status
        })

    # 3. Ask Gemini to analyse the inventory
    prompt = f"""
    You are an inventory management advisor.

    Analyse the following inventory data:
    {inventory}

    Provide:
    1. A short overall inventory summary.
    2. Products that need attention and why.
    3. Practical recommendations for the user.

    Only use the supplied data.
    Do not invent sales history, demand forecasts,
    supplier information, or missing product details.
    If there are no products, explain that the inventory is empty.

    Return a clear, concise answer with headings.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        advice = (response.text or "").strip()

        if not advice:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response."
            )

        return {
            "inventory": inventory,
            "advice": advice
        }

    except HTTPException:
        raise

    except Exception as e:
        print("Gemini inventory advice error:", repr(e))
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again."
        )
    