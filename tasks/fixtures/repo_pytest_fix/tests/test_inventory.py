from decimal import Decimal

import pytest

from inventory import Inventory, InventoryError, Item


def test_can_reserve_all_available_stock() -> None:
    inventory = Inventory()
    inventory.add_item(Item("A-1", "Adapter", Decimal("12.50")), 4)
    assert inventory.reserve("A-1", 4) == 4
    assert inventory.available("A-1") == 0


def test_cannot_reserve_more_than_available() -> None:
    inventory = Inventory()
    inventory.add_item(Item("A-1", "Adapter", Decimal("12.50")), 4)
    with pytest.raises(InventoryError, match="insufficient"):
        inventory.reserve("A-1", 5)
