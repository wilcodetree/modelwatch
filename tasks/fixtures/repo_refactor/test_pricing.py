from decimal import Decimal

from pricing import invoice_total


def test_invoice_total_keeps_taxable_and_exempt_outcomes() -> None:
    lines = [
        {"quantity": 2, "unit_price": "10.00", "discount": "0.10", "taxable": True},
        {"quantity": 1, "unit_price": "5.00", "taxable": False},
    ]
    assert invoice_total(lines) == Decimal("23.00")
