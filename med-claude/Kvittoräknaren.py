from decimal import Decimal, ROUND_HALF_UP

DISCOUNT_CODES = {
    "RABATT10": 0.10,
}

EXCHANGE_RATES_TO_SEK = {
    "SEK": 1.0,
    "EUR": 11.5,
    "USD": 10.5,
}


def main(shoppingList, moms, discount_code=None, target_currency="SEK"):

    items = shoppingList.split(",")
    subtotal = 0

    while len(items) > 0:
        raw = items.pop(0).strip()
        if not raw:
            continue
        tokens = raw.split(" ")
        currency = "SEK"
        price_str = tokens[-1]
        if len(tokens) >= 2 and tokens[-1].upper() in EXCHANGE_RATES_TO_SEK:
            currency = tokens[-1].upper()
            price_str = tokens[-2]
        try:
            price = float(price_str)
        except ValueError:
            print(f"Skipping invalid item: '{raw}'")
            continue
        subtotal += price * EXCHANGE_RATES_TO_SEK[currency]

    discount = DISCOUNT_CODES.get(discount_code, 0)
    subtotal_after_discount = subtotal * (1 - discount)
    total_sek = subtotal_after_discount * moms

    target_currency = target_currency.upper()
    return total_sek / EXCHANGE_RATES_TO_SEK[target_currency]


RECEIPT_WIDTH = 31
MAX_NAME_LENGTH = 20


def _to_decimal(value):
    return Decimal(str(value))


def _format_amount(amount):
    """Format an amount with two decimals and a decimal comma, e.g. 1234.5 -> '1234,50'."""
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}".replace(".", ",")


def _format_rate(rate):
    """Format a VAT rate without needless decimals, e.g. 25 -> '25', 12.5 -> '12,5'."""
    return format(rate.normalize(), "f").replace(".", ",")


def _receipt_line(label, amount):
    return label + _format_amount(amount).rjust(RECEIPT_WIDTH - len(label))


def format_receipt(items):
    """Return a receipt as text for a list of (name, price excl. VAT, VAT rate in percent)."""
    if not items:
        return "Inga varor"

    lines = ["KVITTO"]
    subtotal = Decimal("0")
    net_per_rate = {}

    for name, price, vat_percent in items:
        price = _to_decimal(price)
        rate = _to_decimal(vat_percent)
        if len(name) > MAX_NAME_LENGTH:
            name = name[:MAX_NAME_LENGTH - 3] + "..."
        lines.append(_receipt_line(name, price))
        subtotal += price
        net_per_rate[rate] = net_per_rate.get(rate, Decimal("0")) + price

    lines.append("-" * RECEIPT_WIDTH)
    lines.append(_receipt_line("Summa exkl. moms", subtotal))

    total = subtotal
    for rate in sorted(net_per_rate, reverse=True):
        vat = (net_per_rate[rate] * rate / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lines.append(_receipt_line(f"Moms {_format_rate(rate)} %", vat))
        total += vat

    lines.append("-" * RECEIPT_WIDTH)
    lines.append(_receipt_line("ATT BETALA", total))
    return "\n".join(lines)




if __name__ == "__main__":
    shopping_list = input("Enter your shopping list as 'item price currency' pairs separated by commas (e.g. milk 10 SEK, bread 20 EUR, eggs 15): ")
    discount_code = input("Enter a discount code (or leave blank): ").strip() or None
    target_currency = input("Enter target currency SEK/EUR/USD (or leave blank for SEK): ").strip() or "SEK"
    moms = 1.25
    price = main(shopping_list, moms, discount_code, target_currency)
    print(price)


"""
Job Done zug zug
"""
