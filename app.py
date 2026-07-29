from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, HiddenField
from wtforms.validators import DataRequired, NumberRange
import datetime

app = Flask(__name__)
app.secret_key = 'change-this-secret-key-in-production'

SHOP_NAME = "CRYSTAL GENERAL SHOP"


# --- Auto-inject SHOP_NAME into every HTML template ---
@app.context_processor
def inject_shop_name():
    return dict(SHOP_NAME=SHOP_NAME)


inventory = {
    "A": {"name": "rice", "price": 120.00, "category": "grain", "quantity": 55, "active": True},
    "B": {"name": "sugar", "price": 160.00, "category": "food", "quantity": 31, "active": True},
    "C": {"name": "beans", "price": 150.00, "category": "cereal", "quantity": 50, "active": True},
    "D": {"name": "bread", "price": 120.00, "category": "whole foods", "quantity": 30, "active": True},
    "E": {"name": "bar soap", "price": 180.00, "category": "cleaning product", "quantity": 15, "active": True},
}

sales_history = []


# --- WTForms ---
class AddProductForm(FlaskForm):
    code = StringField('Product Code', validators=[DataRequired()])
    name = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price (KES)', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])


class AddToCartForm(FlaskForm):
    code = HiddenField('Code', validators=[DataRequired()])
    quantity = IntegerField('Qty', validators=[DataRequired(), NumberRange(min=1)])


# --- Discount logic (bulk + loyalty) ---
def calculate_discounts(cart):
    """
    Returns (subtotal, discount_pct, discount_amount, final_total, reasons)
    """
    subtotal = 0.0
    total_items = 0

    for code, item in cart.items():
        subtotal += item['price'] * item['quantity']
        total_items += item['quantity']

    discount_pct = 0.0
    reasons = []

    # Bulk discount: 5% if 10 or more items
    if total_items >= 10:
        discount_pct += 5.0
        reasons.append("Bulk Purchase (10+ items)")

    # Loyalty discount: 5% if loyalty card is active
    if session.get('loyalty', False):
        discount_pct += 5.0
        reasons.append("Loyalty Card")

    discount_amount = subtotal * (discount_pct / 100)
    final_total = subtotal - discount_amount

    return subtotal, discount_pct, discount_amount, final_total, reasons


@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    threshold = 10
    products = []
    low_stock_products = []
    form = AddToCartForm()

    if query.lower() == 'low':
        low_stock_products = [(k, v) for k, v in inventory.items() if v['active'] and v['quantity'] <= threshold]
        products = [(k, v) for k, v in inventory.items() if v['active']]
    elif query:
        q = query.lower()
        for code, details in inventory.items():
            if details['active']:
                if q in code.lower() or q in details['name'].lower() or q in details['category'].lower():
                    products.append((code, details))
    else:
        products = [(k, v) for k, v in inventory.items() if v['active']]

    return render_template('index.html', products=products, low_stock_products=low_stock_products,
                           form=form, search_query=query, threshold=threshold)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        code = form.code.data.upper().strip()
        name = form.name.data.strip()
        price = form.price.data
        category = form.category.data.strip()
        quantity = form.quantity.data

        if code in inventory:
            if not inventory[code]["active"]:
                # Reactivate and restock
                inventory[code]["active"] = True
                inventory[code]["quantity"] = quantity
                inventory[code]["name"] = name
                inventory[code]["price"] = price
                inventory[code]["category"] = category
                flash(f'Product {code} reactivated and restocked.', 'success')
            else:
                inventory[code]["quantity"] += quantity
                flash(f'Stock for {code} increased by {quantity}.', 'info')
        else:
            inventory[code] = {
                "name": name,
                "price": price,
                "category": category,
                "quantity": quantity,
                "active": True
            }
            flash(f'Product {code} added successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('add_product.html', form=form)


@app.route('/remove_product/<code>', methods=['POST'])
def remove_product(code):
    if code in inventory and inventory[code]["active"]:
        inventory[code]["active"] = False
        flash(f'Product {code} removed (hidden).', 'warning')
    else:
        flash('Product already removed or not found.', 'info')
    return redirect(url_for('index'))


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    code = request.form['code'].upper().strip()
    product = inventory.get(code)

    if not product or not product['active']:
        flash('Product not found or inactive.', 'danger')
        return redirect(url_for('index'))

    try:
        qty = int(request.form['quantity'])
    except ValueError:
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('index'))

    if qty <= 0:
        flash('Quantity must be positive.', 'danger')
        return redirect(url_for('index'))

    cart = session.get('cart', {})
    reserved = cart.get(code, {}).get('quantity', 0)
    available_stock = product['quantity'] - reserved

    if available_stock < qty:
        flash(f'Not enough stock. Only {available_stock} available.', 'danger')
        return redirect(url_for('index'))

    if code in cart:
        cart[code]['quantity'] += qty
    else:
        cart[code] = {
            'name': product['name'],
            'price': product['price'],
            'quantity': qty
        }

    session['cart'] = cart
    session.modified = True
    flash(f'Added {qty} x {product["name"]} to cart.', 'success')
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<code>', methods=['POST'])
def remove_from_cart(code):
    cart = session.get('cart', {})
    if code in cart:
        del cart[code]
        session['cart'] = cart
        session.modified = True
        flash(f'Removed {code} from cart.', 'info')
    else:
        flash('Item not found in cart.', 'warning')
    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    if not cart:
        return render_template('cart.html', cart={}, total=0, discount_pct=0,
                               discount_amount=0, discounted_total=0, reasons=[])

    subtotal, discount_pct, discount_amount, final_total, reasons = calculate_discounts(cart)
    return render_template('cart.html',
                           cart=cart,
                           subtotal=subtotal,
                           discount_pct=discount_pct,
                           discount_amount=discount_amount,
                           discounted_total=final_total,
                           reasons=reasons,
                           loyalty=session.get('loyalty', False))


@app.route('/toggle_loyalty', methods=['POST'])
def toggle_loyalty():
    current = session.get('loyalty', False)
    session['loyalty'] = not current
    status = "activated" if session['loyalty'] else "deactivated"
    flash(f'Loyalty card {status}.', 'info')
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Cart is empty.', 'warning')
        return redirect(url_for('view_cart'))

    today_str = datetime.date.today().strftime('%d/%m/%Y')

    subtotal, discount_pct, discount_amount, final_total, reasons = calculate_discounts(cart)

    for code, item in cart.items():
        product = inventory.get(code)
        if not product or not product['active'] or product['quantity'] < item['quantity']:
            flash(f'Stock changed for {item["name"]}. Please update your cart.', 'danger')
            return redirect(url_for('view_cart'))

        product['quantity'] -= item['quantity']

        line_subtotal = item['price'] * item['quantity']
        line_discount = line_subtotal * (discount_pct / 100)
        line_final = line_subtotal - line_discount

        sale_entry = {
            "date": today_str,
            "code": code,
            "name": item['name'],
            "quantity_sold": item['quantity'],
            "price": item['price'],
            "discount_applied": discount_pct,
            "line_total": line_final
        }
        sales_history.append(sale_entry)

    session.pop('cart', None)
    session.pop('loyalty', None)
    flash(f'Checkout successful! Total: ${final_total:.2f}', 'success')
    return redirect(url_for('index'))


@app.route('/clear_cart', methods=['POST'])
def clear_cart_route():
    session.pop('cart', None)
    flash('Cart cleared.', 'info')
    return redirect(url_for('view_cart'))


@app.route('/report')
def daily_report():
    today_str = datetime.date.today().strftime('%d/%m/%Y')

    total_inventory_value = 0.0
    active_items = []
    for code, details in inventory.items():
        if details['active']:
            total_inventory_value += details['price'] * details['quantity']
            active_items.append((code, details))

    today_sales = [sale for sale in sales_history if sale['date'] == today_str]
    total_revenue = sum(s['line_total'] for s in today_sales)   # use line_total (discounted)
    total_items_sold = sum(s['quantity_sold'] for s in today_sales)

    freq = {}
    for sale in today_sales:
        freq[sale['name']] = freq.get(sale['name'], 0) + sale['quantity_sold']
    top_product = max(freq.items(), key=lambda x: x[1]) if freq else None

    sorted_active = sorted(active_items, key=lambda x: x[1]['quantity'])
    low_stock_alert = sorted_active[:3]

    return render_template('report.html',
                           active_count=len(active_items),
                           total_inventory_value=total_inventory_value,
                           total_revenue=total_revenue,
                           total_items_sold=total_items_sold,
                           top_product=top_product,
                           low_stock_alert=low_stock_alert,
                           date=today_str)


if __name__ == '__main__':
    app.run(debug=True)