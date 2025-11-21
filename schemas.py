"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# -----------------------------------------------------------------------------
# Example schemas
# -----------------------------------------------------------------------------

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# -----------------------------------------------------------------------------
# App-specific schemas
# -----------------------------------------------------------------------------

class TemplateElement(BaseModel):
    id: str
    type: str = Field(..., description="rectangle | text | image")
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0
    styles: Dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None  # text content or image URL placeholder

class Template(BaseModel):
    name: str
    description: Optional[str] = None
    width: int = 1080
    height: int = 1350
    background: str = "#0b0f1a"
    palette: List[str] = Field(default_factory=lambda: ["#FF7A00", "#111827", "#F3F4F6"])  # orange/neutral
    fonts: List[str] = Field(default_factory=lambda: ["Inter", "Manrope"])
    elements: List[TemplateElement] = Field(default_factory=list)

class Guide(BaseModel):
    source_name: str
    detected: Dict[str, Any] = Field(default_factory=dict)
    steps: Dict[str, List[str]] = Field(default_factory=dict)  # tool -> steps

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
