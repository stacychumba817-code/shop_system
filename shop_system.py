import datetime

# Shop and Inventory Management System
# author name=[Stacy]
# date=[19/06/2026]
# purpose:Manage products,stocks available and sales for my shop

SHOP_NAME = "CRYSTAL GENERAL SHOP"

inventory = {
    "A": {"name": "rice", "price": 120.00, "category": "grain", "quantity": 55, "active": True},
    "B": {"name": "sugar", "price": 160.00, "category": "food", "quantity": 31, "active": True},
    "C": {"name": "beans", "price": 150.00, "category": "cereal", "quantity": 50, "active": True},
    "D": {"name": "bread", "price": 120.00, "category": "whole foods", "quantity": 30, "active": True},
    "E": {"name": "bar soap", "price": 180.00, "category": "cleaning product", "quantity": 15, "active": True},
}

sales_history = []
active_cart = {}


def view_products():
    print("\n--- Available Products ---")
    for key, item in inventory.items():
        if item["active"]:
            print(
                f"Product {key}. Name: {item['name']} | Price: Kes {item['price']:.2f} | Category: {item['category']} | Stock: {item['quantity']}|available: {item['active']}")

    choice = input("\nEnter product letter to view details, or press Enter to return: ").upper().strip()

    if choice == "":
        return
    if choice in inventory and inventory[choice]["active"]:
        prod = inventory[choice]
        print(
            f"\n[Detail] Product {choice}: {prod['name']} | Price: Kes {prod['price']:.2f} | Stock: {prod['quantity']}|available: {prod['active']}")
    else:
        print("\nProduct not available.")


def add_product():
    new = input("Enter product code: ").upper().strip()

    if new in inventory:
        if not inventory[new]["active"]:
            print(f"\nProduct {new} exists but is currently deleted.")
            action = input("Do you want to add and restock it? (yes/no): ").lower().strip()
            if action == 'yes':
                quantity = int(input("Enter quantity to add: "))
                inventory[new]["quantity"] = quantity
                inventory[new]["active"] = True
                print(f"\nProduct {new} has been restocked successfully!")
            return
        else:
            print(f"\nProduct {new} is already active in the inventory!!")
            action = input(
                "Do you want to add to its stock? (type 'add' to proceed): or press enter to continue ").lower().strip()
            if action == 'add':
                quantity = int(input("Enter quantity: "))
                inventory[new]["quantity"] += quantity
                print(f"\nStock updated successfully!")
            return

    name = input("Enter product name: ").strip()
    price = float(input("Enter product price: "))
    category_name = input("Enter product category: ").strip()
    quantity = int(input("Enter product quantity: "))

    inventory[new] = {
        "name": name,
        "price": price,
        "category": category_name,
        "quantity": quantity,
        "active": True
    }
    print(f"\nProduct '{name}' has been added to inventory under code '{new}'")


def remove_product():
    remove = input("\nEnter product code to remove: ").upper().strip()
    if remove in inventory:
        if inventory[remove]["active"]:
            inventory[remove]["active"] = False
            print(f"\nProduct '{remove}' has been removed (hidden from shop, kept for history).")
        else:
            print("\nProduct is already removed.")
    else:
        print("\nProduct code not found!")


def search(query,inventory):
    query = query.lower().strip()
    results_list = []
    for code, details in inventory.items():
        if details["active"]:
            if query in code.lower() or query in details["name"].lower() or query in details["category"].lower():
                results_list.append((code, details))
    return results_list


def low_stock(inventory, threshold=15):
    print(f"\n--- Low Stock Alert!! (Threshold: {threshold} items) ---")
    low_stock_found = False

    for code, details in inventory.items():
        if details["active"]:
            if details["quantity"] <= threshold:
                print(f"[LOW STOCK] Product {code}: {details['name']} | Remaining Stock: {details['quantity']}")
                low_stock_found = True

    if not low_stock_found:
        print("All active products have sufficient stock!!")


def results(inventory, threshold=20):
    raw_query = input("\nEnter product code or keyword to search (or type 'low' to see low stock items): ").strip()
    query = raw_query.lower()

    if query == "low":
        print(f"--- Low Stock Alert (Threshold: {threshold}) ---")
        low_stock_found = False
        for code, details in inventory.items():
            if details["active"] and details["quantity"] <= threshold:
                print(f"[Low] {details['name'].upper()} ({code}) only {details['quantity']} left")
                low_stock_found = True
        if not low_stock_found:
            print("Products have sufficient stock")
    else:
        search_results = []
        for code, details in inventory.items():
            if details["active"]:
                if query == code.lower() or query in details["name"].lower() or query in details["category"].lower():
                    search_results.append((code, details))
        if search_results:
            print(f"\n--- Search results for '{raw_query}' ---")
            for code, item in search_results:
                status = " [LOW]" if item['quantity'] <= threshold else ""
                print(
                    f"Product: {code} | Name: {item['name']}{status} | Category: {item['category']} | Price: Kes {item['price']:.2f} | Stock: {item['quantity']}")
        else:
            print(f"\nNo active products match '{raw_query}'.")


def record_sale():
    print("\n--- Record Direct Sale ---")
    sale = input("Enter product code: ").upper().strip()

    if sale not in inventory:
        print(f"\nProduct '{sale}' is not in the inventory.")
        return

    product = inventory[sale]

    if not product["active"]:
        print(f"\nError! Product '{product['name']}' is deactivated!.")
        return

    if product["quantity"] <= 0:
        print(f"\nError! Product '{product['name']}' is not in stock.")
        return

    print(f"\nProduct '{product['name']}' is available. Current Stock: {product['quantity']}.")

    try:
        quantity_to_buy = int(input("Enter quantity to buy: "))
    except ValueError:
        print("\nError! Please enter a valid number.")
        return

    if quantity_to_buy <= 0:
        print("\nYou cannot buy a product with less than one item!!")
        return

    if quantity_to_buy > product["quantity"]:
        print("\nNot enough items in stock to fulfill this buy!!")
        return

    product["quantity"] -= quantity_to_buy
    today_str = datetime.date.today().strftime("%d/%m/%Y")

    sale_entry = {
        "date": today_str,
        "code": sale,
        "name": product["name"],
        "quantity_sold": quantity_to_buy,
        "price": product["price"],
    }
    sales_history.append(sale_entry)

    print(f"\n---SALE RECORD---")
    print(f"Item: {product['name']}")
    print(f"Quantity Sold: {quantity_to_buy}")
    print(f"Price per unit: Kes {product['price']}")
    print(f"Remaining Stock: {product['quantity']}")


# --- CONTINUOUS ADD TO CART FUNCTION ---
def add_to_cart():
    print("\n--- Add Products to Cart ---")
    print("(Type 'done' at the product code prompt when finished adding items)")

    while True:
        user_input = input("\nEnter product code (or type 'done' to stop): ").strip()

        if user_input.lower() == "done":
            print(f"\nFinished adding items. Total items currently in cart: {len(active_cart)}")
            return

        code = user_input.upper()

        if code not in inventory or not inventory[code]["active"]:
            print(f"Error! Product '{code}' is invalid or deactivated!!")
            continue

        product = inventory[code]
        available_stock = product["quantity"]

        if code in active_cart:
            available_stock -= active_cart[code]["quantity"]

        if available_stock <= 0:
            print(f"Error! '{product['name']}' is sold out or maximum stock is already in your cart!")
            continue

        print(f"Selected: {product['name']} | Price: Kes {product['price']} | Available stock: {available_stock}")

        try:
            quantity = int(input(f"Enter quantity of {product['name']} to add: "))
            if quantity <= 0:
                print("Error! Quantity must be greater than zero.")
                continue
            if quantity > available_stock:
                print(f"Error! Only {available_stock} units left in stock.")
                continue
        except ValueError:
            print("Error! Please enter a valid number.")
            continue

        if code in active_cart:
            active_cart[code]["quantity"] += quantity
        else:
            active_cart[code] = {
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity
            }

        print(f"Added {quantity}x '{product['name']}' to cart successfully.")


def view_and_checkout_cart():
    global active_cart

    print("\n--- Active Shopping Cart ---")

    if not active_cart:
        print("Your cart is empty.")
        return

    cart_total = 0.0
    print("-" * 60)

    for code, item in active_cart.items():
        item_total = item["price"] * item["quantity"]
        cart_total += item_total
        print(f"Code: {code} | {item['name'].capitalize()} | Qty: {item['quantity']} | Total: Kes {item_total:.2f}")

    print("-" * 60)
    print(f"Cart Total: Kes {cart_total:.2f}")

    action = input("\nType 'checkout' to buy items, 'clear' to empty cart, or press Enter to return: ").lower().strip()

    if action == "checkout":
        today_str = datetime.date.today().strftime("%d/%m/%Y")

        for code, item in active_cart.items():
            inventory[code]["quantity"] -= item["quantity"]

            sale_entry = {
                "date": today_str,
                "code": code,
                "name": item["name"],
                "quantity_sold": item["quantity"],
                "price": item["price"]
            }

            sales_history.append(sale_entry)

        print("\nCheckout completed successfully!")
        active_cart.clear()

    elif action == "clear":
        active_cart.clear()
        print("Cart cleared.")

def generate_daily_report():
    today_str = datetime.date.today().strftime("%d/%m/%Y")

    print(f"DAILY FINANCIAL & STOCK REPORT")
    print(f"SHOP: {SHOP_NAME} ")
    print(f"DATE: {today_str}  ")

    total_inventory_value = 0.0
    active_items_list = []

    for code, details in inventory.items():
        if details["active"]:
            item_value = details["price"] * details["quantity"]
            total_inventory_value += item_value
            active_items_list.append((code, details))

    print(f"\n SHOP INVENTORY SUMMARY")
    print(f" Total Active Stock Items Checked : {len(active_items_list)}")
    print(f" Current Total Inventory Value    : Kes {total_inventory_value:,.2f}")
    print(f"\n TODAY'S TRANSACTION LOG")
    print(
        f"  {'Index':<6} | {'Code':<5} | {'Product Name':<15} | {'Qty Sold':<8} | {'Unit Price':<12} | {'Total Price':<12}")

    daily_sales_revenue = 0.0
    daily_items_sold_count = 0
    transaction_count = 0
    product_frequency = {}

    for sale in sales_history:
        if sale.get("date") == today_str:
            transaction_count += 1
            qty_sold = sale["quantity_sold"]
            unit_price = sale["price"]
            line_item_total = qty_sold * unit_price

            daily_sales_revenue += line_item_total
            daily_items_sold_count += qty_sold

            prod_name = sale["name"]
            product_frequency[prod_name] = product_frequency.get(prod_name, 0) + qty_sold

            print(
                f"  {transaction_count:<6} | {sale['code']:<5} | {prod_name.capitalize():<15} | {qty_sold:<8} | Kes {unit_price:<8.2f} | Kes {line_item_total:<10.2f}")

    if transaction_count == 0:
        print(f"[ALERT] No transaction records today. ")

    print(f"\nDAILY REVENUE SUMMARY")
    print(f" Revenue Generated : Kes {daily_sales_revenue:,.2f}")
    print(f" Items sold   : {daily_items_sold_count} units")

    if product_frequency:
        top_product = max(product_frequency, key=product_frequency.get)
        print(f"Top Performing Product of Day  : {top_product.upper()} ({product_frequency[top_product]} units)")
    else:
        print(f"Top Performing Product of Day  : None (No items sold)")

    print(f"\n CRITICAL LOW-STOCK RESTOCK ALERTS (TOP 3)")

    sorted_by_stock = sorted(active_items_list, key=lambda x: x[1]["quantity"])

    top_3_low_stock = sorted_by_stock[:3]

    if top_3_low_stock:
        print(f"  {'Rank':<4} | {'Code':<5} | {'Product Name':<15} | {'Current Stock Level':<20} | {'Status Flag'}")
        for rank, (code, details) in enumerate(top_3_low_stock, start=1):
            current_qty = details["quantity"]

            if current_qty == 0:
                alert_flag = " COMPLETELY CRITICAL OUT OF STOCK"
            elif current_qty <= 15:
                alert_flag = "URGENT RESTOCK REQUIRED"
            else:
                alert_flag = " Stock Healthy (Above threshold)"

            print(
                f"  #{rank:<3} | {code:<5} | {details['name'].capitalize():<15} | {current_qty:<19} units | {alert_flag}")
    else:
        print(f"  No active products found in inventory registers.")


def show_menu():
    while True:
        print("\nWelcome to Crystal General Shop")
        print("---Main Menu ---")
        print("1. View shop's products")
        print("2. Add a product")
        print("3. Remove a product")
        print("4. Results (Search & Low Stock)")
        print("5. Add product to cart(record sale)")
        print("6. Daily sale report")
        print("7. Exit")

        choice = input("\nEnter your choice (1-7): ")

        if choice == "1":
            view_products()
        elif choice == "2":
            add_product()
        elif choice == "3":
            remove_product()
        elif choice == "4":
            results(inventory)
        elif choice == "5":
            add_to_cart()
            view_and_checkout_cart()
        elif choice == "6":
            generate_daily_report()
        elif choice == "7":
            print("Thank you for your time visiting!")
            break
        else:
            print("\nPlease enter a valid choice between 1 and 8.")

if __name__ == "__main__":
    show_menu()