import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    email: str = Field(..., max_length=255, unique=True, index=True, nullable=False)
    hashed_password: str = Field(..., max_length=255, nullable=False)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    recipes: List["Recipe"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    carts: List["Cart"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    orders: List["Order"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
