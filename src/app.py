from uuid import UUID
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from database import get_db
from models import Movement, IdempotencyKey
from schemas import MovementCreate, MovementResponse, ProductStock, TYPE_TO_INT, INT_TO_TYPE

app = FastAPI(title="Metreecs API")


@app.post("/movements", response_model=MovementResponse, status_code=201)
async def create_movement(
    movement: MovementCreate,
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[UUID] = Header(default=None)
):
    """Enregistrer un mouvement de stock."""
    
    # Check if idempotency key exists
    if idempotency_key:
        result = await db.execute(
            select(IdempotencyKey).where(IdempotencyKey.idempotency_key == idempotency_key)
        )
        existing_key = result.scalar_one_or_none()
        
        if existing_key:
            # Return cached response
            return MovementResponse(**existing_key.response)
    
    # Process the request normally
    db_movement = Movement(
        product_id=movement.product_id,
        quantity=movement.quantity,
        type=TYPE_TO_INT[movement.type]
    )
    db.add(db_movement)
    await db.commit()
    await db.refresh(db_movement)
    
    response = MovementResponse(
        id=db_movement.id,
        product_id=db_movement.product_id,
        quantity=db_movement.quantity,
        type=INT_TO_TYPE[db_movement.type],
        created_at=db_movement.created_at.strftime("%Y/%m/%d %H:%M")
    )
    
    # Store the idempotency key and response
    if idempotency_key:
        db_idempotency = IdempotencyKey(
            idempotency_key=idempotency_key,
            response=response.model_dump()
        )
        db.add(db_idempotency)
        await db.commit()
    
    return response


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}


@app.get("/products/{product_id}/stock", response_model=ProductStock, status_code=200)
async def get_product_stock(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    if_none_match: Optional[str] = Header(default=None)
):
    """Obtenir le stock actuel d'un produit."""
    
    # Get the last movement ID for this product
    last_movement_result = await db.execute(
        select(Movement.id)
        .where(Movement.product_id == product_id)
        .order_by(Movement.id.desc())
        .limit(1)
    )
    last_movement_id = last_movement_result.scalar()
    
    # Product has no movements - return 404
    if last_movement_id is None:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    
    # Generate ETag from last movement ID
    etag = f'W/"{last_movement_id}"'
    
    # Check if client has cached version - return 304
    if if_none_match and if_none_match == etag:
        return Response(status_code=304, headers={"ETag": etag})
    
    # Compute current stock
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Movement.type == 0, Movement.quantity),
                        else_=-Movement.quantity
                    )
                ),
                0
            ).label("current_stock")
        ).where(Movement.product_id == product_id)
    )
    current_stock = result.scalar()
    
    return Response(
        content=ProductStock(product_id=product_id, current_stock=current_stock).model_dump_json(),
        media_type="application/json",
        headers={"ETag": etag}
    )
