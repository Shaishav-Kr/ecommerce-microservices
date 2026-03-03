from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Index
from sqlalchemy.sql import func
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Indexed for fast search
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String, index=True)              # Indexed for filtering
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Composite index — optimizes queries like: filter by category, sort by price
    __table_args__ = (
        Index("ix_products_category_price", "category", "price"),
    )
