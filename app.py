from flask import abort
from flask import request
from flask import render_template_string

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import check_password_hash

from database import get_db_connection, create_tables

import os


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-only-change-this-key"
)


# DATABASE
create_tables()


# LOGIN MANAGER
login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


# ADMIN CLASS
class Admin(UserMixin):

    def __init__(self, admin_id, username):

        self.id = str(admin_id)

        self.username = username


@login_manager.user_loader
def load_user(user_id):

    conn = get_db_connection()

    admin = conn.execute(
        "SELECT * FROM admin WHERE admin_id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    if admin:

        return Admin(
            admin["admin_id"],
            admin["username"]
        )

    return None


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()

        password = request.form.get("password", "")

        conn = get_db_connection()

        admin = conn.execute(
            "SELECT * FROM admin WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if admin and check_password_hash(
            admin["password"], password
        ):

            user = Admin(
                admin["admin_id"],
                admin["username"]
            )

            login_user(user)

            return redirect(url_for("dashboard"))

        flash("Invalid username or password!", "danger")

    return render_template("login.html")


# DASHBOARD
@app.route("/")
@login_required
def dashboard():

    conn = get_db_connection()

    total_products = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    total_customers = conn.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    total_sales = conn.execute(
        "SELECT COUNT(*) FROM sales"
    ).fetchone()[0]

    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM sales"
    ).fetchone()[0]

    low_stock = conn.execute(
        """
        SELECT COUNT(*) FROM products
        WHERE quantity <= minimum_stock
        """
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_customers=total_customers,
        total_sales=total_sales,
        total_revenue=total_revenue,
        low_stock=low_stock
    )


# =================================
# PRODUCT MANAGEMENT
# =================================


# VIEW PRODUCTS
@app.route("/products")
@login_required
def products():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search:

        product_list = conn.execute(
            """
            SELECT * FROM products
            WHERE product_name LIKE ?
            OR category LIKE ?
            ORDER BY product_id DESC
            """,
            (f"%{search}%", f"%{search}%")
        ).fetchall()

    else:

        product_list = conn.execute(
            "SELECT * FROM products ORDER BY product_id DESC"
        ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=product_list,
        search=search
    )


# ADD PRODUCT
@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():

    if request.method == "POST":

        product_name = request.form.get(
            "product_name", ""
        ).strip()

        category = request.form.get(
            "category", ""
        ).strip()

        purchase_price = request.form.get(
            "purchase_price", ""
        )

        selling_price = request.form.get(
            "selling_price", ""
        )

        quantity = request.form.get(
            "quantity", ""
        )

        minimum_stock = request.form.get(
            "minimum_stock", ""
        )

        try:

            purchase_price = float(purchase_price)

            selling_price = float(selling_price)

            quantity = int(quantity)

            minimum_stock = int(minimum_stock)

            if not product_name:
                raise ValueError("Product name is required.")

            if (
                purchase_price < 0
                or selling_price < 0
                or quantity < 0
                or minimum_stock < 0
            ):
                raise ValueError("Values cannot be negative.")

            if selling_price < purchase_price:

                flash(
                    "Warning: Selling price is lower than purchase price.",
                    "warning"
                )

            conn = get_db_connection()

            cursor = conn.execute(
                """
                INSERT INTO products
                (
                    product_name,
                    category,
                    purchase_price,
                    selling_price,
                    quantity,
                    minimum_stock
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_name,
                    category,
                    purchase_price,
                    selling_price,
                    quantity,
                    minimum_stock
                )
            )

            product_id = cursor.lastrowid

            conn.execute(
                """
                INSERT INTO stock_history
                (product_id, change_type, quantity, note)
                VALUES (?, ?, ?, ?)
                """,
                (
                    product_id,
                    "IN",
                    quantity,
                    "Initial stock added"
                )
            )

            conn.commit()

            conn.close()

            flash("Product added successfully!", "success")

            return redirect(url_for("products"))

        except ValueError as error:

            flash(str(error), "danger")

        except Exception:

            flash(
                "Unable to add product. Please check your entries.",
                "danger"
            )

    return render_template("add_product.html")


# EDIT PRODUCT
@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):

    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE product_id = ?",
        (product_id,)
    ).fetchone()

    if product is None:

        conn.close()

        flash("Product not found!", "danger")

        return redirect(url_for("products"))

    if request.method == "POST":

        try:

            product_name = request.form.get(
                "product_name", ""
            ).strip()

            category = request.form.get(
                "category", ""
            ).strip()

            purchase_price = float(
                request.form.get("purchase_price", "")
            )

            selling_price = float(
                request.form.get("selling_price", "")
            )

            quantity = int(
                request.form.get("quantity", "")
            )

            minimum_stock = int(
                request.form.get("minimum_stock", "")
            )

            if not product_name:
                raise ValueError("Product name is required.")

            if (
                purchase_price < 0
                or selling_price < 0
                or quantity < 0
                or minimum_stock < 0
            ):
                raise ValueError("Values cannot be negative.")

            old_quantity = product["quantity"]

            conn.execute(
                """
                UPDATE products

                SET product_name = ?,
                    category = ?,
                    purchase_price = ?,
                    selling_price = ?,
                    quantity = ?,
                    minimum_stock = ?

                WHERE product_id = ?
                """,
                (
                    product_name,
                    category,
                    purchase_price,
                    selling_price,
                    quantity,
                    minimum_stock,
                    product_id
                )
            )

            difference = quantity - old_quantity

            if difference != 0:

                change_type = (
                    "IN" if difference > 0 else "OUT"
                )

                conn.execute(
                    """
                    INSERT INTO stock_history
                    (product_id, change_type, quantity, note)

                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        change_type,
                        abs(difference),
                        "Stock adjusted during product update"
                    )
                )

            conn.commit()

            conn.close()

            flash("Product updated successfully!", "success")

            return redirect(url_for("products"))

        except ValueError as error:

            flash(str(error), "danger")

        except Exception:

            flash("Unable to update product.", "danger")

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )


# DELETE PRODUCT
@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):

    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE product_id = ?",
        (product_id,)
    ).fetchone()

    if product is None:

        conn.close()

        flash("Product not found!", "danger")

        return redirect(url_for("products"))

    used_in_sales = conn.execute(
        """
        SELECT COUNT(*)
        FROM sale_items
        WHERE product_id = ?
        """,
        (product_id,)
    ).fetchone()[0]

    if used_in_sales > 0:

        conn.close()

        flash(
            "This product is linked to sales and cannot be deleted.",
            "warning"
        )

        return redirect(url_for("products"))

    conn.execute(
        "DELETE FROM stock_history WHERE product_id = ?",
        (product_id,)
    )

    conn.execute(
        "DELETE FROM products WHERE product_id = ?",
        (product_id,)
    )

    conn.commit()

    conn.close()

    flash("Product deleted successfully!", "success")

    return redirect(url_for("products"))

# =================================
# INVENTORY MANAGEMENT
# =================================

@app.route("/inventory")
@login_required
def inventory():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search:

        products = conn.execute(
            """
            SELECT * FROM products

            WHERE product_name LIKE ?
            OR category LIKE ?

            ORDER BY product_name
            """,
            (f"%{search}%", f"%{search}%")
        ).fetchall()

    else:

        products = conn.execute(
            """
            SELECT * FROM products
            ORDER BY product_name
            """
        ).fetchall()

    total_products = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    total_stock = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM products"
    ).fetchone()[0]

    low_stock = conn.execute(
        """
        SELECT COUNT(*) FROM products
        WHERE quantity <= minimum_stock
        """
    ).fetchone()[0]

    out_of_stock = conn.execute(
        """
        SELECT COUNT(*) FROM products
        WHERE quantity = 0
        """
    ).fetchone()[0]

    stock_value = conn.execute(
        """
        SELECT COALESCE(SUM(quantity * purchase_price), 0)
        FROM products
        """
    ).fetchone()[0]

    conn.close()

    return render_template(
        "inventory.html",
        products=products,
        search=search,
        total_products=total_products,
        total_stock=total_stock,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        stock_value=stock_value
    )

@app.route(
    "/stock/<int:product_id>",
    methods=["GET", "POST"]
)
@login_required
def stock_update(product_id):

    conn = get_db_connection()

    product = conn.execute(
        """
        SELECT * FROM products
        WHERE product_id = ?
        """,
        (product_id,)
    ).fetchone()

    if product is None:

        conn.close()

        flash("Product not found!", "danger")

        return redirect(url_for("inventory"))

    if request.method == "POST":

        change_type = request.form.get("change_type")

        note = request.form.get("note", "").strip()

        try:

            quantity = int(request.form.get("quantity", ""))

            if quantity <= 0:

                raise ValueError(
                    "Quantity must be greater than zero."
                )

            if change_type not in ["IN", "OUT"]:

                raise ValueError(
                    "Invalid stock operation."
                )

            if change_type == "IN":

                conn.execute(
                    """
                    UPDATE products

                    SET quantity = quantity + ?

                    WHERE product_id = ?
                    """,
                    (quantity, product_id)
                )

            else:

                cursor = conn.execute(
                    """
                    UPDATE products

                    SET quantity = quantity - ?

                    WHERE product_id = ?
                    AND quantity >= ?
                    """,
                    (quantity, product_id, quantity)
                )

                if cursor.rowcount == 0:

                    raise ValueError(
                        "Insufficient stock available!"
                    )

            conn.execute(
                """
                INSERT INTO stock_history

                (
                    product_id,
                    change_type,
                    quantity,
                    note
                )

                VALUES (?, ?, ?, ?)
                """,
                (
                    product_id,
                    change_type,
                    quantity,
                    note
                )
            )

            conn.commit()

            flash(
                "Inventory updated successfully!",
                "success"
            )

            conn.close()

            return redirect(url_for("inventory"))

        except ValueError as error:

            conn.rollback()

            flash(str(error), "danger")

        except Exception:

            conn.rollback()

            flash(
                "Something went wrong while updating stock.",
                "danger"
            )

    conn.close()

    return render_template(
        "stock_update.html",
        product=product
    )

@app.route("/stock-history")
@login_required
def stock_history():

    conn = get_db_connection()

    history = conn.execute(
        """
        SELECT

            stock_history.history_id,

            products.product_name,

            stock_history.change_type,

            stock_history.quantity,

            stock_history.note,

            stock_history.created_at

        FROM stock_history

        JOIN products

        ON stock_history.product_id =
           products.product_id

        ORDER BY stock_history.history_id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "stock_history.html",
        history=history
    )

@app.route("/new-sale", methods=["GET", "POST"])
@login_required
def new_sale():

    conn = get_db_connection()

    customers = conn.execute("""
        SELECT customer_id, customer_name
        FROM customers
        ORDER BY customer_name
    """).fetchall()

    products = conn.execute("""
        SELECT product_id, product_name,
               selling_price, purchase_price, quantity
        FROM products
        WHERE quantity > 0
        ORDER BY product_name
    """).fetchall()

    conn.close()

    if request.method == "POST":

        try:

            customer_id = int(
                request.form.get("customer_id", "")
            )

            product_ids = request.form.getlist("product_id[]")

            quantities = request.form.getlist("quantity[]")

            discount = float(
                request.form.get("discount", 0)
            )

            tax_rate = float(
                request.form.get("tax_rate", 0)
            )

            payment_method = request.form.get(
                "payment_method", ""
            )

            if not product_ids:
                raise ValueError("Please select a product.")

            if len(product_ids) != len(quantities):
                raise ValueError("Invalid product quantities.")

            if discount < 0 or tax_rate < 0 or tax_rate > 100:
                raise ValueError("Invalid discount or tax rate.")

            if payment_method not in [
                "Cash", "UPI", "Card", "Bank Transfer"
            ]:
                raise ValueError("Invalid payment method.")

            # Combine duplicate product entries
            cart = {}

            for pid, qty in zip(product_ids, quantities):

                pid = int(pid)
                qty = int(qty)

                if pid <= 0 or qty <= 0:
                    raise ValueError("Invalid product or quantity.")

                cart[pid] = cart.get(pid, 0) + qty

            conn = get_db_connection()

            # Begin one transaction for the entire sale
            conn.execute("BEGIN IMMEDIATE")

            customer = conn.execute("""
                SELECT customer_id
                FROM customers
                WHERE customer_id = ?
            """, (customer_id,)).fetchone()

            if customer is None:
                raise ValueError("Customer not found.")

            cart_items = []

            subtotal = 0

            total_profit = 0

            for product_id, quantity in cart.items():

                product = conn.execute("""
                    SELECT *
                    FROM products
                    WHERE product_id = ?
                """, (product_id,)).fetchone()

                if product is None:
                    raise ValueError("Product not found.")

                if product["quantity"] < quantity:
                    raise ValueError(
                        f"Insufficient stock for {product['product_name']}."
                    )

                unit_price = float(product["selling_price"])

                purchase_price = float(product["purchase_price"])

                item_total = unit_price * quantity

                item_profit = (
                    unit_price - purchase_price
                ) * quantity

                subtotal += item_total

                total_profit += item_profit

                cart_items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "purchase_price": purchase_price,
                    "subtotal": item_total
                })

            if discount > subtotal:
                raise ValueError(
                    "Discount cannot exceed subtotal."
                )

            taxable_amount = subtotal - discount

            tax_amount = taxable_amount * tax_rate / 100

            grand_total = taxable_amount + tax_amount

            # Insert sale record
            cursor = conn.execute("""
                INSERT INTO sales
                (
                    customer_id,
                    subtotal,
                    discount,
                    tax_amount,
                    total_amount,
                    payment_method
                )

                VALUES (?, ?, ?, ?, ?, ?)

            """, (
                customer_id,
                subtotal,
                discount,
                tax_amount,
                grand_total,
                payment_method
            ))

            sale_id = cursor.lastrowid

            # Insert sale items and update stock
            for item in cart_items:

                conn.execute("""
                    INSERT INTO sale_items
                    (
                        sale_id,
                        product_id,
                        quantity,
                        unit_price,
                        purchase_price,
                        subtotal
                    )

                    VALUES (?, ?, ?, ?, ?, ?)

                """, (
                    sale_id,
                    item["product_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["purchase_price"],
                    item["subtotal"]
                ))

                cursor = conn.execute("""
                    UPDATE products

                    SET quantity = quantity - ?

                    WHERE product_id = ?
                    AND quantity >= ?

                """, (
                    item["quantity"],
                    item["product_id"],
                    item["quantity"]
                ))

                if cursor.rowcount != 1:
                    raise ValueError(
                        "Stock changed. Please try again."
                    )

                conn.execute("""
                    INSERT INTO stock_history
                    (
                        product_id,
                        change_type,
                        quantity,
                        note
                    )

                    VALUES (?, 'OUT', ?, ?)

                """, (
                    item["product_id"],
                    item["quantity"],
                    f"Sale ID: {sale_id}"
                ))

            conn.commit()

            conn.close()

            flash("Sale completed successfully!", "success")

            return redirect(
                url_for("invoice", sale_id=sale_id)
            )

        except ValueError as error:

            if "conn" in locals():
                conn.rollback()
                conn.close()

            flash(str(error), "danger")

        except Exception:

            if "conn" in locals():
                conn.rollback()
                conn.close()

            flash(
                "Unable to complete sale. Please check database configuration.",
                "danger"
            )

    return render_template(
        "new_sale.html",
        customers=customers,
        products=products
    )

@app.route("/invoice/<int:sale_id>")
@login_required
def invoice(sale_id):

    conn = get_db_connection()

    sale = conn.execute("""
        SELECT
            sales.*,
            customers.customer_name

        FROM sales

        LEFT JOIN customers

        ON sales.customer_id = customers.customer_id

        WHERE sales.sale_id = ?

    """, (sale_id,)).fetchone()

    if sale is None:

        conn.close()

        abort(404)

    items = conn.execute("""
        SELECT
            sale_items.*,
            products.product_name

        FROM sale_items

        JOIN products

        ON sale_items.product_id = products.product_id

        WHERE sale_items.sale_id = ?

    """, (sale_id,)).fetchall()

    conn.close()

    return render_template(
        "invoice.html",
        sale=sale,
        items=items
    )

# =================================
# SALES MANAGEMENT
# =================================

@app.route("/sales")
@login_required
def sales():

    conn = get_db_connection()

    sales_list = conn.execute("""
        SELECT

            sales.sale_id,

            customers.customer_name,

            sales.subtotal,

            sales.discount,

            sales.tax_amount,

            sales.total_amount,

            sales.payment_method,

            sales.sale_date

        FROM sales

        LEFT JOIN customers

        ON sales.customer_id = customers.customer_id

        ORDER BY sales.sale_id DESC

    """).fetchall()

    total_sales = conn.execute("""
        SELECT COUNT(*) FROM sales
    """).fetchone()[0]

    total_revenue = conn.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales
    """).fetchone()[0]

    conn.close()

    return render_template(
        "sales.html",
        sales=sales_list,
        total_sales=total_sales,
        total_revenue=total_revenue
    )

# =================================
# CUSTOMER MANAGEMENT
# =================================

@app.route("/customers")
@login_required
def customers():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search:

        customer_list = conn.execute("""
            SELECT *
            FROM customers

            WHERE customer_name LIKE ?
            OR phone LIKE ?
            OR email LIKE ?

            ORDER BY customer_id DESC

        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        customer_list = conn.execute("""
            SELECT *
            FROM customers
            ORDER BY customer_id DESC
        """).fetchall()

    total_customers = conn.execute("""
        SELECT COUNT(*)
        FROM customers
    """).fetchone()[0]

    conn.close()

    return render_template(
        "customers.html",
        customers=customer_list,
        total_customers=total_customers,
        search=search
    )

@app.route("/add-customer", methods=["GET", "POST"])
@login_required
def add_customer():

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name", ""
        ).strip()

        phone = request.form.get(
            "phone", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        address = request.form.get(
            "address", ""
        ).strip()

        if not customer_name:

            flash("Customer name is required!", "danger")

            return redirect(url_for("add_customer"))

        if len(phone) > 20:

            flash("Phone number is too long!", "danger")

            return redirect(url_for("add_customer"))

        if email and (
            "@" not in email or "." not in email.split("@")[-1]
        ):

            flash("Please enter a valid email!", "danger")

            return redirect(url_for("add_customer"))

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO customers
            (
                customer_name,
                phone,
                email,
                address
            )

            VALUES (?, ?, ?, ?)

        """, (
            customer_name,
            phone,
            email,
            address
        ))

        conn.commit()

        conn.close()

        flash(
            "Customer added successfully!",
            "success"
        )

        return redirect(url_for("customers"))

    return render_template("add_customer.html")

@app.route(
    "/edit-customer/<int:customer_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_customer(customer_id):

    conn = get_db_connection()

    customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE customer_id = ?
    """, (customer_id,)).fetchone()

    if customer is None:

        conn.close()

        abort(404)

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name", ""
        ).strip()

        phone = request.form.get(
            "phone", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        address = request.form.get(
            "address", ""
        ).strip()

        if not customer_name:

            flash("Customer name is required!", "danger")

            conn.close()

            return redirect(
                url_for(
                    "edit_customer",
                    customer_id=customer_id
                )
            )

        if email and (
            "@" not in email or "." not in email.split("@")[-1]
        ):

            flash("Please enter a valid email!", "danger")

            conn.close()

            return redirect(
                url_for(
                    "edit_customer",
                    customer_id=customer_id
                )
            )

        conn.execute("""
            UPDATE customers

            SET
                customer_name = ?,
                phone = ?,
                email = ?,
                address = ?

            WHERE customer_id = ?

        """, (
            customer_name,
            phone,
            email,
            address,
            customer_id
        ))

        conn.commit()

        conn.close()

        flash(
            "Customer updated successfully!",
            "success"
        )

        return redirect(url_for("customers"))

    conn.close()

    return render_template(
        "edit_customer.html",
        customer=customer
    )

@app.route(
    "/delete-customer/<int:customer_id>",
    methods=["POST"]
)
@login_required
def delete_customer(customer_id):

    conn = get_db_connection()

    customer = conn.execute("""
        SELECT customer_id
        FROM customers
        WHERE customer_id = ?
    """, (customer_id,)).fetchone()

    if customer is None:

        conn.close()

        abort(404)

    sales_count = conn.execute("""
        SELECT COUNT(*)
        FROM sales
        WHERE customer_id = ?
    """, (customer_id,)).fetchone()[0]

    if sales_count > 0:

        conn.close()

        flash(
            "Cannot delete customer because sales records exist.",
            "danger"
        )

        return redirect(url_for("customers"))

    conn.execute("""
        DELETE FROM customers
        WHERE customer_id = ?
    """, (customer_id,))

    conn.commit()

    conn.close()

    flash(
        "Customer deleted successfully!",
        "success"
    )

    return redirect(url_for("customers"))

@app.route("/customer-history/<int:customer_id>")
@login_required
def customer_history(customer_id):

    conn = get_db_connection()

    customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE customer_id = ?
    """, (customer_id,)).fetchone()

    if customer is None:

        conn.close()

        abort(404)

    purchase_history = conn.execute("""
        SELECT *

        FROM sales

        WHERE customer_id = ?

        ORDER BY sale_id DESC

    """, (customer_id,)).fetchall()

    total_purchases = conn.execute("""
        SELECT COUNT(*)
        FROM sales
        WHERE customer_id = ?
    """, (customer_id,)).fetchone()[0]

    total_spending = conn.execute("""
        SELECT COALESCE(SUM(total_amount), 0)

        FROM sales

        WHERE customer_id = ?

    """, (customer_id,)).fetchone()[0]

    conn.close()

    return render_template(
        "customer_history.html",
        customer=customer,
        purchases=purchase_history,
        total_purchases=total_purchases,
        total_spending=total_spending
    )

# =================================
# SUPPLIER MANAGEMENT
# =================================

@app.route("/suppliers")
@login_required
def suppliers():

    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search:

        supplier_list = conn.execute("""
            SELECT *
            FROM suppliers

            WHERE supplier_name LIKE ?
            OR company_name LIKE ?
            OR phone LIKE ?
            OR email LIKE ?

            ORDER BY supplier_id DESC

        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        supplier_list = conn.execute("""
            SELECT *
            FROM suppliers
            ORDER BY supplier_id DESC
        """).fetchall()


    total_suppliers = conn.execute("""
        SELECT COUNT(*)
        FROM suppliers
    """).fetchone()[0]


    conn.close()

    return render_template(
        "suppliers.html",
        suppliers=supplier_list,
        total_suppliers=total_suppliers,
        search=search
    )

@app.route("/add-supplier", methods=["GET", "POST"])
@login_required
def add_supplier():

    if request.method == "POST":

        supplier_name = request.form.get(
            "supplier_name", ""
        ).strip()

        company_name = request.form.get(
            "company_name", ""
        ).strip()

        phone = request.form.get(
            "phone", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        address = request.form.get(
            "address", ""
        ).strip()


        if not supplier_name:

            flash(
                "Supplier name is required!",
                "danger"
            )

            return redirect(url_for("add_supplier"))


        if email and (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):

            flash(
                "Please enter a valid email!",
                "danger"
            )

            return redirect(url_for("add_supplier"))


        conn = get_db_connection()

        conn.execute("""
            INSERT INTO suppliers

            (
                supplier_name,
                company_name,
                phone,
                email,
                address
            )

            VALUES (?, ?, ?, ?, ?)

        """, (
            supplier_name,
            company_name,
            phone,
            email,
            address
        ))

        conn.commit()

        conn.close()

        flash(
            "Supplier added successfully!",
            "success"
        )

        return redirect(url_for("suppliers"))


    return render_template("add_supplier.html")

@app.route(
    "/edit-supplier/<int:supplier_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_supplier(supplier_id):

    conn = get_db_connection()

    supplier = conn.execute("""
        SELECT *
        FROM suppliers
        WHERE supplier_id = ?
    """, (supplier_id,)).fetchone()


    if supplier is None:

        conn.close()

        abort(404)


    if request.method == "POST":

        supplier_name = request.form.get(
            "supplier_name", ""
        ).strip()

        company_name = request.form.get(
            "company_name", ""
        ).strip()

        phone = request.form.get(
            "phone", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        address = request.form.get(
            "address", ""
        ).strip()


        if not supplier_name:

            conn.close()

            flash(
                "Supplier name is required!",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_supplier",
                    supplier_id=supplier_id
                )
            )


        if email and (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):

            conn.close()

            flash(
                "Invalid email address!",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_supplier",
                    supplier_id=supplier_id
                )
            )


        conn.execute("""
            UPDATE suppliers

            SET

                supplier_name = ?,
                company_name = ?,
                phone = ?,
                email = ?,
                address = ?

            WHERE supplier_id = ?

        """, (
            supplier_name,
            company_name,
            phone,
            email,
            address,
            supplier_id
        ))


        conn.commit()

        conn.close()

        flash(
            "Supplier updated successfully!",
            "success"
        )

        return redirect(url_for("suppliers"))


    conn.close()

    return render_template(
        "edit_supplier.html",
        supplier=supplier
    )

@app.route(
    "/delete-supplier/<int:supplier_id>",
    methods=["POST"]
)
@login_required
def delete_supplier(supplier_id):

    conn = get_db_connection()

    supplier = conn.execute("""
        SELECT supplier_id
        FROM suppliers
        WHERE supplier_id = ?
    """, (supplier_id,)).fetchone()


    if supplier is None:

        conn.close()

        abort(404)


    purchase_count = conn.execute("""
        SELECT COUNT(*)
        FROM purchases
        WHERE supplier_id = ?
    """, (supplier_id,)).fetchone()[0]


    if purchase_count > 0:

        conn.close()

        flash(
            "Cannot delete supplier with purchase records!",
            "danger"
        )

        return redirect(url_for("suppliers"))


    conn.execute("""
        DELETE FROM suppliers
        WHERE supplier_id = ?
    """, (supplier_id,))


    conn.commit()

    conn.close()

    flash(
        "Supplier deleted successfully!",
        "success"
    )

    return redirect(url_for("suppliers"))

@app.route("/new-purchase", methods=["GET", "POST"])
@login_required
def new_purchase():

    conn = get_db_connection()

    suppliers_list = conn.execute("""
        SELECT *
        FROM suppliers
        ORDER BY supplier_name
    """).fetchall()

    products_list = conn.execute("""
        SELECT *
        FROM products
        ORDER BY product_name
    """).fetchall()

    conn.close()


    if request.method == "POST":

        conn = get_db_connection()

        try:

            supplier_id = int(
                request.form.get("supplier_id", "")
            )

            product_ids = request.form.getlist("product_id[]")

            quantities = request.form.getlist("quantity[]")

            prices = request.form.getlist("purchase_price[]")

            payment_status = request.form.get(
                "payment_status", "Pending"
            )

            payment_method = request.form.get(
                "payment_method", ""
            )


            if not product_ids:

                raise ValueError("Please select products.")


            if not (
                len(product_ids) == len(quantities)
                == len(prices)
            ):

                raise ValueError("Invalid purchase details.")


            if payment_status not in [
                "Paid", "Pending", "Partial"
            ]:

                raise ValueError("Invalid payment status.")


            if payment_method not in [
                "Cash", "UPI", "Card", "Bank Transfer"
            ]:

                raise ValueError("Invalid payment method.")


            # Combine duplicate product entries

            cart = {}

            for pid, qty, price in zip(
                product_ids, quantities, prices
            ):

                pid = int(pid)

                qty = int(qty)

                price = float(price)

                if pid <= 0 or qty <= 0 or price <= 0:

                    raise ValueError(
                        "Quantity and purchase price must be positive."
                    )

                if pid not in cart:

                    cart[pid] = {
                        "quantity": 0,
                        "total_cost": 0
                    }

                cart[pid]["quantity"] += qty

                cart[pid]["total_cost"] += qty * price


            conn.execute("BEGIN IMMEDIATE")


            supplier = conn.execute("""
                SELECT supplier_id
                FROM suppliers
                WHERE supplier_id = ?
            """, (supplier_id,)).fetchone()


            if supplier is None:

                raise ValueError("Supplier not found.")


            purchase_items = []

            total_amount = 0


            for product_id, details in cart.items():

                product = conn.execute("""
                    SELECT *
                    FROM products
                    WHERE product_id = ?
                """, (product_id,)).fetchone()


                if product is None:

                    raise ValueError("Product not found.")


                quantity = details["quantity"]

                unit_price = (
                    details["total_cost"] / quantity
                )

                item_total = details["total_cost"]

                total_amount += item_total


                purchase_items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "purchase_price": unit_price,
                    "subtotal": item_total
                })


            # Create Purchase Record

            cursor = conn.execute("""
                INSERT INTO purchases

                (
                    supplier_id,
                    total_amount,
                    payment_status,
                    payment_method
                )

                VALUES (?, ?, ?, ?)

            """, (
                supplier_id,
                total_amount,
                payment_status,
                payment_method
            ))


            purchase_id = cursor.lastrowid


            # Save Items and Increase Stock

            for item in purchase_items:

                conn.execute("""
                    INSERT INTO purchase_items

                    (
                        purchase_id,
                        product_id,
                        quantity,
                        purchase_price,
                        subtotal
                    )

                    VALUES (?, ?, ?, ?, ?)

                """, (
                    purchase_id,
                    item["product_id"],
                    item["quantity"],
                    item["purchase_price"],
                    item["subtotal"]
                ))


                conn.execute("""
                    UPDATE products

                    SET
                        quantity = quantity + ?,
                        supplier_id = ?

                    WHERE product_id = ?

                """, (
                    item["quantity"],
                    supplier_id,
                    item["product_id"]
                ))


                conn.execute("""
                    UPDATE products

                    SET purchase_price = ?

                    WHERE product_id = ?

                """, (
                    item["purchase_price"],
                    item["product_id"]
                ))


                conn.execute("""
                    INSERT INTO stock_history

                    (
                        product_id,
                        change_type,
                        quantity,
                        note
                    )

                    VALUES (?, 'IN', ?, ?)

                """, (
                    item["product_id"],
                    item["quantity"],
                    f"Purchase ID: {purchase_id}"
                ))


            conn.commit()

            flash(
                "Purchase completed successfully!",
                "success"
            )

            return redirect(
                url_for(
                    "supplier_history",
                    supplier_id=supplier_id
                )
            )


        except ValueError as error:

            conn.rollback()

            flash(str(error), "danger")


        except Exception as error:

            conn.rollback()

            print("Purchase Error:", error)

            flash(
                "Unable to complete purchase. Please check database configuration.",
                "danger"
            )


        finally:

            conn.close()


    return render_template(
        "new_purchase.html",
        suppliers=suppliers_list,
        products=products_list
    )

@app.route("/supplier-history/<int:supplier_id>")
@login_required
def supplier_history(supplier_id):

    conn = get_db_connection()

    supplier = conn.execute("""
        SELECT *
        FROM suppliers
        WHERE supplier_id = ?
    """, (supplier_id,)).fetchone()


    if supplier is None:

        conn.close()

        abort(404)


    purchases = conn.execute("""
        SELECT *
        FROM purchases
        WHERE supplier_id = ?
        ORDER BY purchase_id DESC
    """, (supplier_id,)).fetchall()


    total_purchases = conn.execute("""
        SELECT COUNT(*)
        FROM purchases
        WHERE supplier_id = ?
    """, (supplier_id,)).fetchone()[0]


    total_amount = conn.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM purchases
        WHERE supplier_id = ?
    """, (supplier_id,)).fetchone()[0]


    conn.close()

    return render_template(
        "supplier_history.html",
        supplier=supplier,
        purchases=purchases,
        total_purchases=total_purchases,
        total_amount=total_amount
    )

@app.route("/reports")
@login_required
def reports():

    conn = get_db_connection()

    # Total Products

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]


    # Total Customers

    total_customers = conn.execute("""
        SELECT COUNT(*)
        FROM customers
    """).fetchone()[0]


    # Total Suppliers

    total_suppliers = conn.execute("""
        SELECT COUNT(*)
        FROM suppliers
    """).fetchone()[0]


    conn.close()

    return render_template(
        "reports.html",

        total_products=total_products,

        total_customers=total_customers,

        total_suppliers=total_suppliers
    )

# ==========================================
# PHASE 9 - REPORT MANAGEMENT ROUTES
# ==========================================

# ==========================================
# PHASE 9.2 - PURCHASE ANALYTICS
# ==========================================

@app.route("/purchase-report")
@login_required
def purchase_report():

    conn = get_db_connection()

    # ======================================
    # DATE FILTER
    # ======================================

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    conditions = []
    params = []

    if start_date:
        conditions.append(
            "DATE(pu.purchase_date) >= DATE(?)"
        )
        params.append(start_date)

    if end_date:
        conditions.append(
            "DATE(pu.purchase_date) <= DATE(?)"
        )
        params.append(end_date)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # ======================================
    # 1. TOTAL PURCHASES
    # ======================================

    total_purchases = conn.execute(f"""
        SELECT COALESCE(SUM(pu.total_amount), 0)

        FROM purchases pu

        {where_clause}

    """, params).fetchone()[0]

    # ======================================
    # 2. TOTAL PURCHASE ORDERS
    # ======================================

    total_orders = conn.execute(f"""
        SELECT COUNT(*)

        FROM purchases pu

        {where_clause}

    """, params).fetchone()[0]

    # ======================================
    # 3. TOTAL ITEMS PURCHASED
    # ======================================

    total_items = conn.execute(f"""
        SELECT COALESCE(SUM(pi.quantity), 0)

        FROM purchase_items pi

        INNER JOIN purchases pu
        ON pi.purchase_id = pu.purchase_id

        {where_clause}

    """, params).fetchone()[0]

    # ======================================
    # 4. AVERAGE PURCHASE VALUE
    # ======================================

    average_purchase = (
        total_purchases / total_orders
        if total_orders > 0 else 0
    )

    # ======================================
    # 5. MONTHLY PURCHASE ANALYTICS
    # ======================================

    monthly_purchases = conn.execute(f"""

        SELECT

            strftime('%Y-%m', pu.purchase_date) AS month,

            SUM(pu.total_amount) AS amount

        FROM purchases pu

        {where_clause}

        GROUP BY strftime('%Y-%m', pu.purchase_date)

        ORDER BY month

    """, params).fetchall()

    monthly_labels = [
        row["month"] for row in monthly_purchases
    ]

    monthly_values = [
        row["amount"] for row in monthly_purchases
    ]

    # ======================================
    # 6. DAILY PURCHASE ANALYTICS
    # ======================================

    daily_purchases = conn.execute(f"""

        SELECT

            DATE(pu.purchase_date) AS purchase_day,

            SUM(pu.total_amount) AS amount

        FROM purchases pu

        {where_clause}

        GROUP BY DATE(pu.purchase_date)

        ORDER BY purchase_day

    """, params).fetchall()

    daily_labels = [
        row["purchase_day"] for row in daily_purchases
    ]

    daily_values = [
        row["amount"] for row in daily_purchases
    ]

    # ======================================
    # 7. TOP 5 PURCHASED PRODUCTS
    # ======================================

    top_products = conn.execute(f"""

        SELECT

            pr.product_name,

            SUM(pi.quantity) AS total_quantity,

            SUM(pi.subtotal) AS total_value

        FROM purchase_items pi

        INNER JOIN purchases pu
        ON pi.purchase_id = pu.purchase_id

        INNER JOIN products pr
        ON pi.product_id = pr.product_id

        {where_clause}

        GROUP BY pr.product_id, pr.product_name

        ORDER BY total_quantity DESC

        LIMIT 5

    """, params).fetchall()

    product_labels = [
        row["product_name"] for row in top_products
    ]

    product_values = [
        row["total_quantity"] for row in top_products
    ]

    # ======================================
    # 8. SUPPLIER-WISE PURCHASE REPORT
    # ======================================

    supplier_purchases = conn.execute(f"""

        SELECT

            COALESCE(su.supplier_name, 'Unknown Supplier')
                AS supplier_name,

            COUNT(pu.purchase_id) AS total_orders,

            SUM(pu.total_amount) AS total_amount

        FROM purchases pu

        LEFT JOIN suppliers su

        ON pu.supplier_id = su.supplier_id

        {where_clause}

        GROUP BY pu.supplier_id, su.supplier_name

        ORDER BY total_amount DESC

    """, params).fetchall()

    # ======================================
    # 9. PURCHASE HISTORY
    # ======================================

    purchase_history = conn.execute(f"""

        SELECT

            pu.purchase_id,

            COALESCE(su.supplier_name, 'Unknown Supplier')
                AS supplier_name,

            pu.total_amount,

            pu.payment_status,

            pu.payment_method,

            pu.purchase_date

        FROM purchases pu

        LEFT JOIN suppliers su

        ON pu.supplier_id = su.supplier_id

        {where_clause}

        ORDER BY pu.purchase_id DESC

        LIMIT 100

    """, params).fetchall()

    # ======================================
    # CLOSE DATABASE
    # ======================================

    conn.close()

    # ======================================
    # SEND DATA TO HTML
    # ======================================

    return render_template(

        "purchase_report.html",

        total_purchases=total_purchases,

        total_orders=total_orders,

        total_items=total_items,

        average_purchase=average_purchase,

        monthly_labels=monthly_labels,

        monthly_values=monthly_values,

        daily_labels=daily_labels,

        daily_values=daily_values,

        product_labels=product_labels,

        product_values=product_values,

        supplier_purchases=supplier_purchases,

        purchase_history=purchase_history,

        start_date=start_date,

        end_date=end_date

    )


# ==========================================
# PHASE 9.3 - PROFIT & REVENUE ANALYTICS
# ==========================================

@app.route("/profit-report")
@login_required
def profit_report():

    conn = get_db_connection()

    # ======================================
    # DATE FILTER
    # ======================================

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    conditions = []
    params = []

    if start_date:
        conditions.append(
            "DATE(s.sale_date) >= DATE(?)"
        )
        params.append(start_date)

    if end_date:
        conditions.append(
            "DATE(s.sale_date) <= DATE(?)"
        )
        params.append(end_date)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # ======================================
    # 1. TOTAL REVENUE
    # ======================================

    total_revenue = conn.execute(f"""

        SELECT COALESCE(SUM(s.total_amount), 0)

        FROM sales s

        {where_clause}

    """, params).fetchone()[0]

    # ======================================
    # 2. TOTAL PURCHASE COST
    # ======================================

    purchase_conditions = []
    purchase_params = []

    if start_date:

        purchase_conditions.append(
            "DATE(pu.purchase_date) >= DATE(?)"
        )

        purchase_params.append(start_date)

    if end_date:

        purchase_conditions.append(
            "DATE(pu.purchase_date) <= DATE(?)"
        )

        purchase_params.append(end_date)

    purchase_where = ""

    if purchase_conditions:

        purchase_where = (
            "WHERE " + " AND ".join(purchase_conditions)
        )

    total_purchase_cost = conn.execute(f"""

        SELECT COALESCE(SUM(pu.total_amount), 0)

        FROM purchases pu

        {purchase_where}

    """, purchase_params).fetchone()[0]

    # ======================================
    # 3. ESTIMATED COST OF GOODS SOLD
    # ======================================

    total_cogs = conn.execute(f"""

        SELECT COALESCE(
            SUM(si.quantity * p.purchase_price), 0
        )

        FROM sale_items si

        INNER JOIN sales s

        ON si.sale_id = s.sale_id

        INNER JOIN products p

        ON si.product_id = p.product_id

        {where_clause}

    """, params).fetchone()[0]

    # ======================================
    # 4. GROSS PROFIT
    # ======================================

    gross_profit = total_revenue - total_cogs

    # ======================================
    # 5. PROFIT MARGIN
    # ======================================

    profit_margin = (

        (gross_profit / total_revenue) * 100

        if total_revenue > 0 else 0

    )

    # ======================================
    # 6. MONTHLY REVENUE
    # ======================================

    monthly_revenue = conn.execute(f"""

        SELECT

            strftime('%Y-%m', s.sale_date) AS month,

            SUM(s.total_amount) AS revenue

        FROM sales s

        {where_clause}

        GROUP BY strftime('%Y-%m', s.sale_date)

        ORDER BY month

    """, params).fetchall()

    revenue_labels = [
        row["month"] for row in monthly_revenue
    ]

    revenue_values = [
        row["revenue"] for row in monthly_revenue
    ]

    # ======================================
    # 7. MONTHLY COGS
    # ======================================

    monthly_cogs = conn.execute(f"""

        SELECT

            strftime('%Y-%m', s.sale_date) AS month,

            SUM(si.quantity * p.purchase_price) AS cost

        FROM sale_items si

        INNER JOIN sales s

        ON si.sale_id = s.sale_id

        INNER JOIN products p

        ON si.product_id = p.product_id

        {where_clause}

        GROUP BY strftime('%Y-%m', s.sale_date)

        ORDER BY month

    """, params).fetchall()

    cogs_dict = {
        row["month"]: row["cost"] or 0
        for row in monthly_cogs
    }

    # ======================================
    # 8. MONTHLY PROFIT
    # ======================================

    profit_values = [

        revenue - cogs_dict.get(month, 0)

        for month, revenue in zip(
            revenue_labels,
            revenue_values
        )

    ]

    # ======================================
    # 9. PRODUCT-WISE PROFIT
    # ======================================

    product_profit = conn.execute(f"""

        SELECT

            p.product_name,

            SUM(si.quantity) AS quantity_sold,

            SUM(si.subtotal) AS sales_amount,

            SUM(
                si.quantity * p.purchase_price
            ) AS estimated_cost,

            SUM(si.subtotal) -

            SUM(
                si.quantity * p.purchase_price
            ) AS estimated_profit

        FROM sale_items si

        INNER JOIN sales s

        ON si.sale_id = s.sale_id

        INNER JOIN products p

        ON si.product_id = p.product_id

        {where_clause}

        GROUP BY p.product_id, p.product_name

        ORDER BY estimated_profit DESC

    """, params).fetchall()

    # ======================================
    # 10. TOP 5 PROFITABLE PRODUCTS
    # ======================================

    top_products = product_profit[:5]

    top_product_labels = [

        row["product_name"]

        for row in top_products

    ]

    top_product_values = [

        row["estimated_profit"]

        for row in top_products

    ]

    # ======================================
    # 11. REVENUE VS PURCHASE COMPARISON
    # ======================================

    comparison_labels = [
        "Revenue",
        "Purchase Cost"
    ]

    comparison_values = [

        total_revenue,

        total_purchase_cost

    ]

    # ======================================
    # CLOSE DATABASE
    # ======================================

    conn.close()

    # ======================================
    # SEND DATA TO HTML
    # ======================================

    return render_template(

        "profit_report.html",

        total_revenue=total_revenue,

        total_purchase_cost=total_purchase_cost,

        total_cogs=total_cogs,

        gross_profit=gross_profit,

        profit_margin=profit_margin,

        revenue_labels=revenue_labels,

        revenue_values=revenue_values,

        profit_values=profit_values,

        top_product_labels=top_product_labels,

        top_product_values=top_product_values,

        product_profit=product_profit,

        comparison_labels=comparison_labels,

        comparison_values=comparison_values,

        start_date=start_date,

        end_date=end_date

    )


# ==========================================
# PHASE 9.4 - INVENTORY ANALYTICS
# ==========================================

@app.route("/inventory-report")
@login_required
def inventory_report():

    conn = get_db_connection()

    # ======================================
    # DATE FILTER FOR STOCK HISTORY
    # ======================================

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    conditions = []
    params = []

    if start_date:
        conditions.append("DATE(created_at) >= DATE(?)")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(created_at) <= DATE(?)")
        params.append(end_date)

    history_where = ""

    if conditions:
        history_where = "WHERE " + " AND ".join(conditions)

    # ======================================
    # 1. TOTAL PRODUCTS
    # ======================================

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    # ======================================
    # 2. TOTAL STOCK QUANTITY
    # ======================================

    total_stock = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM products
    """).fetchone()[0]

    # ======================================
    # 3. TOTAL INVENTORY VALUE
    # ======================================

    inventory_value = conn.execute("""
        SELECT COALESCE(
            SUM(quantity * purchase_price), 0
        )
        FROM products
    """).fetchone()[0]

    # ======================================
    # 4. LOW STOCK PRODUCTS
    # ======================================

    low_stock_count = conn.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity > 0
        AND quantity <= minimum_stock
    """).fetchone()[0]

    # ======================================
    # 5. OUT OF STOCK PRODUCTS
    # ======================================

    out_of_stock_count = conn.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity <= 0
    """).fetchone()[0]

    # ======================================
    # 6. OVERSTOCK PRODUCTS
    # ======================================

    overstock_count = conn.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE minimum_stock > 0
        AND quantity >= minimum_stock * 3
    """).fetchone()[0]

    # ======================================
    # 7. CATEGORY-WISE INVENTORY
    # ======================================

    category_data = conn.execute("""
        SELECT

            COALESCE(category, 'Uncategorized')
                AS category,

            SUM(quantity) AS total_quantity,

            SUM(quantity * purchase_price)
                AS total_value

        FROM products

        GROUP BY category

        ORDER BY total_value DESC

    """).fetchall()

    category_labels = [
        row["category"] for row in category_data
    ]

    category_values = [
        row["total_quantity"] for row in category_data
    ]

    # ======================================
    # 8. STOCK IN ANALYTICS
    # ======================================

    stock_in = conn.execute(f"""

        SELECT COALESCE(SUM(quantity), 0)

        FROM stock_history

        {history_where}

        {"AND" if history_where else "WHERE"}
        LOWER(change_type) IN ('in', 'stock in', 'purchase')

    """, params).fetchone()[0]

    # ======================================
    # 9. STOCK OUT ANALYTICS
    # ======================================

    stock_out = conn.execute(f"""

        SELECT COALESCE(SUM(quantity), 0)

        FROM stock_history

        {history_where}

        {"AND" if history_where else "WHERE"}
        LOWER(change_type) IN ('out', 'stock out', 'sale')

    """, params).fetchone()[0]

    # ======================================
    # 10. PRODUCT STOCK STATUS
    # ======================================

    stock_status = conn.execute("""
        SELECT

            CASE

                WHEN quantity <= 0
                    THEN 'Out of Stock'

                WHEN quantity <= minimum_stock
                    THEN 'Low Stock'

                WHEN minimum_stock > 0
                     AND quantity >= minimum_stock * 3
                    THEN 'Overstock'

                ELSE 'Available'

            END AS status,

            COUNT(*) AS total

        FROM products

        GROUP BY status

    """).fetchall()

    status_labels = [
        row["status"] for row in stock_status
    ]

    status_values = [
        row["total"] for row in stock_status
    ]

    # ======================================
    # 11. TOP 5 INVENTORY PRODUCTS
    # ======================================

    top_products = conn.execute("""
        SELECT

            product_name,

            quantity,

            purchase_price,

            quantity * purchase_price
                AS stock_value

        FROM products

        ORDER BY stock_value DESC

        LIMIT 5

    """).fetchall()

    top_product_labels = [
        row["product_name"] for row in top_products
    ]

    top_product_values = [
        row["stock_value"] for row in top_products
    ]

    # ======================================
    # 12. LOW STOCK PRODUCT DETAILS
    # ======================================

    low_stock_products = conn.execute("""
        SELECT

            product_id,

            product_name,

            category,

            quantity,

            minimum_stock

        FROM products

        WHERE quantity <= minimum_stock

        ORDER BY quantity ASC

    """).fetchall()

    # ======================================
    # 13. STOCK HISTORY
    # ======================================

    stock_history = conn.execute(f"""
        SELECT

            sh.history_id,

            p.product_name,

            sh.change_type,

            sh.quantity,

            sh.note,

            sh.created_at

        FROM stock_history sh

        LEFT JOIN products p

        ON sh.product_id = p.product_id

        WHERE 1=1

        {"AND DATE(sh.created_at) >= DATE(?)" if start_date else ""}

        {"AND DATE(sh.created_at) <= DATE(?)" if end_date else ""}

        ORDER BY sh.history_id DESC

        LIMIT 100

    """, (
        ([start_date] if start_date else []) +
        ([end_date] if end_date else [])
    )).fetchall()

    # ======================================
    # CLOSE DATABASE
    # ======================================

    conn.close()

    # ======================================
    # SEND DATA TO HTML
    # ======================================

    return render_template(

        "inventory_report.html",

        total_products=total_products,

        total_stock=total_stock,

        inventory_value=inventory_value,

        low_stock_count=low_stock_count,

        out_of_stock_count=out_of_stock_count,

        overstock_count=overstock_count,

        stock_in=stock_in,

        stock_out=stock_out,

        category_labels=category_labels,

        category_values=category_values,

        status_labels=status_labels,

        status_values=status_values,

        top_product_labels=top_product_labels,

        top_product_values=top_product_values,

        top_products=top_products,

        low_stock_products=low_stock_products,

        stock_history=stock_history,

        start_date=start_date,

        end_date=end_date

    )

# ==========================================
# PHASE 9.1 - SALES ANALYTICS
# ==========================================

@app.route("/sales-report")
@login_required
def sales_report():

    conn = get_db_connection()

    # Date Filters
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    conditions = []
    params = []

    if start_date:
        conditions.append("DATE(s.sale_date) >= DATE(?)")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(s.sale_date) <= DATE(?)")
        params.append(end_date)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # ======================================
    # 1. TOTAL SALES
    # ======================================

    total_sales = conn.execute(f"""
        SELECT COALESCE(SUM(s.total_amount), 0)
        FROM sales s
        {where_clause}
    """, params).fetchone()[0]

    # ======================================
    # 2. TOTAL ORDERS
    # ======================================

    total_orders = conn.execute(f"""
        SELECT COUNT(*)
        FROM sales s
        {where_clause}
    """, params).fetchone()[0]

    # ======================================
    # 3. TOTAL ITEMS SOLD
    # ======================================

    item_query = f"""
        SELECT COALESCE(SUM(si.quantity), 0)

        FROM sale_items si

        INNER JOIN sales s
        ON si.sale_id = s.sale_id

        {where_clause}
    """

    total_items = conn.execute(
        item_query, params
    ).fetchone()[0]

    # ======================================
    # 4. AVERAGE ORDER VALUE
    # ======================================

    average_order = (
        total_sales / total_orders
        if total_orders > 0 else 0
    )

    # ======================================
    # 5. MONTHLY SALES
    # ======================================

    monthly_sales = conn.execute(f"""
        SELECT
            strftime('%Y-%m', s.sale_date) AS month,
            SUM(s.total_amount) AS amount

        FROM sales s

        {where_clause}

        GROUP BY strftime('%Y-%m', s.sale_date)

        ORDER BY month
    """, params).fetchall()

    monthly_labels = [
        row["month"] for row in monthly_sales
    ]

    monthly_values = [
        row["amount"] for row in monthly_sales
    ]

    # ======================================
    # 6. DAILY SALES
    # ======================================

    daily_sales = conn.execute(f"""
        SELECT
            DATE(s.sale_date) AS sale_day,
            SUM(s.total_amount) AS amount

        FROM sales s

        {where_clause}

        GROUP BY DATE(s.sale_date)

        ORDER BY sale_day
    """, params).fetchall()

    daily_labels = [
        row["sale_day"] for row in daily_sales
    ]

    daily_values = [
        row["amount"] for row in daily_sales
    ]

    # ======================================
    # 7. TOP 5 SELLING PRODUCTS
    # ======================================

    top_products = conn.execute(f"""
        SELECT
            p.product_name,
            SUM(si.quantity) AS total_quantity

        FROM sale_items si

        INNER JOIN sales s
        ON si.sale_id = s.sale_id

        INNER JOIN products p
        ON si.product_id = p.product_id

        {where_clause}

        GROUP BY p.product_id, p.product_name

        ORDER BY total_quantity DESC

        LIMIT 5
    """, params).fetchall()

    product_labels = [
        row["product_name"] for row in top_products
    ]

    product_values = [
        row["total_quantity"] for row in top_products
    ]

    # ======================================
    # 8. SALES HISTORY
    # ======================================

    sales_history = conn.execute(f"""
        SELECT
            s.sale_id,
            COALESCE(c.customer_name, 'Walk-in Customer')
                AS customer_name,
            s.total_amount,
            s.sale_date,
            s.payment_method

        FROM sales s

        LEFT JOIN customers c
        ON s.customer_id = c.customer_id

        {where_clause}

        ORDER BY s.sale_id DESC

        LIMIT 100
    """, params).fetchall()

    conn.close()

    # ======================================
    # SEND DATA TO HTML
    # ======================================

    return render_template(
        "sales_report.html",

        total_sales=total_sales,
        total_orders=total_orders,
        total_items=total_items,
        average_order=average_order,

        monthly_labels=monthly_labels,
        monthly_values=monthly_values,

        daily_labels=daily_labels,
        daily_values=daily_values,

        product_labels=product_labels,
        product_values=product_values,

        sales_history=sales_history,

        start_date=start_date,
        end_date=end_date
    )

    # =====================================
# SETTINGS DATABASE TABLES
# =====================================
@app.route("/settings")
@login_required
def settings():

    conn = get_db_connection()

    settings_data = conn.execute("""

        SELECT setting_key, setting_value

        FROM app_settings

    """).fetchall()

    company = conn.execute("""

        SELECT *

        FROM company_settings

        ORDER BY company_id DESC

        LIMIT 1

    """).fetchone()

    conn.close()

    settings_dict = {

        row["setting_key"]: row["setting_value"]

        for row in settings_data

    }

    return render_template(

        "settings/settings.html",

        settings=settings_dict,

        company=company

    )

@app.route("/settings/general", methods=["POST"])
@login_required
def save_general_settings():

    allowed = [
        "app_name",
        "language",
        "currency",
        "date_format"
    ]

    conn = get_db_connection()

    for key in allowed:

        value = request.form.get(key, "").strip()

        if not value:
            continue

        conn.execute("""

            INSERT INTO app_settings
            (setting_key, setting_value)

            VALUES (?, ?)

            ON CONFLICT(setting_key)

            DO UPDATE SET
            setting_value = excluded.setting_value,
            updated_at = CURRENT_TIMESTAMP

        """, (key, value))

    conn.commit()
    conn.close()

    flash("General settings saved successfully!", "success")

    return redirect(url_for("settings", section="general"))

def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()

    # =================================
    # SETTINGS DATABASE TABLES
    # =================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (

        setting_id INTEGER PRIMARY KEY AUTOINCREMENT,

        setting_key TEXT UNIQUE NOT NULL,

        setting_value TEXT,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_settings (

        company_id INTEGER PRIMARY KEY AUTOINCREMENT,

        company_name TEXT,

        company_email TEXT,

        company_phone TEXT,

        company_address TEXT,

        company_logo TEXT,

        tax_number TEXT,

        currency TEXT DEFAULT 'INR',

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =================================
    # DEFAULT SETTINGS
    # =================================

    default_settings = {

        "app_name": "Smart Inventory & Sales Manager",

        "language": "English",

        "currency": "INR",

        "date_format": "DD-MM-YYYY",

        "theme": "light",

        "minimum_stock": "5",

        "low_stock_alert": "1",

        "tax_percentage": "18",

        "invoice_prefix": "INV",

        "default_discount": "0",

        "email_notifications": "1",

        "session_timeout": "30"

    }

    for key, value in default_settings.items():

        cursor.execute("""

            INSERT OR IGNORE INTO app_settings

            (setting_key, setting_value)

            VALUES (?, ?)

        """, (key, value))

    conn.commit()

    conn.close()

def create_settings_tables():

    conn = get_db_connection()

    # ======================================
    # APP SETTINGS TABLE
    # ======================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (

            setting_id INTEGER PRIMARY KEY AUTOINCREMENT,

            setting_key TEXT UNIQUE NOT NULL,

            setting_value TEXT,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # ======================================
    # COMPANY SETTINGS TABLE
    # ======================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_settings (

            company_id INTEGER PRIMARY KEY AUTOINCREMENT,

            company_name TEXT,

            company_email TEXT,

            company_phone TEXT,

            company_address TEXT,

            company_logo TEXT,

            tax_number TEXT,

            currency TEXT DEFAULT 'INR',

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # ======================================
    # DEFAULT SETTINGS
    # ======================================

    default_settings = {

        "app_name": "Smart Inventory & Sales Manager",

        "language": "English",

        "currency": "INR",

        "date_format": "DD-MM-YYYY",

        "theme": "light",

        "minimum_stock": "5",

        "low_stock_alert": "1",

        "tax_percentage": "18",

        "invoice_prefix": "INV",

        "default_discount": "0",

        "email_notifications": "1",

        "session_timeout": "30"

    }

    for key, value in default_settings.items():

        conn.execute("""

            INSERT OR IGNORE INTO app_settings

            (setting_key, setting_value)

            VALUES (?, ?)

        """, (key, value))

    conn.commit()

    

    conn.close()

    print("Settings tables created successfully!")
# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()

    return redirect(url_for("login"))


if __name__ == "__main__":

    # Initialize existing database first
    init_db()

    # Create settings tables
    create_settings_tables()

    # Start Flask
    app.run(debug=True)