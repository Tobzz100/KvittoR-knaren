
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
