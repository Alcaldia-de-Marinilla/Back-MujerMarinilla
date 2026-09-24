from datetime import datetime

from app.schemas.base import CamelModel


class Token(CamelModel):
    access_token: str
    token_type: str = "bearer"


class AdminOut(CamelModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime
