import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Database file location
BASE_DIR = Path(__file__).resolve().parent

DATABASE = BASE_DIR / "inventory.db"


# Database Connection
def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    # Access columns using their names
    conn.row_factory = sqlite3.Row

    # Enable foreign key relationships
    conn.execute("PRAGMA foreign_keys = ON")

    return conn

def create_tables():

    conn = get_db_connection()

    # 1. ADMIN TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin (

            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # 2. PRODUCTS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (

            product_id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_name TEXT NOT NULL,

            category TEXT,

            purchase_price REAL NOT NULL,

            selling_price REAL NOT NULL,

            quantity INTEGER DEFAULT 0,

            minimum_stock INTEGER DEFAULT 5,

            supplier_id INTEGER,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (supplier_id)
            REFERENCES suppliers(supplier_id)

        )
    """)


    # 3. CUSTOMERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (

            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_name TEXT NOT NULL,

            phone TEXT,

            email TEXT,

            address TEXT

        )
    """)


    # 4. SUPPLIERS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (

            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,

            supplier_name TEXT NOT NULL,

            phone TEXT,

            email TEXT,

            address TEXT

        )
    """)


    # 5. SALES TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (

            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_id INTEGER,

            total_amount REAL NOT NULL,

            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
            REFERENCES customers(customer_id)

        )
    """)


    # 6. SALE ITEMS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (

            sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

            sale_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            price REAL NOT NULL,

            subtotal REAL NOT NULL,

            FOREIGN KEY (sale_id)
            REFERENCES sales(sale_id),

            FOREIGN KEY (product_id)
            REFERENCES products(product_id)

        )
    """)


    # 7. STOCK HISTORY TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_history (

            history_id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER NOT NULL,

            change_type TEXT NOT NULL,

            quantity INTEGER NOT NULL,

            note TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (product_id)
            REFERENCES products(product_id)

        )
    """)
    
    #SALES TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
        
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_id INTEGER,

            subtotal REAL NOT NULL,

            discount REAL DEFAULT 0,

            tax_amount REAL DEFAULT 0,

            total_amount REAL NOT NULL,

            payment_method TEXT,

            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
            REFERENCES customers(customer_id)

        )
    """)

    # SALE ITEMS TABLE
    conn.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (

            sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

            sale_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            unit_price REAL NOT NULL,

            purchase_price REAL NOT NULL,

            subtotal REAL NOT NULL,

            FOREIGN KEY (sale_id)
            REFERENCES sales(sale_id),

            FOREIGN KEY (product_id)
            REFERENCES products(product_id)

        )
    """)
    
    conn.commit()

    conn.close()

    print("All database tables created successfully!")

def insert_sample_data():

    conn = get_db_connection()

    # Insert sample suppliers
    conn.execute("""
        INSERT INTO suppliers
        (supplier_name, phone, email, address)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM suppliers WHERE supplier_name = ?
        )
    """, (
        "ABC Electronics",
        "9876543210",
        "abc@gmail.com",
        "Delhi",
        "ABC Electronics"
    ))


    # Insert sample customers
    conn.execute("""
        INSERT INTO customers
        (customer_name, phone, email, address)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM customers WHERE phone = ?
        )
    """, (
        "Rahul Kumar",
        "9876543211",
        "rahul@gmail.com",
        "Delhi",
        "9876543211"
    ))


    # Insert sample products
    conn.execute("""
        INSERT INTO products
        (product_name, category, purchase_price,
         selling_price, quantity, minimum_stock)
        SELECT ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM products WHERE product_name = ?
        )
    """, (
        "Laptop",
        "Electronics",
        35000,
        42000,
        10,
        5,
        "Laptop"
    ))


    conn.execute("""
        INSERT INTO products
        (product_name, category, purchase_price,
         selling_price, quantity, minimum_stock)
        SELECT ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM products WHERE product_name = ?
        )
    """, (
        "Mouse",
        "Accessories",
        200,
        350,
        50,
        10,
        "Mouse"
    ))


    conn.commit()

    conn.close()

    print("Sample data inserted successfully!")

def create_admin():

    conn = get_db_connection()

    username = "admin"

    password = "Admin@123"

    hashed_password = generate_password_hash(password)

    existing_admin = conn.execute(
        "SELECT * FROM admin WHERE username = ?",
        (username,)
    ).fetchone()

    if existing_admin is None:

        conn.execute("""
            INSERT INTO admin (username, password)
            VALUES (?, ?)
        """, (username, hashed_password))

        conn.commit()

        print("Admin account created successfully!")

    else:

        print("Admin account already exists!")

    conn.close()

def update_sales_table():

    conn = get_db_connection()

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(sales)"
        ).fetchall()
    ]


    required_columns = {

        "customer_id": "INTEGER",

        "subtotal": "REAL DEFAULT 0",

        "discount": "REAL DEFAULT 0",

        "tax_amount": "REAL DEFAULT 0",

        "total_amount": "REAL DEFAULT 0",

        "payment_method": "TEXT",

        "sale_date": "TEXT"

    }

    for column, data_type in required_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE sales ADD COLUMN {column} {data_type}"
            )

            print(f"Added column: {column}")

    conn.commit()

    conn.close()

    print("Sales database updated successfully!")

def update_customers_table():

    conn = get_db_connection()

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(customers)"
        ).fetchall()
    ]

    required_columns = {

        "customer_name": "TEXT",

        "phone": "TEXT",

        "email": "TEXT",

        "address": "TEXT",

        "created_at": "TEXT"

    }

    for column, data_type in required_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE customers ADD COLUMN "
                f"{column} {data_type}"
            )

            print(f"Added column: {column}")

    conn.commit()

    conn.close()

    print("Customer database updated successfully!")

def update_supplier_database():

    conn = get_db_connection()

    # Create Suppliers Table

    conn.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (

            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,

            supplier_name TEXT NOT NULL,

            company_name TEXT,

            phone TEXT,

            email TEXT,

            address TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # Create Purchases Table

    conn.execute("""
        CREATE TABLE IF NOT EXISTS purchases (

            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,

            supplier_id INTEGER NOT NULL,

            total_amount REAL DEFAULT 0,

            payment_status TEXT DEFAULT 'Pending',

            payment_method TEXT,

            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (supplier_id)
            REFERENCES suppliers(supplier_id)

        )
    """)


    # Create Purchase Items Table

    conn.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (

            purchase_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

            purchase_id INTEGER NOT NULL,

            product_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            purchase_price REAL NOT NULL,

            subtotal REAL NOT NULL,

            FOREIGN KEY (purchase_id)
            REFERENCES purchases(purchase_id),

            FOREIGN KEY (product_id)
            REFERENCES products(product_id)

        )
    """)

    # Check existing product columns

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(products)"
        ).fetchall()
    ]

    if "supplier_id" not in columns:

        conn.execute("""
            ALTER TABLE products
            ADD COLUMN supplier_id INTEGER
        """)

        print("Added supplier_id to products table")

        # =====================================
        # # SUPPLIER TABLE MIGRATION
        # # =====================================
    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(suppliers)"
            ).fetchall()
    ]
        
    supplier_columns = {
        "supplier_name": "TEXT",
        "company_name": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "address": "TEXT",
        "created_at": "TIMESTAMP"
    }
        
    for column_name, column_type in supplier_columns.items():
        
        if column_name not in columns:
            
            conn.execute(f"""
                ALTER TABLE suppliers
                ADD COLUMN {column_name} {column_type}
            """)
                
            print(f"Added column: {column_name}")


    conn.commit()

    conn.close()

    print("Supplier database created successfully!")

    

from database import get_db_connection

conn = get_db_connection()

tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("\n========== DATABASE STRUCTURE ==========\n")

for table in tables:

    table_name = table["name"]

    print("\nTABLE:", table_name)

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    for column in columns:

        print(
            "Column:",
            column["name"],
            "| Type:",
            column["type"]
        )

    print("--------------------------------")

conn.close()

if __name__ == "__main__":

    create_tables()

    insert_sample_data()

    create_admin()

    update_sales_table()

    update_customers_table()

    update_supplier_database()

    print("Database initialization completed!")