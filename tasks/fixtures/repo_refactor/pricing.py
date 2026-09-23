from decimal import Decimal


def invoice_total(lines: list[dict[str, object]]) -> Decimal:
    total = Decimal("0")
    for line in lines:
        quantity = int(line["quantity"])
        unit_price = Decimal(str(line["unit_price"]))
        if line.get("taxable", True):
            subtotal = unit_price * quantity
            discount = Decimal(str(line.get("discount", "0")))
            subtotal = subtotal * (Decimal("1") - discount)
            total += subtotal
        else:
            subtotal = unit_price * quantity
            discount = Decimal(str(line.get("discount", "0")))
            subtotal = subtotal * (Decimal("1") - discount)
            total += subtotal
    return total.quantize(Decimal("0.01"))
