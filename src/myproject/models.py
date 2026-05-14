from pydantic import BaseModel


class CartItem(BaseModel):
    internal_uid: str
    item_id: str
    qty: int
    tracked_modifiers: list[str] = []
    special_instructions: list[str] = []
    status: str = "confirmed"


class CartState(BaseModel):
    order_id: str
    cart_items: list[CartItem] = []
    running_total: float = 0.0
    fumbled_state: bool = False
