from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Product, Sale
import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ---------- Helper Functions ----------
def get_cart():
    """Retrieve cart from session; each item: {code, name, price, quantity}"""
    return session.get('cart', {})

def save_cart(cart):
    session['cart'] = cart
    session.modified = True

def clear_cart():
    session.pop('cart', None)

# ---------- Routes ----------
@app.route('/')
def index():
    # Show all active products
    products = Product.query.filter_by(active=True).all()
    return render_template('index.html', products=products)

@app.route('/product/<code>')
def product_detail(code):
    product = Product.query.get_or_404(code)
    return render_template('product_detail.html', product=product)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        code = request.form['code'].upper().strip()
        name = request.form['name'].strip()
        price = float(request.form['price'])
        category = request.form['category'].strip()
        quantity = int(request.form['quantity'])

        product = Product.query.get(code)
        if product:
            if not product.active:
                # Restore deleted product
                product.active = True
                product.quantity = quantity
                product.name = name
                product.price = price
                product.category = category
                flash(f'Product {code} reactivated and restocked.', 'success')
            else:
                # Add to existing stock
                product.quantity += quantity
                flash(f'Stock for {code} increased by {quantity}.', 'info')
        else:
            new_product = Product(
                code=code, name=name, price=price,
                category=category, quantity=quantity, active=True
            )
            db.session.add(new_product)
            flash(f'Product {code} added successfully.', 'success')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/remove_product/<code>', methods=['POST'])
def remove_product(code):
    product = Product.query.get_or_404(code)
    if product.active:
        product.active = False
        db.session.commit()
        flash(f'Product {code} removed (hidden).', 'warning')
    else:
        flash('Product already removed.', 'info')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    threshold = 15
    products = []
    low_stock_products = []

    if query.lower() == 'low':
        low_stock_products = Product.query.filter(
            Product.active == True,
            Product.quantity <= threshold
        ).all()
    elif query:
        # Search by code, name, or category
        products = Product.query.filter(
            Product.active == True,
            (Product.code.ilike(f'%{query}%') |
             Product.name.ilike(f'%{query}%') |
             Product.category.ilike(f'%{query}%'))
        ).all()
    else:
        products = Product.query.filter_by(active=True).all()

    return render_template('index.html',
                           products=products,
                           search_query=query,
                           low_stock_products=low_stock_products,
                           threshold=threshold)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    code = request.form['code'].upper().strip()
    product = Product.query.filter_by(code=code, active=True).first()
    if not product:
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

    # Check if enough stock (including current cart reservations)
    cart = get_cart()
    reserved = cart.get(code, {}).get('quantity', 0)
    if product.quantity - reserved < qty:
        flash(f'Not enough stock. Only {product.quantity - reserved} available.', 'danger')
        return redirect(url_for('index'))

    # Update cart
    if code in cart:
        cart[code]['quantity'] += qty
    else:
        cart[code] = {
            'name': product.name,
            'price': product.price,
            'quantity': qty
        }
    save_cart(cart)
    flash(f'Added {qty} x {product.name} to cart.', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def view_cart():
    cart = get_cart()
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    cart = get_cart()
    if not cart:
        flash('Cart is empty.', 'warning')
        return redirect(url_for('cart'))

    today_str = datetime.date.today().strftime('%d/%m/%Y')
    # Process each item
    for code, item in cart.items():
        product = Product.query.get(code)
        if not product or product.quantity < item['quantity']:
            flash(f'Stock changed for {item["name"]}. Please update your cart.', 'danger')
            return redirect(url_for('cart'))
        # Deduct stock
        product.quantity -= item['quantity']
        # Record sale
        sale = Sale(
            date=today_str,
            code=code,
            name=item['name'],
            quantity_sold=item['quantity'],
            price=item['price']
        )
        db.session.add(sale)

    db.session.commit()
    clear_cart()
    flash('Checkout successful!', 'success')
    return redirect(url_for('index'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart_route():
    clear_cart()
    flash('Cart cleared.', 'info')
    return redirect(url_for('cart'))

@app.route('/report')
def daily_report():
    today_str = datetime.date.today().strftime('%d/%m/%Y')
    sales_today = Sale.query.filter_by(date=today_str).all()
    # Total revenue
    total_revenue = sum(s.total for s in sales_today)
    total_items = sum(s.quantity_sold for s in sales_today)
    # Top product
    freq = {}
    for sale in sales_today:
        freq[sale.name] = freq.get(sale.name, 0) + sale.quantity_sold
    top_product = max(freq.items(), key=lambda x: x[1]) if freq else None

    # Low stock products (top 3)
    low_stock = Product.query.filter(
        Product.active == True,
        Product.quantity <= 15
    ).order_by(Product.quantity).limit(3).all()

    # Total inventory value
    total_value = db.session.query(db.func.sum(Product.price * Product.quantity)).filter_by(active=True).scalar() or 0.0

    return render_template('report.html',
                           sales=sales_today,
                           total_revenue=total_revenue,
                           total_items=total_items,
                           top_product=top_product,
                           low_stock=low_stock,
                           total_value=total_value,
                           shop_name='CRYSTAL GENERAL SHOP',
                           date=today_str)

# ---------- Init Database ----------
with app.app_context():
    db.create_all()
    # Seed some initial products if empty
    if not Product.query.first():
        products = [
            Product(code='A', name='rice', price=120.0, category='grain', quantity=55),
            Product(code='B', name='sugar', price=160.0, category='food', quantity=31),
            Product(code='C', name='beans', price=150.0, category='cereal', quantity=50),
            Product(code='D', name='bread', price=120.0, category='whole foods', quantity=30),
            Product(code='E', name='bar soap', price=180.0, category='cleaning product', quantity=15),
        ]
        db.session.add_all(products)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
