

SUPPORTED_CURRENCIES = ("SEK", "EUR", "USD")


def main(shoppingList, moms, discount_code=None, currency="SEK"):
    """Sum item prices with optional discount and receipt currency. Job Done zug zug."""
    if not isinstance(currency, str):
        raise ValueError("Currency must be SEK, EUR, or USD.")
    currency = currency.strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError("Currency must be SEK, EUR, or USD.")

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

    return cost * moms




if __name__ == "__main__":
    shopping_list = input("Enter your shopping list as 'item price' pairs separated by commas (e.g. milk 10, bread 20, eggs 15): ")
    moms = 1.25
    discount_code = input("Discount code (press Enter if none): ")
    currency = input("Currency (SEK/EUR/USD) [SEK]: ").strip().upper() or "SEK"
    while True:
        try:
            price = main(shopping_list, moms, discount_code, currency)
            break
        except ValueError as error:
            print(error)
            currency = input("Currency (SEK/EUR/USD) [SEK]: ").strip().upper() or "SEK"
    print(f"{price:.2f} {currency}")
