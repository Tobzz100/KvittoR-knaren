

EXCHANGE_RATES = {
    "SEK": 1.0,
    "EUR": 11.5,
    "USD": 10.5,
}


def main(shoppingList, moms, discount_code=None, currency="SEK"):
    """Sum item prices, apply an optional discount before VAT, then convert to the requested currency. Job Done zug zug."""

    currency = currency.strip().upper()
    if currency not in EXCHANGE_RATES:
        raise ValueError(f"Okänd valuta: {currency}")

    items = shoppingList.split(",")
    cost = 0

    while len(items) > 0:
        raw = items.pop(0).strip()
        if not raw:
            continue
        price_str = raw.split(" ")[-1]
        try:
            price = float(price_str)
        except ValueError:
            print(f"Skipping invalid item: '{raw}'")
            continue
        cost += price

    if discount_code and discount_code.strip().upper() == "RABATT10":
        cost *= 0.9

    return cost * moms / EXCHANGE_RATES[currency]




if __name__ == "__main__":
    shopping_list = input("Enter your shopping list as 'item price' pairs separated by commas (e.g. milk 10, bread 20, eggs 15): ")
    moms = 1.25
    discount_code = input("Discount code (press Enter if none): ")
    currency = input("Currency (SEK/EUR/USD, press Enter for SEK): ").strip() or "SEK"
    price = main(shopping_list, moms, discount_code, currency)
    print(price)
