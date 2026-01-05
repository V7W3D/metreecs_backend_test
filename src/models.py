from sqlalchemy import Column, Integer, String, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Movement(Base):
    """Movement model for stock movements."""
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    type = Column(Integer, nullable=False)  # 0 = "in", 1 = "out"
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("type IN (0, 1)", name="check_movement_type"),
    )


class IdempotencyKey(Base):
    """Idempotency key model."""
    __tablename__ = "idempotency_keys"

    idempotency_key = Column(UUID, primary_key=True, nullable=False)
    response = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
