# Book E-Store Database Model Plan

This document outlines the plan to create SQLAlchemy models for a book e-store database, based on the provided relational data structure.

## 1. Books Table

- **Model Class:** `Book`
- **Table Name:** `books`
- **Purpose:** Stores information about individual book editions.

| Column Name        | Data Type        | Constraints                                       |
| ------------------ | ---------------- | ------------------------------------------------- |
| `book_id`          | `db.Integer`     | Primary Key, Auto-incrementing                    |
| `isbn`             | `db.String(20)`  | Unique, Not Null                                  |
| `title`            | `db.String(255)` | Not Null                                          |
| `description`      | `db.Text`        |                                                   |
| `publisher_id`     | `db.Integer`     | Foreign Key referencing `publishers.publisher_id` |
| `publication_date` | `db.Date`        |                                                   |
| `language`         | `db.String(50)`  |                                                   |
| `num_pages`        | `db.Integer`     |                                                   |
| `format`           | `db.String(50)`  |                                                   |
| `cover_image_url`  | `db.String(255)` |                                                   |

## 2. Authors Table

- **Model Class:** `Author`
- **Table Name:** `authors`
- **Purpose:** Stores information about book authors.

| Column Name   | Data Type        | Constraints                    |
| ------------- | ---------------- | ------------------------------ |
| `author_id`   | `db.Integer`     | Primary Key, Auto-incrementing |
| `author_name` | `db.String(255)` | Not Null                       |
| `bio`         | `db.Text`        | Optional                       |

## 3. BookAuthors Table (Linking Table)

- **Model Class:** `BookAuthor`
- **Table Name:** `book_authors`
- **Purpose:** Links Books and Authors for a many-to-many relationship.

| Column Name | Data Type    | Constraints                                    |
| ----------- | ------------ | ---------------------------------------------- |
| `book_id`   | `db.Integer` | Foreign Key referencing `books.book_id`        |
| `author_id` | `db.Integer` | Foreign Key referencing `authors.author_id`    |
|             |              | Composite Primary Key (`book_id`, `author_id`) |

## 4. Genres Table

- **Model Class:** `Genre`
- **Table Name:** `genres`
- **Purpose:** Stores book categories/genres.

| Column Name  | Data Type        | Constraints                    |
| ------------ | ---------------- | ------------------------------ |
| `genre_id`   | `db.Integer`     | Primary Key, Auto-incrementing |
| `genre_name` | `db.String(100)` | Unique, Not Null               |

## 5. BookGenres Table (Linking Table)

- **Model Class:** `BookGenre`
- **Table Name:** `book_genres`
- **Purpose:** Links Books and Genres for a many-to-many relationship.

| Column Name | Data Type    | Constraints                                   |
| ----------- | ------------ | --------------------------------------------- |
| `book_id`   | `db.Integer` | Foreign Key referencing `books.book_id`       |
| `genre_id`  | `db.Integer` | Foreign Key referencing `genres.genre_id`     |
|             |              | Composite Primary Key (`book_id`, `genre_id`) |

## 6. Publishers Table

- **Model Class:** `Publisher`
- **Table Name:** `publishers`
- **Purpose:** Stores information about book publishers.

| Column Name      | Data Type        | Constraints                    |
| ---------------- | ---------------- | ------------------------------ |
| `publisher_id`   | `db.Integer`     | Primary Key, Auto-incrementing |
| `publisher_name` | `db.String(255)` | Unique, Not Null               |

## 7. Stores Table

- **Model Class:** `Store`
- **Table Name:** `stores`
- **Purpose:** Stores information about physical locations, warehouses, or online storefronts.

| Column Name  | Data Type        | Constraints                    |
| ------------ | ---------------- | ------------------------------ |
| `store_id`   | `db.Integer`     | Primary Key, Auto-incrementing |
| `store_name` | `db.String(255)` | Not Null                       |
| `location`   | `db.Text`        | Optional                       |

## 8. Inventory/ProductListings Table

- **Model Class:** `ProductListing`
- **Table Name:** `product_listings`
- **Purpose:** Stores selling information for books at specific stores.

| Column Name           | Data Type           | Constraints                                                    |
| --------------------- | ------------------- | -------------------------------------------------------------- |
| `listing_id`          | `db.Integer`        | Primary Key, Auto-incrementing                                 |
| `book_id`             | `db.Integer`        | Foreign Key referencing `books.book_id`, Not Null              |
| `store_id`            | `db.Integer`        | Foreign Key referencing `stores.store_id`, Not Null            |
| `price`               | `db.Numeric(10, 2)` | Not Null                                                       |
| `discount_percentage` | `db.Numeric(5, 2)`  | Default 0.0                                                    |
| `stock_quantity`      | `db.Integer`        | Default 0, Not Null                                            |
| `sku`                 | `db.String(100)`    | Optional, Unique per store (needs composite unique constraint) |
| `is_active`           | `db.Boolean`        | Default TRUE, Not Null                                         |

## 9. Reviews Table

- **Model Class:** `Review`
- **Table Name:** `reviews`
- **Purpose:** Stores individual book reviews and ratings.

| Column Name   | Data Type     | Constraints                                       |
| ------------- | ------------- | ------------------------------------------------- |
| `review_id`   | `db.Integer`  | Primary Key, Auto-incrementing                    |
| `book_id`     | `db.Integer`  | Foreign Key referencing `books.book_id`, Not Null |
| `user_id`     | `db.Integer`  | Foreign Key referencing `users.id`, Not Null      |
| `rating`      | `db.Integer`  | Not Null (e.g., 1-5)                              |
| `review_text` | `db.Text`     | Optional                                          |
| `review_date` | `db.DateTime` | Default `datetime.utcnow`, Not Null               |

## Implementation Steps:

1. Create new Python files for each model in the `src/app/model/` directory (e.g., `book.py`, `author.py`, `publisher.py`, etc.).
2. Define each SQLAlchemy model class within its respective file, inheriting from `db.Model`.
3. Define the table name using `__tablename__`.
4. Define each column using `db.Column` with the appropriate data type and constraints.
5. Define relationships between models using `db.relationship` and `db.ForeignKey` where necessary, especially for the many-to-many relationships using the linking tables.
6. Add `__repr__` methods to each model for better representation.
7. Import necessary modules (e.g., `db` from `..extensions`, `datetime` from `datetime`).
8. Update `src/app/model/__init__.py` to import all the new models.
9. Consider adding appropriate indexes for performance optimization.
10. Implement database migrations (e.g., using Flask-Migrate) to create these tables in the database.
