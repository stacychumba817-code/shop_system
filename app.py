from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from forms import ProductForm, AddToCartForm  # Removed LoginForm, RegistrationForm
from datetime import datetime, timedelta
import random
import string

from config import Config
from models import db, User, Product, Sale, SaleItem

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

def generate_invoice_no():
    return 'INV-' + ''.join(random.choices(string.digits, k=8))

def calculate_discounts(cart_items):
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    total_items = sum(item['quantity'] for item in cart_items)
    discount_pct = 0.0
    reasons = []
    if total_items >= 10:
        discount_pct += 5.0
        reasons.append("Bulk Purchase (10+ items)")
        discount_pct += 5.0
        reasons.append("Loyalty Card")
    discount_amount = subtotal * (discount_pct / 100)
    final_total = subtotal - discount_amount
    return subtotal, discount_pct, discount_amount, final_total, reasons

@app.context_processor
def inject_shop_name():
    return dict(SHOP_NAME=Config.SHOP_NAME)

@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    threshold = 10
    products = Product.query.filter_by(active=True)
    low_stock = Product.query.filter(Product.active == True, Product.quantity <= threshold).all()
    if query:
        if query.lower() == 'low':
            products = products.filter(Product.quantity <= threshold)
        else:
            q = f"%{query}%"
            products = products.filter(
                db.or_(Product.code.ilike(q), Product.name.ilike(q), Product.category.ilike(q))
            )
    else:
        products = products.all()
    form = AddToCartForm()
    return render_template('index.html', products=products, low_stock=low_stock,
                           form=form, search_query=query, threshold=threshold)

@app.route('/dashboard')
def dashboard():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    sales_today = Sale.query.filter(Sale.sale_date >= today_start).all()
    total_sales_today = sum(s.final_total for s in sales_today)

    items_sold_today = db.session.query(db.func.sum(SaleItem.quantity)). \
                           join(Sale, Sale.id == SaleItem.sale_id). \
                           filter(Sale.sale_date >= today_start).scalar() or 0

    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)
        daily_total = db.session.query(db.func.sum(Sale.final_total)).filter(
            Sale.sale_date >= start, Sale.sale_date < end
        ).scalar() or 0
        last_7_days.append({'date': day.strftime('%Y-%m-%d'), 'total': daily_total})

    low_stock_count = Product.query.filter(Product.active == True, Product.quantity <= 5).count()
    total_products = Product.query.filter_by(active=True).count()

    return render_template('dashboard.html',
                           total_sales_today=total_sales_today,
                           items_sold_today=items_sold_today,
                           sales_7_days=last_7_days,
                           low_stock_count=low_stock_count,
                           total_products=total_products)

@app.route('/inventory')
def inventory():
    products = Product.query.filter_by(active=True).all()
    return render_template('inventory.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        existing = Product.query.filter_by(code=form.code.data.upper()).first()
        if existing:
            if not existing.active:
                existing.active = True
                existing.quantity = form.quantity.data
                existing.name = form.name.data
                existing.price = form.price.data
                existing.category = form.category.data
                db.session.commit()
                flash(f'Product {existing.code} reactivated.', 'success')
            else:
                existing.quantity += form.quantity.data
                db.session.commit()
                flash(f'Stock for {existing.code} increased by {form.quantity.data}.', 'info')
        else:
            product = Product(
                code=form.code.data.upper(),
                name=form.name.data,
                price=form.price.data,
                category=form.category.data,
                quantity=form.quantity.data,
                active=True
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully.', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_product.html', form=form)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.code = form.code.data.upper()
        product.name = form.name.data
        product.price = form.price.data
        product.category = form.category.data
        product.quantity = form.quantity.data
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit_product.html', form=form, product=product)

@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.active = False
    db.session.commit()
    flash(f'Product {product.code} hidden.', 'warning')
    return redirect(url_for('inventory'))

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

    cart = session.get('cart', {})
    reserved = cart.get(code, {}).get('quantity', 0)
    available = product.quantity - reserved
    if available < qty:
        flash(f'Not enough stock. Only {available} available.', 'danger')
        return redirect(url_for('index'))

    if code in cart:
        cart[code]['quantity'] += qty
    else:
        cart[code] = {
            'name': product.name,
            'price': product.price,
            'quantity': qty,
            'product_id': product.id
        }
    session['cart'] = cart
    session.modified = True
    flash(f'Added {qty} x {product.name} to cart.', 'success')
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<code>', methods=['POST'])
def remove_from_cart(code):
    cart = session.get('cart', {})
    if code in cart:
        del cart[code]
        session['cart'] = cart
        session.modified = True
        flash(f'Removed {code} from cart.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    if not cart:
        return render_template('cart.html', cart={}, subtotal=0, discount_pct=0,
                               discount_amount=0, final_total=0, reasons=[])
    cart_items = list(cart.values())
    subtotal, discount_pct, discount_amount, final_total, reasons = calculate_discounts(cart_items)
    return render_template('cart.html',
                           cart=cart,
                           subtotal=subtotal,
                           discount_pct=discount_pct,
                           discount_amount=discount_amount,
                           final_total=final_total,
                           reasons=reasons)

@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Cart is empty.', 'warning')
        return redirect(url_for('view_cart'))

    cart_items = list(cart.values())
    subtotal, discount_pct, discount_amount, final_total, reasons = calculate_discounts(cart_items)

    # Verify stock again
    for code, item in cart.items():
        product = Product.query.get(item['product_id'])
        if not product or not product.active or product.quantity < item['quantity']:
            flash(f'Stock changed for {item["name"]}. Please update your cart.', 'danger')
            return redirect(url_for('view_cart'))

    invoice_no = generate_invoice_no()
    payment_method = request.form.get('payment_method', 'cash')
    sale = Sale(
        invoice_no=invoice_no,
        user_id=1,
        total_amount=subtotal,
        discount_pct=discount_pct,
        discount_amount=discount_amount,
        final_total=final_total,
        payment_method=payment_method
    )
    db.session.add(sale)
    db.session.flush()

    for code, item in cart.items():
        product = Product.query.get(item['product_id'])
        product.quantity -= item['quantity']
        line_total = item['price'] * item['quantity'] * (1 - discount_pct / 100)
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item['quantity'],
            price=item['price'],
            line_total=line_total
        )
        db.session.add(sale_item)

    db.session.commit()
    session.pop('cart', None)
    flash(f'Checkout successful! Invoice: {invoice_no}, Total: KES {final_total:.2f}', 'success')
    return redirect(url_for('index'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/sales_report')
def sales_report():
    today = datetime.utcnow().date()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            start = datetime(today.year, today.month, today.day)
            end = start + timedelta(days=1)
    else:
        start = datetime(today.year, today.month, today.day)
        end = start + timedelta(days=1)

    sales = Sale.query.filter(Sale.sale_date >= start, Sale.sale_date < end).all()
    total_revenue = sum(s.final_total for s in sales)

    total_items_sold = db.session.query(db.func.sum(SaleItem.quantity)).\
        join(Sale, Sale.id == SaleItem.sale_id).\
        filter(Sale.sale_date >= start, Sale.sale_date < end).scalar() or 0

    top_products = db.session.query(
        Product.name, db.func.sum(SaleItem.quantity).label('total_qty')
    ).join(SaleItem, SaleItem.product_id == Product.id) \
        .join(Sale, Sale.id == SaleItem.sale_id) \
        .filter(Sale.sale_date >= start, Sale.sale_date < end) \
        .group_by(Product.id).order_by(db.func.sum(SaleItem.quantity).desc()).limit(5).all()

    return render_template('sales_report.html',
                           sales=sales,
                           total_revenue=total_revenue,
                           total_items_sold=total_items_sold,
                           top_products=top_products,
                           start_date=start.strftime('%Y-%m-%d'),
                           end_date=(end - timedelta(days=1)).strftime('%Y-%m-%d'))

with app.app_context():
    db.create_all()

    if Product.query.count() == 0:
        sample_products = [
            Product(code='RICE-001', name='Premium Rice (5kg)', price=450.0, category='Food', quantity=50, active=True),
            Product(code='SUGAR-01', name='White Sugar (2kg)', price=220.0, category='Food', quantity=30, active=True),
            Product(code='OIL-001', name='Cooking Oil (1L)', price=350.0, category='Food', quantity=20, active=True),
            Product(code='SODA-01', name='Soda Pack', price=120.0, category='Beverages', quantity=100, active=True),
            Product(code='WATER-01', name='Mineral Water', price=50.0, category='Beverages', quantity=80, active=True),
        ]
        db.session.add_all(sample_products)
        db.session.commit()
        print("Added 5 sample products to the database!")

if __name__ == '__main__':
    app.run(debug=True)