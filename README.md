# 📦 Smart Inventory & Sales Manager

### A Python Flask-Based Inventory and Sales Management System for Small Businesses

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue?logo=sqlite)
![Status](https://img.shields.io/badge/Project-Active-success)

---

## 📌 About the Project

**Smart Inventory & Sales Manager** is a web-based application developed using Python and Flask to help small businesses manage their daily inventory, sales, purchases, customers, and suppliers efficiently.

The main objective of this project is to simplify business operations, reduce manual record-keeping, maintain accurate stock information, and provide useful business insights through a centralized dashboard.

The system provides an easy-to-use interface for managing products, tracking stock movements, generating invoices, and monitoring sales performance.

## 🎯 Project Objectives

- Automate inventory management.
- Simplify sales and purchase operations.
- Maintain customer and supplier records.
- Track stock availability and low-stock products.
- Generate sales invoices.
- Monitor revenue and business performance.
- Reduce manual errors and paperwork.

## ✨ Key Features

### 1. Dashboard
- Overview of total products.
- Total customers and sales.
- Revenue monitoring.
- Low-stock alerts.

### 2. Product Management
- Add new products.
- Update product information.
- Delete products.
- Search and manage products.

### 3. Inventory Management
- Track available stock.
- Add and remove stock.
- Monitor low-stock products.
- Maintain stock history.
- View inventory value.

### 4. Sales Management
- Create new sales.
- Select customers and products.
- Calculate subtotal, discount, and tax.
- Manage payment methods.
- Generate customer invoices.

### 5. Customer Management
- Add customers.
- Edit customer details.
- Delete customer records.
- View customer purchase history.

### 6. Supplier Management
- Add and manage suppliers.
- Update supplier information.
- Track supplier purchases.
- Maintain supplier records.

### 7. Purchase Management
- Record new purchases.
- Select suppliers and products.
- Update inventory automatically.
- Track payment status.

### 8. Reports & Settings
- Monitor business performance.
- View sales reports.
- Manage application settings.
- Configure company information.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Framework |
| SQLite | Database Management |
| HTML5 | Web Page Structure |
| CSS3 | Styling |
| JavaScript | Frontend Interactions |
| Bootstrap | Responsive UI Components |
| Flask-Login | User Authentication |
| Werkzeug | Password Hashing |

## 📂 Project Structure

```text
smart-inventory-sales-manager/
│
├── app.py
├── database.py
├── check_database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── products.html
│   ├── inventory.html
│   ├── customers.html
│   ├── suppliers.html
│   ├── sales.html
│   └── other HTML templates
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── inventory.db
```

*Note: The database file is generated locally and should not be committed to GitHub.*

## ⚙️ Installation & Setup

Follow these steps to run the project on your local computer.

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/smart-inventory-sales-manager.git
```

### Step 2: Open Project Directory

```bash
cd smart-inventory-sales-manager
```

### Step 3: Create Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Open in Browser

Visit:

```text
http://127.0.0.1:5000/
```

The application should now be running locally.

## 🗄️ Database

The project uses SQLite for storing application data.

The database manages:

- Admin accounts
- Products
- Customers
- Suppliers
- Sales records
- Sale items
- Purchase records
- Stock history
- Application settings

The database tables are initialized by the application.

## 🔐 Security Features

- Admin authentication.
- Password hashing using Werkzeug.
- Login-protected application routes.
- Session management using Flask-Login.
- Parameterized SQL queries.

**Security Note:** Configure a strong secret key using an environment variable before deployment. Never commit passwords, secret keys, or private business data to GitHub.

## 🚀 Future Improvements

- Cloud database integration.
- Advanced analytics dashboard.
- PDF and Excel report exports.
- Email notifications.
- Barcode scanning.
- Multiple user roles and permissions.
- Online deployment.
- Automated database backup.

## 🎓 Project Information

**Project Name:** Smart Inventory & Sales Manager

**Project Type:** Python Web Application

**Domain:** Inventory and Business Management

**Backend:** Python Flask

**Database:** SQLite

**Developed By:** Parveen Kumar

**GitHub:** [parveenkumar-code](https://github.com/parveenkumar-code)

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

If you want to contribute:

1. Fork this repository.
2. Create a feature branch.
3. Make your changes.
4. Commit your changes.
5. Submit a Pull Request.

## 📄 License

This project is developed for educational and learning purposes.

---

### ⭐ Support

If you find this project useful, please consider giving it a ⭐ on GitHub.

**Thank you for visiting Smart Inventory & Sales Manager!**
