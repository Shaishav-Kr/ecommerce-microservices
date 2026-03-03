from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import httpx, os
import models, schemas, database

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Orders Service")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8002")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{AUTH_SERVICE_URL}/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")
    return resp.json()

@app.get("/health")
def health_check():
    return {"status": "Orders service running"}

@app.post("/orders", response_model=schemas.OrderOut, status_code=201)
async def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Place a new order.
    1. Verifies the user is authenticated
    2. Fetches each product from Catalog Service
    3. Creates the order with a calculated total
    """
    order = models.Order(user_id=current_user["user_id"])
    db.add(order)
    db.flush()  # Get the order ID before committing

    total = 0.0
    async with httpx.AsyncClient() as client:
        for item in order_data.items:
            # Fetch real product data from Catalog Service
            resp = await client.get(f"{CATALOG_SERVICE_URL}/products/{item.product_id}")
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            
            product = resp.json()
            line_total = product["price"] * item.quantity
            total += line_total

            order_item = models.OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=product["name"],   # Snapshot the name for history
                quantity=item.quantity,
                unit_price=product["price"]
            )
            db.add(order_item)

    order.total_price = total
    order.status = "confirmed"
    db.commit()
    db.refresh(order)
    return order

@app.get("/orders", response_model=list[schemas.OrderOut])
async def list_my_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all orders for the currently logged-in user"""
    return db.query(models.Order).filter(
        models.Order.user_id == current_user["user_id"]
    ).all()

@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your order")
    return order

@app.patch("/orders/{order_id}/status")
async def update_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    db.commit()
    return {"message": f"Order {order_id} status updated to {status}"}
