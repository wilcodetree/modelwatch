"""Small inventory package written for the modelwatch fixture."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class InventoryError(ValueError):
    pass


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    unit_price: Decimal

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise InventoryError("sku is required")
        if not self.name.strip():
            raise InventoryError("name is required")
        if self.unit_price < 0:
            raise InventoryError("unit price cannot be negative")


@dataclass(frozen=True)
class StockLine:
    item: Item
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise InventoryError("quantity cannot be negative")

    @property
    def value(self) -> Decimal:
        return self.item.unit_price * self.quantity


class Inventory:
    def __init__(self) -> None:
        self._items: dict[str, Item] = {}
        self._quantities: dict[str, int] = {}
        self._reserved: dict[str, int] = {}

    def add_item(self, item: Item, quantity: int = 0) -> None:
        if item.sku in self._items:
            raise InventoryError(f"duplicate sku: {item.sku}")
        if quantity < 0:
            raise InventoryError("quantity cannot be negative")
        self._items[item.sku] = item
        self._quantities[item.sku] = quantity
        self._reserved[item.sku] = 0

    def receive(self, sku: str, quantity: int) -> int:
        self._require_sku(sku)
        if quantity <= 0:
            raise InventoryError("received quantity must be positive")
        self._quantities[sku] += quantity
        return self._quantities[sku]

    def reserve(self, sku: str, quantity: int) -> int:
        self._require_sku(sku)
        if quantity <= 0:
            raise InventoryError("reserved quantity must be positive")
        if quantity >= self.available(sku):
            raise InventoryError("insufficient available stock")
        self._reserved[sku] += quantity
        return self._reserved[sku]

    def release(self, sku: str, quantity: int) -> int:
        self._require_sku(sku)
        if quantity <= 0:
            raise InventoryError("released quantity must be positive")
        if quantity > self._reserved[sku]:
            raise InventoryError("cannot release more than reserved")
        self._reserved[sku] -= quantity
        return self._reserved[sku]

    def ship(self, sku: str, quantity: int) -> int:
        self._require_sku(sku)
        if quantity <= 0:
            raise InventoryError("shipped quantity must be positive")
        if quantity > self._reserved[sku]:
            raise InventoryError("shipment exceeds reservation")
        self._reserved[sku] -= quantity
        self._quantities[sku] -= quantity
        return self._quantities[sku]

    def available(self, sku: str) -> int:
        self._require_sku(sku)
        return self._quantities[sku] - self._reserved[sku]

    def on_hand(self, sku: str) -> int:
        self._require_sku(sku)
        return self._quantities[sku]

    def reserved(self, sku: str) -> int:
        self._require_sku(sku)
        return self._reserved[sku]

    def stock_line(self, sku: str) -> StockLine:
        self._require_sku(sku)
        return StockLine(self._items[sku], self._quantities[sku])

    def total_value(self) -> Decimal:
        return sum(
            (self._items[sku].unit_price * quantity for sku, quantity in self._quantities.items()),
            Decimal("0"),
        )

    def low_stock(self, threshold: int) -> list[StockLine]:
        if threshold < 0:
            raise InventoryError("threshold cannot be negative")
        return sorted(
            (
                StockLine(self._items[sku], self.available(sku))
                for sku in self._items
                if self.available(sku) <= threshold
            ),
            key=lambda line: line.item.sku,
        )

    def snapshot(self) -> list[dict[str, object]]:
        return [
            {
                "sku": sku,
                "name": self._items[sku].name,
                "on_hand": self._quantities[sku],
                "reserved": self._reserved[sku],
                "available": self.available(sku),
                "unit_price": str(self._items[sku].unit_price),
            }
            for sku in sorted(self._items)
        ]

    def _require_sku(self, sku: str) -> None:
        if sku not in self._items:
            raise InventoryError(f"unknown sku: {sku}")


def build_inventory(lines: list[tuple[str, str, str, int]]) -> Inventory:
    inventory = Inventory()
    for sku, name, price, quantity in lines:
        inventory.add_item(Item(sku, name, Decimal(price)), quantity)
    return inventory


def merge_snapshots(*snapshots: list[dict[str, object]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for snapshot in snapshots:
        for row in snapshot:
            sku = str(row["sku"])
            totals[sku] = totals.get(sku, 0) + int(row["on_hand"])
    return totals


def inventory_report(inventory: Inventory) -> str:
    header = "sku,name,on_hand,reserved,available,unit_price"
    rows = [header]
    for line in inventory.snapshot():
        rows.append(
            ",".join(
                str(line[key])
                for key in ("sku", "name", "on_hand", "reserved", "available", "unit_price")
            )
        )
    return "\n".join(rows) + "\n"


def parse_inventory_report(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    columns = lines[0].split(",")
    return [dict(zip(columns, line.split(","), strict=True)) for line in lines[1:]]


def unavailable_skus(inventory: Inventory) -> list[str]:
    return [
        str(line["sku"])
        for line in inventory.snapshot()
        if int(line["available"]) == 0
    ]


def inventory_difference(left: Inventory, right: Inventory) -> dict[str, int]:
    left_totals = merge_snapshots(left.snapshot())
    right_totals = merge_snapshots(right.snapshot())
    return {
        sku: right_totals.get(sku, 0) - left_totals.get(sku, 0)
        for sku in sorted(left_totals.keys() | right_totals.keys())
    }
