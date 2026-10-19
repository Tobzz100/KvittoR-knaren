import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

DISCOUNT_CODES = {
    "RABATT10": 0.10,
}

EXCHANGE_RATES_TO_SEK = {
    "SEK": 1.0,
    "EUR": 11.5,
    "USD": 10.5,
}


def parse_shopping_list(shoppingList):
    """Parse 'item price [currency]' entries into (name, price in SEK) tuples, skipping invalid ones."""
    items = shoppingList.split(",")
    parsed = []

    while len(items) > 0:
        raw = items.pop(0).strip()
        if not raw:
            continue
        tokens = raw.split(" ")
        currency = "SEK"
        price_index = -1
        if len(tokens) >= 2 and tokens[-1].upper() in EXCHANGE_RATES_TO_SEK:
            currency = tokens[-1].upper()
            price_index = -2
        try:
            price = float(tokens[price_index])
        except ValueError:
            print(f"Skipping invalid item: '{raw}'")
            continue
        if not math.isfinite(price) or price < 0:
            # float() accepts "nan" and "inf", and negative prices make no sense here
            print(f"Skipping invalid item: '{raw}'")
            continue
        name = " ".join(t for t in tokens[:price_index] if t) or "Vara"
        parsed.append((name, price * EXCHANGE_RATES_TO_SEK[currency]))

    return parsed


def main(shoppingList, moms, discount_code=None, target_currency="SEK"):

    subtotal = sum(price_sek for _name, price_sek in parse_shopping_list(shoppingList))

    discount = DISCOUNT_CODES.get(discount_code, 0)
    subtotal_after_discount = subtotal * (1 - discount)
    total_sek = subtotal_after_discount * moms

    target_currency = target_currency.upper()
    return total_sek / EXCHANGE_RATES_TO_SEK[target_currency]


# Svenska momssatser i procent -> andel av priset exkl. moms
VAT_RATES = {
    25: Decimal("0.25"),
    12: Decimal("0.12"),
    6: Decimal("0.06"),
    0: Decimal("0"),
}

RECEIPT_WIDTH = 31
MAX_NAME_LENGTH = 20


def _to_decimal(value):
    return Decimal(str(value))


def _to_price(value):
    """Convert a price to Decimal, raising ValueError unless it is a finite number >= 0."""
    try:
        price = _to_decimal(value)
    except InvalidOperation:
        raise ValueError(f"Ogiltigt pris: {value!r}. Priset måste vara ett tal.") from None
    if not price.is_finite() or price < 0:
        raise ValueError(f"Ogiltigt pris: {value!r}. Priset måste vara ett tal som är 0 eller större.")
    return price


def _format_amount(amount):
    """Format an amount with two decimals and a decimal comma, e.g. 1234.5 -> '1234,50'."""
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}".replace(".", ",")


def _format_rate(rate):
    """Format a VAT rate without needless decimals, e.g. 25 -> '25', 12.5 -> '12,5'."""
    return format(rate.normalize(), "f").replace(".", ",")


def _receipt_line(label, amount):
    return label + _format_amount(amount).rjust(RECEIPT_WIDTH - len(label))


def vat_breakdown(items):
    """Returnerar momsbelopp per momssats, högsta sats först, t.ex. {25: 25.00, 12: 6.00}.

    Beloppen är Decimal avrundade till två decimaler.
    """
    net_per_rate = {}
    for _name, price, vat_percent in items:
        rate = _to_decimal(vat_percent)
        if rate not in VAT_RATES:
            raise ValueError(f"Ogiltig momssats: {vat_percent} %. Tillåtna: 25, 12, 6 och 0 %.")
        net_per_rate[rate] = net_per_rate.get(rate, Decimal("0")) + _to_price(price)

    breakdown = {}
    for rate in sorted(net_per_rate, reverse=True):
        vat = net_per_rate[rate] * VAT_RATES[rate]
        breakdown[rate] = vat.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return breakdown


def format_receipt(items):
    """Return a receipt as text for a list of (name, price excl. VAT, VAT rate in percent)."""
    if not items:
        return "Inga varor"

    lines = ["KVITTO"]
    subtotal = Decimal("0")

    for name, price, _vat_percent in items:
        price = _to_price(price)
        if len(name) > MAX_NAME_LENGTH:
            name = name[:MAX_NAME_LENGTH - 3] + "..."
        lines.append(_receipt_line(name, price))
        subtotal += price

    lines.append("-" * RECEIPT_WIDTH)
    lines.append(_receipt_line("Summa exkl. moms", subtotal))

    # vat_breakdown() may return plain ints/floats in any order, so normalize to Decimal and sort here.
    breakdown = {_to_decimal(rate): _to_decimal(vat) for rate, vat in vat_breakdown(items).items()}
    total = subtotal
    for rate in sorted(breakdown, reverse=True):
        vat = breakdown[rate].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lines.append(_receipt_line(f"Moms {_format_rate(rate)} %", vat))
        total += vat

    lines.append("-" * RECEIPT_WIDTH)
    lines.append(_receipt_line("ATT BETALA", total))
    return "\n".join(lines)


DEFAULT_VAT_PERCENT = 25


if __name__ == "__main__":
    shopping_list = input("Enter your shopping list as 'item price currency' pairs separated by commas (e.g. milk 10 SEK, bread 20 EUR, eggs 15): ")
    items = [(name, price_sek, DEFAULT_VAT_PERCENT) for name, price_sek in parse_shopping_list(shopping_list)]
    print(format_receipt(items))


"""
Job Done zug zug
"""
