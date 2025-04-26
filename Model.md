# Book E-Store Database Schema (Flask-SQLAlchemy)

This document describes the database schema using Flask-SQLAlchemy conventions.

---

## 1. Language Model (`Language`)

Stores language information.

| Column Name     | SQLAlchemy Type | Constraints/Notes               | Relationship / FK Target |
| :-------------- | :-------------- | :------------------------------ | :----------------------- |
| `language_code` | `db.String(10)` | `primary_key=True`              |                          |
| `language_name` | `db.String(50)` | `nullable=False`, `unique=True` |                          |

---

## 2. Author Model (`Author`)

Stores information about book authors.

| Column Name  | SQLAlchemy Type              | Constraints/Notes                                                | Relationship / FK Target    |
| :----------- | :--------------------------- | :--------------------------------------------------------------- | :-------------------------- |
| `id`         | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                           |                             |
| `first_name` | `db.String(100)`             | `nullable=True`                                                  |                             |
| `last_name`  | `db.String(100)`             | `nullable=False`                                                 |                             |
| `bio`        | `db.Text`                    | `nullable=True`                                                  |                             |
| `created_at` | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                   |                             |
| `updated_at` | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`         |                             |
| `books`      | `db.relationship`            | `'Book'`, `secondary='book_authors'`, `back_populates='authors'` | `Book` (via `book_authors`) |

---

## 3. Publisher Model (`Publisher`)

Stores information about book publishers.

| Column Name     | SQLAlchemy Type              | Constraints/Notes                                        | Relationship / FK Target |
| :-------------- | :--------------------------- | :------------------------------------------------------- | :----------------------- |
| `id`            | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                   |                          |
| `name`          | `db.String(255)`             | `nullable=False`, `unique=True`                          |                          |
| `contact_email` | `db.String(255)`             | `nullable=True`                                          |                          |
| `website`       | `db.String(255)`             | `nullable=True`                                          |                          |
| `created_at`    | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                           |                          |
| `updated_at`    | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()` |                          |
| `books`         | `db.relationship`            | `'Book'`, `back_populates='publisher'`                   | `Book`                   |

---

## 4. Category Model (`Category`)

Stores book categories. Can be hierarchical.

| Column Name          | SQLAlchemy Type              | Constraints/Notes                                                      | Relationship / FK Target       |
| :------------------- | :--------------------------- | :--------------------------------------------------------------------- | :----------------------------- |
| `id`                 | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                                 |                                |
| `name`               | `db.String(100)`             | `nullable=False`, `unique=True`                                        |                                |
| `description`        | `db.Text`                    | `nullable=True`                                                        |                                |
| `parent_category_id` | `db.Integer`                 | `db.ForeignKey('categories.id', ondelete='SET NULL')`, `nullable=True` | `Category` (`id`)              |
| `created_at`         | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                         |                                |
| `updated_at`         | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`               |                                |
| `parent`             | `db.relationship`            | `'Category'`, `remote_side=[id]`, `back_populates='children'`          | `Category`                     |
| `children`           | `db.relationship`            | `'Category'`, `back_populates='parent'`                                | `Category`                     |
| `books`              | `db.relationship`            | `'Book'`, `secondary='book_categories'`, `back_populates='categories'` | `Book` (via `book_categories`) |

---

## 5. User Model (`User`)

Stores user information (based on Flask model).

| Column Name      | SQLAlchemy Type              | Constraints/Notes                                                                    | Relationship / FK Target |
| :--------------- | :--------------------------- | :----------------------------------------------------------------------------------- | :----------------------- |
| `id`             | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                                               |                          |
| `username`       | `db.String(80)`              | `unique=True`, `nullable=False`                                                      |                          |
| `email`          | `db.String(120)`             | `unique=True`, `nullable=False`                                                      |                          |
| `password_hash`  | `db.String(255)`             | `nullable=False`                                                                     |                          |
| `role`           | `db.String(20)`              | `nullable=False` (e.g., 'customer', 'seller', 'admin')                               |                          |
| `created_at`     | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                                       |                          |
| `updated_at`     | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`                             |                          |
| `seller_profile` | `db.relationship`            | `'Seller'`, `back_populates='user'`, `uselist=False`, `cascade='all, delete-orphan'` | `Seller`                 |
| `addresses`      | `db.relationship`            | `'Address'`, `back_populates='user'`, `cascade='all, delete-orphan'`                 | `Address`                |
| `reviews`        | `db.relationship`            | `'Review'`, `back_populates='user'`, `cascade='all, delete-orphan'`                  | `Review`                 |
| `orders`         | `db.relationship`            | `'Order'`, `back_populates='user'`                                                   | `Order`                  |

_Note: Fields like `balance`, `referral_code`, `referred_by` from the original Flask model are kept application-level._

---

## 6. Seller Model (`Seller`)

Stores information about users who are sellers.

| Column Name   | SQLAlchemy Type              | Constraints/Notes                                                                | Relationship / FK Target |
| :------------ | :--------------------------- | :------------------------------------------------------------------------------- | :----------------------- |
| `id`          | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                                           |                          |
| `user_id`     | `db.Integer`                 | `db.ForeignKey('users.id', ondelete='CASCADE')`, `unique=True`, `nullable=False` | `User` (`id`)            |
| `store_name`  | `db.String(255)`             | `nullable=False`, `unique=True`                                                  |                          |
| `description` | `db.Text`                    | `nullable=True`                                                                  |                          |
| `is_active`   | `db.Boolean`                 | `default=True`                                                                   |                          |
| `created_at`  | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                                   |                          |
| `updated_at`  | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`                         |                          |
| `user`        | `db.relationship`            | `'User'`, `back_populates='seller_profile'`                                      | `User`                   |
| `inventory`   | `db.relationship`            | `'Inventory'`, `back_populates='seller'`, `cascade='all, delete-orphan'`         | `Inventory`              |
| `order_items` | `db.relationship`            | `'OrderItem'`, `back_populates='seller'`                                         | `OrderItem`              |

---

## 7. Address Model (`Address`)

Stores user addresses (shipping/billing).

| Column Name       | SQLAlchemy Type              | Constraints/Notes                                                                          | Relationship / FK Target |
| :---------------- | :--------------------------- | :----------------------------------------------------------------------------------------- | :----------------------- |
| `id`              | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                                                     |                          |
| `user_id`         | `db.Integer`                 | `db.ForeignKey('users.id', ondelete='CASCADE')`, `nullable=False`                          | `User` (`id`)            |
| `address_type`    | `db.String(20)`              | `nullable=False` (CHECK constraint: 'shipping' or 'billing')                               |                          |
| `street_address`  | `db.String(255)`             | `nullable=False`                                                                           |                          |
| `city`            | `db.String(100)`             | `nullable=False`                                                                           |                          |
| `state_province`  | `db.String(100)`             | `nullable=True`                                                                            |                          |
| `postal_code`     | `db.String(20)`              | `nullable=False`                                                                           |                          |
| `country`         | `db.String(100)`             | `nullable=False`                                                                           |                          |
| `is_default`      | `db.Boolean`                 | `default=False`                                                                            |                          |
| `created_at`      | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                                             |                          |
| `updated_at`      | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`                                   |                          |
| `user`            | `db.relationship`            | `'User'`, `back_populates='addresses'`                                                     | `User`                   |
| `shipping_orders` | `db.relationship`            | `'Order'`, `foreign_keys='Order.shipping_address_id'`, `back_populates='shipping_address'` | `Order`                  |
| `billing_orders`  | `db.relationship`            | `'Order'`, `foreign_keys='Order.billing_address_id'`, `back_populates='billing_address'`   | `Order`                  |

---

## 8. Book Model (`Book`)

The core model for abstract book metadata.

| Column Name        | SQLAlchemy Type              | Constraints/Notes                                                                | Relationship / FK Target           |
| :----------------- | :--------------------------- | :------------------------------------------------------------------------------- | :--------------------------------- |
| `id`               | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                                           |                                    |
| `isbn`             | `db.String(20)`              | `nullable=False`, `unique=True`                                                  |                                    |
| `title`            | `db.String(255)`             | `nullable=False`                                                                 |                                    |
| `description`      | `db.Text`                    | `nullable=True`                                                                  |                                    |
| `publisher_id`     | `db.Integer`                 | `db.ForeignKey('publishers.id', ondelete='SET NULL')`, `nullable=True`           | `Publisher` (`id`)                 |
| `publication_date` | `db.Date`                    | `nullable=True`                                                                  |                                    |
| `num_pages`        | `db.Integer`                 | `nullable=True` (CHECK constraint: > 0)                                          |                                    |
| `language_code`    | `db.String(10)`              | `db.ForeignKey('languages.language_code', ondelete='SET NULL')`, `nullable=True` | `Language` (`language_code`)       |
| `cover_image_url`  | `db.String(512)`             | `nullable=True`                                                                  |                                    |
| `average_rating`   | `db.Numeric(3, 2)`           | `default=0.00` (CHECK constraint: 0-5)                                           |                                    |
| `created_at`       | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                                   |                                    |
| `updated_at`       | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`                         |                                    |
| `publisher`        | `db.relationship`            | `'Publisher'`, `back_populates='books'`                                          | `Publisher`                        |
| `language`         | `db.relationship`            | `'Language'`                                                                     | `Language`                         |
| `authors`          | `db.relationship`            | `'Author'`, `secondary='book_authors'`, `back_populates='books'`                 | `Author` (via `book_authors`)      |
| `categories`       | `db.relationship`            | `'Category'`, `secondary='book_categories'`, `back_populates='books'`            | `Category` (via `book_categories`) |
| `inventory_items`  | `db.relationship`            | `'Inventory'`, `back_populates='book'`, `cascade='all, delete-orphan'`           | `Inventory`                        |
| `reviews`          | `db.relationship`            | `'Review'`, `back_populates='book'`, `cascade='all, delete-orphan'`              | `Review`                           |
| `order_items`      | `db.relationship`            | `'OrderItem'`, `back_populates='book'`                                           | `OrderItem`                        |

---

## 9. Inventory Model (`Inventory`)

Stores specific listings/offers of books by sellers.

| Column Name             | SQLAlchemy Type              | Constraints/Notes                                                   | Relationship / FK Target |
| :---------------------- | :--------------------------- | :------------------------------------------------------------------ | :----------------------- |
| `id`                    | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                              |                          |
| `book_id`               | `db.Integer`                 | `db.ForeignKey('books.id', ondelete='CASCADE')`, `nullable=False`   | `Book` (`id`)            |
| `seller_id`             | `db.Integer`                 | `db.ForeignKey('sellers.id', ondelete='CASCADE')`, `nullable=False` | `Seller` (`id`)          |
| `price`                 | `db.Numeric(10, 2)`          | `nullable=False` (CHECK constraint: >= 0)                           |                          |
| `quantity`              | `db.Integer`                 | `nullable=False`, `default=0` (CHECK constraint: >= 0)              |                          |
| `condition`             | `db.String(50)`              | `default='New'` (CHECK constraint: valid conditions)                |                          |
| `condition_description` | `db.Text`                    | `nullable=True`                                                     |                          |
| `is_active`             | `db.Boolean`                 | `default=True`                                                      |                          |
| `created_at`            | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                      |                          |
| `updated_at`            | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`            |                          |
| `book`                  | `db.relationship`            | `'Book'`, `back_populates='inventory_items'`                        | `Book`                   |
| `seller`                | `db.relationship`            | `'Seller'`, `back_populates='inventory'`                            | `Seller`                 |
| `order_items`           | `db.relationship`            | `'OrderItem'`, `back_populates='inventory_item'`                    | `OrderItem`              |
|                         |                              | `UniqueConstraint('book_id', 'seller_id', 'condition')`             |                          |

---

## 10. BookAuthors Association Table (`book_authors`)

Links books to their authors (Many-to-Many). Defined using `db.Table`.

| Column Name | SQLAlchemy Type | Constraints/Notes                                                     |
| :---------- | :-------------- | :-------------------------------------------------------------------- |
| `book_id`   | `db.Integer`    | `db.ForeignKey('books.id', ondelete='CASCADE')`, `primary_key=True`   |
| `author_id` | `db.Integer`    | `db.ForeignKey('authors.id', ondelete='CASCADE')`, `primary_key=True` |

---

## 11. BookCategories Association Table (`book_categories`)

Links books to their categories (Many-to-Many). Defined using `db.Table`.

| Column Name   | SQLAlchemy Type | Constraints/Notes                                                        |
| :------------ | :-------------- | :----------------------------------------------------------------------- |
| `book_id`     | `db.Integer`    | `db.ForeignKey('books.id', ondelete='CASCADE')`, `primary_key=True`      |
| `category_id` | `db.Integer`    | `db.ForeignKey('categories.id', ondelete='CASCADE')`, `primary_key=True` |

---

## 12. Review Model (`Review`)

Stores user reviews for books.

| Column Name   | SQLAlchemy Type              | Constraints/Notes                                                 | Relationship / FK Target |
| :------------ | :--------------------------- | :---------------------------------------------------------------- | :----------------------- |
| `id`          | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                            |                          |
| `book_id`     | `db.Integer`                 | `db.ForeignKey('books.id', ondelete='CASCADE')`, `nullable=False` | `Book` (`id`)            |
| `user_id`     | `db.Integer`                 | `db.ForeignKey('users.id', ondelete='CASCADE')`, `nullable=False` | `User` (`id`)            |
| `rating`      | `db.Integer`                 | `nullable=False` (CHECK constraint: 1-5)                          |                          |
| `review_text` | `db.Text`                    | `nullable=True`                                                   |                          |
| `review_date` | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                    |                          |
| `is_approved` | `db.Boolean`                 | `default=False`                                                   |                          |
| `book`        | `db.relationship`            | `'Book'`, `back_populates='reviews'`                              | `Book`                   |
| `user`        | `db.relationship`            | `'User'`, `back_populates='reviews'`                              | `User`                   |
|               |                              | `UniqueConstraint('book_id', 'user_id')`                          |                          |

---

## 13. Order Model (`Order`)

Stores information about customer orders.

| Column Name           | SQLAlchemy Type              | Constraints/Notes                                                                     | Relationship / FK Target |
| :-------------------- | :--------------------------- | :------------------------------------------------------------------------------------ | :----------------------- |
| `id`                  | `db.Integer`                 | `primary_key=True` (Auto-incrementing)                                                |                          |
| `user_id`             | `db.Integer`                 | `db.ForeignKey('users.id', ondelete='RESTRICT')`, `nullable=False`                    | `User` (`id`)            |
| `order_date`          | `db.DateTime(timezone=True)` | `server_default=db.func.now()`                                                        |                          |
| `status`              | `db.String(50)`              | `nullable=False`, `default='pending'` (CHECK constraint: valid statuses)              |                          |
| `total_amount`        | `db.Numeric(12, 2)`          | `nullable=False` (CHECK constraint: >= 0)                                             |                          |
| `shipping_address_id` | `db.Integer`                 | `db.ForeignKey('addresses.id', ondelete='RESTRICT')`, `nullable=True`                 | `Address` (`id`)         |
| `billing_address_id`  | `db.Integer`                 | `db.ForeignKey('addresses.id', ondelete='RESTRICT')`, `nullable=True`                 | `Address` (`id`)         |
| `shipping_method`     | `db.String(100)`             | `nullable=True`                                                                       |                          |
| `tracking_number`     | `db.String(100)`             | `nullable=True`                                                                       |                          |
| `updated_at`          | `db.DateTime(timezone=True)` | `server_default=db.func.now()`, `onupdate=db.func.now()`                              |                          |
| `user`                | `db.relationship`            | `'User'`, `back_populates='orders'`                                                   | `User`                   |
| `shipping_address`    | `db.relationship`            | `'Address'`, `foreign_keys=[shipping_address_id]`, `back_populates='shipping_orders'` | `Address`                |
| `billing_address`     | `db.relationship`            | `'Address'`, `foreign_keys=[billing_address_id]`, `back_populates='billing_orders'`   | `Address`                |
| `order_items`         | `db.relationship`            | `'OrderItem'`, `back_populates='order'`, `cascade='all, delete-orphan'`               | `OrderItem`              |

---

## 14. OrderItem Model (`OrderItem`)

Stores details of specific inventory items within each order.

| Column Name             | SQLAlchemy Type     | Constraints/Notes                                                      | Relationship / FK Target |
| :---------------------- | :------------------ | :--------------------------------------------------------------------- | :----------------------- |
| `id`                    | `db.Integer`        | `primary_key=True` (Auto-incrementing)                                 |                          |
| `order_id`              | `db.Integer`        | `db.ForeignKey('orders.id', ondelete='CASCADE')`, `nullable=False`     | `Order` (`id`)           |
| `inventory_id`          | `db.Integer`        | `db.ForeignKey('inventory.id', ondelete='RESTRICT')`, `nullable=False` | `Inventory` (`id`)       |
| `book_id`               | `db.Integer`        | `db.ForeignKey('books.id', ondelete='RESTRICT')`, `nullable=False`     | `Book` (`id`)            |
| `seller_id`             | `db.Integer`        | `db.ForeignKey('sellers.id', ondelete='RESTRICT')`, `nullable=False`   | `Seller` (`id`)          |
| `quantity`              | `db.Integer`        | `nullable=False` (CHECK constraint: > 0)                               |                          |
| `price_per_item`        | `db.Numeric(10, 2)` | `nullable=False`                                                       |                          |
| `condition_at_purchase` | `db.String(50)`     | `nullable=False`                                                       |                          |
| `order`                 | `db.relationship`   | `'Order'`, `back_populates='order_items'`                              | `Order`                  |
| `inventory_item`        | `db.relationship`   | `'Inventory'`, `back_populates='order_items'`                          | `Inventory`              |
| `book`                  | `db.relationship`   | `'Book'`, `back_populates='order_items'`                               | `Book`                   |
| `seller`                | `db.relationship`   | `'Seller'`, `back_populates='order_items'`                             | `Seller`                 |

---
