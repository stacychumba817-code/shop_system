import csv
from datetime import datetime

PRODUCTS_FILE = 'products.csv'
SALES_FILE = 'sales.csv'

# Local terminal session state trackers
cart = {}
has_loyalty_card = False


def create_default_products():
    """Writes the starter product database inventory to disk."""
    with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'price', 'stock'])
        writer.writerows([
            ['1', 'Laptop', '999.99', '5'],
            ['2', 'Wireless Mouse', '25.50', '25'],
            ['3', 'Mechanical Keyboard', '75.00', '12']
        ])


def create_default_sales():
    """Writes the starter transaction ledger file to disk."""
    with open(SALES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sale_id', 'timestamp', 'product_id', 'quantity', 'total_price'])


def load_catalog():
    """Reads live product data from the CSV file. Initializes defaults if missing."""
    catalog = {}
    try:
        with open(PRODUCTS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                catalog[row['id']] = {
                    'name': row['name'],
                    'price': float(row['price']),
                    'stock': int(row['stock'])
                }
    except FileNotFoundError:
        create_default_products()
        return load_catalog()
    return catalog


def save_catalog(catalog):
    """Overwrites the product database to save updated stock levels."""
    with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'price', 'stock'])
        for pid, info in catalog.items():
            writer.writerow([pid, info['name'], f"{info['price']:.2f}", info['stock']])


def view_catalog():
    """Prints all active items inside the store database."""
    catalog = load_catalog()
    print("\n--- STORE CATALOG ---")
    print(f"{'ID':<5} {'Item Name':<25} {'Price':<10} {'Stock':<5}")
    print("-" * 50)
    for pid, info in catalog.items():
        print(f"{pid:<5} {info['name']:<25} ${info['price']:<9.2f} {info['stock']:<5}")


def add_catalog_item():
    """Inserts a unique product row into the system catalog mapping."""
    catalog = load_catalog()
    pid = input("Enter new Product ID: ").strip()
    if pid in catalog:
        print("❌ Error: Product ID already exists.")
        return

    name = input("Enter product name: ").strip()
    try:
        price = float(input("Enter unit retail price: $"))
        stock = int(input("Enter starting inventory count: "))

        if price <= 0 or stock < 0:
            print("❌ Error: Price and stock numbers must be positive figures.")
            return

        catalog[pid] = {"name": name, "price": price, "stock": stock}
        save_catalog(catalog)
        print(f"✅ Success: '{name}' added to inventory database.")
    except ValueError:
        print("❌ Error: Invalid numeric input provided.")


def remove_catalog_item():
    """Permanently deletes an entire item classification from storage records."""
    catalog = load_catalog()
    pid = input("Enter Product ID to completely delete: ").strip()
    if pid in catalog:
        deleted_name = catalog[pid]['name']
        del catalog[pid]
        if pid in cart:
            del cart[pid]
        save_catalog(catalog)
        print(f"✅ Success: '{deleted_name}' dropped from catalog database.")
    else:
        print("❌ Error: Product ID not located.")


def search_catalog():
    """Filters product records based on identifier or character sequence matches."""
    catalog = load_catalog()
    query = input("Enter query search term (ID or Name): ").strip().lower()
    print("\n--- SEARCH RESULTS ---")
    found = False
    for pid, info in catalog.items():
        if query in pid.lower() or query in info['name'].lower():
            print(f"[{pid}] {info['name']} - ${info['price']:.2f} ({info['stock']} available)")
            found = True
    if not found:
        print("No items matched your search criteria.")


def add_to_cart():
    """Loops item entry continuously until user inputs 'done'."""
    global cart
    while True:
        catalog = load_catalog()
        view_catalog()
        print("\n(Type 'done' to stop adding items and return to the main menu)")
        pid = input("Enter Product ID to add to cart: ").strip()

        if pid.lower() == 'done':
            print("Returning to main menu.")
            break

        if pid not in catalog:
            print("❌ Error: Unknown product ID selection.\n")
            continue

        # Account for dynamic items already sitting in checkout cart
        available_stock = catalog[pid]['stock'] - cart.get(pid, 0)
        if available_stock <= 0:
            print("❌ Error: Out of stock item allocation failure.\n")
            continue

        try:
            qty = int(input(f"Enter quantity for {catalog[pid]['name']} (Max: {available_stock}): "))
            if qty <= 0:
                print("❌ Error: Cart quantity selection must pass zero thresholds.\n")
                continue
            if qty > available_stock:
                print("❌ Error: Insufficient stock allocation headroom.\n")
                continue

            cart[pid] = cart.get(pid, 0) + qty
            print(f"🛒 Success: Added {qty}x '{catalog[pid]['name']}' to basket.\n")
        except ValueError:
            print("❌ Error: Non-integer numeric quantity choice detected.\n")


def toggle_loyalty():
    """Registers or toggles customer loyalty program profile data status."""
    global has_loyalty_card
    status_input = input("Does the customer have a loyalty card? (yes/no): ").strip().lower()
    if status_input == 'yes':
        has_loyalty_card = True
        print("🎟️ Loyalty card status: Activated.")
    else:
        has_loyalty_card = False
        print("🎟️ Loyalty card status: Deactivated.")


def calculate_totals():
    """Helper logic to compute subtotal, item counts, and dynamic split percentage drops."""
    catalog = load_catalog()
    subtotal = 0.0
    total_items_bought = 0

    for pid, qty in cart.items():
        info = catalog.get(pid)
        subtotal += qty * info['price']
        total_items_bought += qty

    discount_pct = 0.0
    discount_reasons = []

    if total_items_bought >= 10:
        discount_pct += 5.0
        discount_reasons.append("Bulk Purchase (10+ Items)")

    if has_loyalty_card:
        discount_pct += 5.0
        discount_reasons.append("Loyalty Card Member")

    discount_amount = subtotal * (discount_pct / 100)
    final_balance = subtotal - discount_amount

    return subtotal, discount_pct, discount_amount, final_balance, discount_reasons


def view_cart():
    """Renders active cart lists and shows pending calculations."""
    if not cart:
        print("\n🛒 Checkout cart session is currently empty.")
        return

    catalog = load_catalog()
    print("\n--- YOUR SHOPPING CART ---")
    print(f"{'Item Name':<25} {'Qty':<6} {'Unit Price':<12} {'Line Total':<10}")
    print("-" * 55)

    for pid, qty in cart.items():
        info = catalog.get(pid)
        line_total = qty * info['price']
        print(f"{info['name']:<25} x{qty:<5} ${info['price']:<11.2f} ${line_total:.2f}")

    subtotal, discount_pct, discount_amount, final_balance, discount_reasons = calculate_totals()

    print("-" * 55)
    print(f"Cart Gross Subtotal:  ${subtotal:.2f}")
    if discount_amount > 0:
        reason_str = " + ".join(discount_reasons)
        print(f"Pending Discount (-{discount_pct:.1f}%): -${discount_amount:.2f} ({reason_str})")
    print(f"Estimated Total:      ${final_balance:.2f}")


def record_sale():
    """Deducts catalog inventory, generates an invoice, and appends raw rows to sales.csv."""
    global cart, has_loyalty_card
    if not cart:
        print("❌ Error: Cannot record sale on empty checkout terminal session.")
        return

    catalog = load_catalog()
    subtotal, discount_pct, discount_amount, final_balance, discount_reasons = calculate_totals()

    # Custom non-uuid identifier generation using timestamp metrics
    now_obj = datetime.now()
    sale_id = now_obj.strftime("TX%H%M%S")
    timestamp = now_obj.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Update and commit stock alterations back inside database catalog file
    for pid, qty in cart.items():
        catalog[pid]['stock'] -= qty
    save_catalog(catalog)

    # 2. Append rows directly into sales transaction log CSV database
    try:
        f = open(SALES_FILE, 'r', newline='', encoding='utf-8')
        f.close()
    except FileNotFoundError:
        create_default_sales()

    with open(SALES_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for pid, qty in cart.items():
            info = catalog.get(pid)
            raw_line_total = qty * info['price']
            # Compute real line cost breakdown relative to applied card markdown splits
            line_discount_share = raw_line_total * (discount_pct / 100)
            final_line_price = raw_line_total - line_discount_share

            writer.writerow([sale_id, timestamp, pid, qty, f"{final_line_price:.2f}"])

    # 3. Print terminal screen readout summary sheet
    print("\n" + "#" * 20 + " TRANSACTION RECORDED " + "#" * 20)
    print(f"Invoice Sale ID: {sale_id}")
    print(f"Log Destination: {SALES_FILE}")
    print(f"Gross Subtotal:  ${subtotal:.2f}")
    if discount_amount > 0:
        print(f"Total Discounts: -${discount_amount:.2f} ({' + '.join(discount_reasons)})")
    print(f"NET CASH PAID:   ${final_balance:.2f}")
    print("#" * 58 + "\n")

    # Clear memory fields to register the next user ticket assignment
    cart = {}
    has_loyalty_card = False


