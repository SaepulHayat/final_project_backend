from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Assume 'db' is your SQLAlchemy instance initialized in your Flask app

# from your_app import db

db = SQLAlchemy() # Replace with your actual db instance

# Association Tables for Many-to-Many relationships

book_authors = db.Table('book_authors',
db.Column('book_id', db.Integer, db.ForeignKey('books.book_id', ondelete='CASCADE'), primary_key=True),
db.Column('author_id', db.Integer, db.ForeignKey('authors.author_id', ondelete='CASCADE'), primary_key=True)
)

book_categories = db.Table('book_categories',
db.Column('book_id', db.Integer, db.ForeignKey('books.book_id', ondelete='CASCADE'), primary_key=True),
db.Column('category_id', db.Integer, db.ForeignKey('categories.category_id', ondelete='CASCADE'), primary_key=True)
)

# --- Model Definitions ---

class Language(db.Model):
"""Model for the Languages table."""
**tablename** = "languages"

    language_code = db.Column(db.String(10), primary_key=True)
    language_name = db.Column(db.String(50), unique=True, nullable=False)

    # Relationship: One-to-Many with Books
    books = db.relationship('Book', back_populates='language')

    def __repr__(self):
        return f'<Language {self.language_code}: {self.language_name}>'

class Author(db.Model):
"""Model for the Authors table."""
**tablename** = "authors"

    author_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: Many-to-Many with Books (handled by book_authors table)
    # books relationship defined in Book model via secondary table

    def __repr__(self):
        return f'<Author {self.author_id}: {self.first_name} {self.last_name}>'

class Publisher(db.Model):
"""Model for the Publishers table."""
**tablename** = "publishers"

    publisher_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    contact_email = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: One-to-Many with Books
    books = db.relationship('Book', back_populates='publisher')

    def __repr__(self):
        return f'<Publisher {self.publisher_id}: {self.name}>'

class Category(db.Model):
"""Model for the Categories table."""
**tablename** = "categories"

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: Self-referential for hierarchy
    parent = db.relationship('Category', remote_side=[category_id], backref='subcategories')
    # Relationship: Many-to-Many with Books (handled by book_categories table)
    # books relationship defined in Book model via secondary table

    def __repr__(self):
        return f'<Category {self.category_id}: {self.name}>'

class User(db.Model):
"""Model for the Users table (matches provided definition)."""
**tablename** = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True, name='id') # Match Flask model 'id'
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # balance = db.Column(db.Numeric(10, 2), default=0.0) # Kept application level
    # referral_code = db.Column(db.String(10), unique=True, nullable=False) # Kept application level
    # referred_by = db.Column(db.String(10), nullable=True) # Kept application level
    role = db.Column(db.String(20), nullable=False) # e.g., 'customer', 'seller', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = db.relationship('Address', back_populates='user', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='user') # Don't cascade delete orders if user is deleted (use RESTRICT in DB)
    seller_profile = db.relationship('Seller', back_populates='user', uselist=False, cascade='all, delete-orphan') # One-to-One

    def __repr__(self):
        return f'<User {self.user_id}: {self.username}>'

class Seller(db.Model):
"""Model for the Sellers table."""
**tablename** = "sellers"

    seller_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    store_name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='seller_profile')
    inventory_items = db.relationship('Inventory', back_populates='seller', cascade='all, delete-orphan')
    # order_items relationship defined in OrderItem model

    def __repr__(self):
        return f'<Seller {self.seller_id}: {self.store_name}>'

class Address(db.Model):
"""Model for the Addresses table."""
**tablename** = "addresses"

    address_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    address_type = db.Column(db.String(20), nullable=False) # 'shipping' or 'billing'
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state_province = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='addresses')
    # shipping_orders relationship defined in Order model
    # billing_orders relationship defined in Order model

    def __repr__(self):
        return f'<Address {self.address_id} for User {self.user_id}>'

class Book(db.Model):
"""Model for the Books table (metadata only)."""
**tablename** = "books"

    book_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.publisher_id', ondelete='SET NULL'), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    num_pages = db.Column(db.Integer, nullable=True)
    language_code = db.Column(db.String(10), db.ForeignKey('languages.language_code', ondelete='SET NULL'), nullable=True)
    cover_image_url = db.Column(db.String(512), nullable=True)
    average_rating = db.Column(db.Numeric(3, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    publisher = db.relationship('Publisher', back_populates='books')
    language = db.relationship('Language', back_populates='books')
    authors = db.relationship('Author', secondary=book_authors, backref=db.backref('books', lazy='dynamic'))
    categories = db.relationship('Category', secondary=book_categories, backref=db.backref('books', lazy='dynamic'))
    inventory_items = db.relationship('Inventory', back_populates='book', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='book', cascade='all, delete-orphan')
    # order_items relationship defined in OrderItem model

    def __repr__(self):
        return f'<Book {self.book_id}: {self.title}>'

class Inventory(db.Model):
"""Model for the Inventory (Listings) table."""
**tablename** = "inventory"
**table_args** = (db.UniqueConstraint('book_id', 'seller_id', 'condition', name='uq_inventory_book_seller_condition'),)

    inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.seller_id', ondelete='CASCADE'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    condition = db.Column(db.String(50), default='New', nullable=False) # 'New', 'Used - Like New', etc.
    condition_description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    book = db.relationship('Book', back_populates='inventory_items')
    seller = db.relationship('Seller', back_populates='inventory_items')
    order_items = db.relationship('OrderItem', back_populates='inventory_item') # Don't cascade delete

    def __repr__(self):
        return f'<Inventory {self.inventory_id} for Book {self.book_id} by Seller {self.seller_id}>'

class Review(db.Model):
"""Model for the Reviews table."""
**tablename** = "reviews"
**table_args** = (db.UniqueConstraint('book_id', 'user_id', name='uq_review_book_user'),)

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    review_text = db.Column(db.Text, nullable=True)
    review_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)

    # Relationships
    book = db.relationship('Book', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

    def __repr__(self):
        return f'<Review {self.review_id} for Book {self.book_id} by User {self.user_id}>'

class Order(db.Model):
"""Model for the Orders table."""
**tablename** = "orders"

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False) # Buyer
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False) # 'pending', 'processing', etc.
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id', ondelete='RESTRICT'), nullable=True)
    billing_address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id', ondelete='RESTRICT'), nullable=True)
    shipping_method = db.Column(db.String(100), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    shipping_address = db.relationship('Address', foreign_keys=[shipping_address_id], backref='shipping_orders')
    billing_address = db.relationship('Address', foreign_keys=[billing_address_id], backref='billing_orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.order_id} by User {self.user_id}>'

class OrderItem(db.Model):
"""Model for the OrderItems table."""
**tablename** = "order_items"

    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.inventory_id', ondelete='RESTRICT'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id', ondelete='RESTRICT'), nullable=False) # Denormalized
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.seller_id', ondelete='RESTRICT'), nullable=False) # Denormalized
    quantity = db.Column(db.Integer, nullable=False)
    price_per_item = db.Column(db.Numeric(10, 2), nullable=False) # Price at time of order
    condition_at_purchase = db.Column(db.String(50), nullable=False) # Condition at time of order

    # Relationships
    order = db.relationship('Order', back_populates='items')
    inventory_item = db.relationship('Inventory', back_populates='order_items')
    book = db.relationship('Book', backref='order_items') # Simple backref ok here
    seller = db.relationship('Seller', backref='order_items') # Simple backref ok here

    def __repr__(self):
        return f'<OrderItem {self.order_item_id} for Order {self.order_id}>'
