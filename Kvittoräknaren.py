

def main(shoppingList, moms ):

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
        cost += price * moms

    return cost




if __name__ == "__main__":
    shopping_list = input("Enter your shopping list as 'item price' pairs separated by commas (e.g. milk 10, bread 20, eggs 15): ")
    moms = 1.25
    price = main(shopping_list, moms)
    print(price)
