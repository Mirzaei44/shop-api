# Shop API – Django REST Backend

This project is a production-style backend built with Django and Django REST Framework.

It simulates a simple e-commerce core system with:

- User authentication (Token-based)
- Product management
- Order lifecycle management
- Business rule enforcement
- Aggregations (totals, summaries)
- Filtering, search and ordering
- Pagination
- Automated tests
- Fake data seeding
- Swagger API documentation

The goal of this project was to build a clean, structured backend that reflects how real systems behave.

---

## What This Backend Does

Users can:

- Log in and receive a token
- View products
- Create draft orders
- Add items to an order
- Submit an order
- Pay an order
- Cancel an order (if not paid)

The system enforces real business logic:

- You cannot add items to a submitted order
- You cannot pay a draft order
- You cannot cancel a paid order
- Users only see their own orders
- Only admins can create/update/delete products

Orders move through a lifecycle:

draft → submitted → paid  
or  
draft → cancelled

Each order can calculate:

- number of items
- total quantity
- total price

All totals are calculated safely at database level using Django ORM expressions.

---

## Tech Stack

- Python
- Django
- Django REST Framework
- SQLite (development)
- Faker (seed data)
- Token Authentication
- drf-spectacular (Swagger docs)

---

## Project Structure (Simplified)

shop/
- models.py (Product, Order, OrderItem)
- serializers.py
- views.py (ViewSets + custom actions)
- tests.py
- management/commands/seed.py

core/
- settings.py
- urls.py

---

## Setup

Clone the repository:

git clone 
cd shop-api

Create virtual environment:

python -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run migrations:

python manage.py migrate

Run the server:

python manage.py runserver

---

## Authentication

Get token:

POST /api/token/

Body:

username=your_username  
password=your_password  

Then include header:

Authorization: Token YOUR_TOKEN

---





## Main Endpoints

Products:

GET /api/products/  
GET /api/products/?search=lap  
GET /api/products/?ordering=price  

Orders:

GET /api/orders/  
POST /api/orders/  

Add item:

POST /api/orders/{id}/items/

Submit:

POST /api/orders/{id}/submit/

Pay:

POST /api/orders/{id}/pay/

Cancel:

POST /api/orders/{id}/cancel/

Summary:

GET /api/orders/{id}/summary/

Total:

GET /api/orders/{id}/total/

---

## Swagger Documentation

Interactive API docs available at:

http://127.0.0.1:8001/api/docs/

This allows testing all endpoints directly from the browser.

---

## Fake Data

Seed data for testing:

python manage.py seed --users 50 --products 50 --orders 50 --max-items 10

Default credentials:

admin / admin123  
user1..userN / password123  

---


## Django Admin

The project includes Django Admin for internal data management.

Access:
http://127.0.0.1:8001/admin/

Admin credentials (after seeding):
admin / admin123



--- 

## Testing

Run automated tests:

python manage.py test

Tests cover:

- Authentication requirements
- Order isolation per user
- Order lifecycle logic
- Business rule enforcement

---

## What This Project Demonstrates

- Proper permission design
- Clean ViewSet usage
- Business logic in backend
- Aggregation queries with F expressions
- Custom API actions
- User data isolation
- Token-based authentication
- Structured testing
- API documentation

This is not just a CRUD project.  
It simulates a real backend domain with state transitions and validation rules.

---

## Notes

This project is built for demonstration and learning purposes.  
It focuses on backend structure, clarity, and business logic correctness.


