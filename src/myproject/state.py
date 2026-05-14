from src.myproject.menu import MENU_INDEX
from src.myproject.models import CartItem, CartState


class CartManager:
    def __init__(self) -> None:
        self._state = CartState(order_id="INIT_000")
        self.latest_directives = {}

    def add_or_update_item(self, item: CartItem) -> None:
        """Adds a new item or updates an existing one, then recalculates total."""
        for idx, existing in enumerate(self._state.cart_items):
            if existing.internal_uid == item.internal_uid:
                self._state.cart_items[idx] = item
                self._recalculate_total()
                return

        # If it's a new item, append it
        self._state.cart_items.append(item)
        self._recalculate_total()

    def update_status(self, internal_uid: str, approved: bool) -> bool:
        """Updates the HITL status of an item. (Used for US-05)"""
        for item in self._state.cart_items:
            if item.internal_uid == internal_uid:
                item.status = "confirmed" if approved else "denied"
                self._recalculate_total()
                return True
        return False

    def flag_fumble(self, is_fumbled: bool) -> None:
        """Sets the fumbled state flag. (Used for US-03)"""
        self._state.fumbled_state = is_fumbled

    def get_state(self) -> CartState:
        return self._state

    def clear_state(self) -> None:
        self._state = CartState(order_id="INIT_000")
        self.latest_directives = {}

    def _recalculate_total(self) -> None:
        """Calculates the exact total based on the strict Menu Index."""
        total = 0.0
        for item in self._state.cart_items:
            if item.status != "denied":
                menu_item = MENU_INDEX.get(item.item_id)
                if menu_item:
                    total += menu_item["price"] * item.qty
        self._state.running_total = total
