# Book E-Store Database Schema

1. **Languages Table**
   Stores language information.

| Column Name   | Data Type   | Constraints/Notes | Foreign Key |
| :------------ | :---------- | :---------------- | :---------- |
| language_code | VARCHAR(10) | PK                |             |
| language_name | VARCHAR(50) | NOT NULL UNIQUE   |             |

2. **Authors Table**
   Stores information about book authors.

| Column Name | Data Type    | Constraints/Notes         | Foreign Key |
| :---------- | :----------- | :------------------------ | :---------- |
| author_id   | SERIAL       | PK                        |             |
| first_name  | VARCHAR(100) |                           |             |
| last_name   | VARCHAR(100) | NOT NULL                  |             |
| bio         | TEXT         | NULL                      |             |
| created_at  | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |             |
| updated_at  | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |             |

3. **Publishers Table**
   Stores information about book publishers.

| Column Name   | Data Type    | Constraints/Notes         | Foreign Key |
| :------------ | :----------- | :------------------------ | :---------- |
| publisher_id  | SERIAL       | PK                        |             |
| name          | VARCHAR(255) | NOT NULL UNIQUE           |             |
| contact_email | VARCHAR(255) | NULL                      |             |
| website       | VARCHAR(255) | NULL                      |             |
| created_at    | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |             |
| updated_at    | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |             |

4. **Categories Table**
   Stores book categories. Can be hierarchical.

| Column Name        | Data Type    | Constraints/Notes         | Foreign Key                |
| :----------------- | :----------- | :------------------------ | :------------------------- |
| category_id        | SERIAL       | PK                        |                            |
| name               | VARCHAR(100) | NOT NULL UNIQUE           |                            |
| description        | TEXT         | NULL                      |                            |
| parent_category_id | INT          | NULL, ON DELETE SET NULL  | -> Categories(category_id) |
| created_at         | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |                            |
| updated_at         | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |                            |

5. **Users Table**
   Stores user information (based on Flask model).

| Column Name   | Data Type    | Constraints/Notes         | Foreign Key |
| :------------ | :----------- | :------------------------ | :---------- |
| user_id       | SERIAL       | PK                        |             |
| username      | VARCHAR(80)  | UNIQUE NOT NULL           |             |
| email         | VARCHAR(120) | NOT NULL UNIQUE           |             |
| password_hash | VARCHAR(255) | NOT NULL                  |             |
| role          | VARCHAR(20)  | NOT NULL                  |             |
| created_at    | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |             |
| updated_at    | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP |             |

6. **Sellers Table**
   Stores information about users who are sellers.

| Column Name | Data Type    | Constraints/Notes                  | Foreign Key       |
| :---------- | :----------- | :--------------------------------- | :---------------- |
| seller_id   | SERIAL       | PK                                 |                   |
| user_id     | INT          | NOT NULL UNIQUE, ON DELETE CASCADE | -> Users(user_id) |
| store_name  | VARCHAR(255) | NOT NULL UNIQUE                    |                   |
| description | TEXT         | NULL                               |                   |
| is_active   | BOOLEAN      | DEFAULT TRUE                       |                   |
| created_at  | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP          |                   |
| updated_at  | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP          |                   |

7. **Addresses Table**
   Stores user addresses (shipping/billing).

| Column Name    | Data Type    | Constraints/Notes                                        | Foreign Key       |
| :------------- | :----------- | :------------------------------------------------------- | :---------------- |
| address_id     | SERIAL       | PK                                                       |                   |
| user_id        | INT          | NOT NULL, ON DELETE CASCADE                              | -> Users(user_id) |
| address_type   | VARCHAR(20)  | NOT NULL CHECK (address_type IN ('shipping', 'billing')) |                   |
| street_address | VARCHAR(255) | NOT NULL                                                 |                   |
| city           | VARCHAR(100) | NOT NULL                                                 |                   |
| state_province | VARCHAR(100) | NULL                                                     |                   |
| postal_code    | VARCHAR(20)  | NOT NULL                                                 |                   |
| country        | VARCHAR(100) | NOT NULL                                                 |                   |
| is_default     | BOOLEAN      | DEFAULT FALSE                                            |                   |
| created_at     | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP                                |                   |
| updated_at     | TIMESTAMPTZ  | DEFAULT CURRENT_TIMESTAMP                                |                   |

8. **Books Table**
   Core table for abstract book metadata.

| Column Name      | Data Type     | Constraints/Notes                                                | Foreign Key                 |
| :--------------- | :------------ | :--------------------------------------------------------------- | :-------------------------- |
| book_id          | SERIAL        | PK                                                               |                             |
| isbn             | VARCHAR(20)   | NOT NULL UNIQUE                                                  |                             |
| title            | VARCHAR(255)  | NOT NULL                                                         |                             |
| description      | TEXT          | NULL                                                             |                             |
| publisher_id     | INT           | ON DELETE SET NULL                                               | -> Publishers(publisher_id) |
| publication_date | DATE          | NULL                                                             |                             |
| num_pages        | INT           | NULL CHECK (num_pages > 0)                                       |                             |
| language_code    | VARCHAR(10)   | ON DELETE SET NULL                                               | -> Languages(language_code) |
| cover_image_url  | VARCHAR(512)  | NULL                                                             |                             |
| average_rating   | DECIMAL(3, 2) | DEFAULT 0.00 CHECK (average_rating >= 0 AND average_rating <= 5) |                             |
| created_at       | TIMESTAMPTZ   | DEFAULT CURRENT_TIMESTAMP                                        |                             |
| updated_at       | TIMESTAMPTZ   | DEFAULT CURRENT_TIMESTAMP                                        |                             |

9. **Inventory Table**
   Stores specific listings/offers of books by sellers.

| Column Name           | Data Type      | Constraints/Notes                                                                                                     | Foreign Key           |
| :-------------------- | :------------- | :-------------------------------------------------------------------------------------------------------------------- | :-------------------- |
| inventory_id          | SERIAL         | PK                                                                                                                    |                       |
| book_id               | INT            | NOT NULL, ON DELETE CASCADE                                                                                           | -> Books(book_id)     |
| seller_id             | INT            | NOT NULL, ON DELETE CASCADE                                                                                           | -> Sellers(seller_id) |
| price                 | DECIMAL(10, 2) | NOT NULL CHECK (price >= 0)                                                                                           |                       |
| quantity              | INT            | NOT NULL DEFAULT 0 CHECK (quantity >= 0)                                                                              |                       |
| condition             | VARCHAR(50)    | DEFAULT 'New' CHECK (condition IN ('New', 'Used - Like New', 'Used - Very Good', 'Used - Good', 'Used - Acceptable')) |                       |
| condition_description | TEXT           | NULL                                                                                                                  |                       |
| is_active             | BOOLEAN        | DEFAULT TRUE                                                                                                          |                       |
| created_at            | TIMESTAMPTZ    | DEFAULT CURRENT_TIMESTAMP                                                                                             |                       |
| updated_at            | TIMESTAMPTZ    | DEFAULT CURRENT_TIMESTAMP                                                                                             |                       |
|                       |                | UNIQUE (book_id, seller_id, condition)                                                                                |                       |

10. **BookAuthors Table (Join Table)**
    Links books to their authors (Many-to-Many).

| Column Name | Data Type | Constraints/Notes               | Foreign Key           |
| :---------- | :-------- | :------------------------------ | :-------------------- |
| book_id     | INT       | NOT NULL, PK, ON DELETE CASCADE | -> Books(book_id)     |
| author_id   | INT       | NOT NULL, PK, ON DELETE CASCADE | -> Authors(author_id) |

11. **BookCategories Table (Join Table)**
    Links books to their categories (Many-to-Many).

| Column Name | Data Type | Constraints/Notes               | Foreign Key                |
| :---------- | :-------- | :------------------------------ | :------------------------- |
| book_id     | INT       | NOT NULL, PK, ON DELETE CASCADE | -> Books(book_id)          |
| category_id | INT       | NOT NULL, PK, ON DELETE CASCADE | -> Categories(category_id) |

12. **Reviews Table**
    Stores user reviews for books.

| Column Name | Data Type   | Constraints/Notes                            | Foreign Key       |
| :---------- | :---------- | :------------------------------------------- | :---------------- |
| review_id   | SERIAL      | PK                                           |                   |
| book_id     | INT         | NOT NULL, ON DELETE CASCADE                  | -> Books(book_id) |
| user_id     | INT         | NOT NULL, ON DELETE CASCADE                  | -> Users(user_id) |
| rating      | INT         | NOT NULL CHECK (rating >= 1 AND rating <= 5) |                   |
| review_text | TEXT        | NULL                                         |                   |
| review_date | TIMESTAMPTZ | DEFAULT CURRENT_TIMESTAMP                    |                   |
| is_approved | BOOLEAN     | DEFAULT FALSE                                |                   |
|             |             | UNIQUE (book_id, user_id)                    |                   |

13. **Orders Table**
    Stores information about customer orders.

| Column Name         | Data Type      | Constraints/Notes                                                                                                       | Foreign Key              |
| :------------------ | :------------- | :---------------------------------------------------------------------------------------------------------------------- | :----------------------- |
| order_id            | SERIAL         | PK                                                                                                                      |                          |
| user_id             | INT            | NOT NULL, ON DELETE RESTRICT                                                                                            | -> Users(user_id)        |
| order_date          | TIMESTAMPTZ    | DEFAULT CURRENT_TIMESTAMP                                                                                               |                          |
| status              | VARCHAR(50)    | NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')) |                          |
| total_amount        | DECIMAL(12, 2) | NOT NULL CHECK (total_amount >= 0)                                                                                      |                          |
| shipping_address_id | INT            | ON DELETE RESTRICT                                                                                                      | -> Addresses(address_id) |
| billing_address_id  | INT            | ON DELETE RESTRICT                                                                                                      | -> Addresses(address_id) |
| shipping_method     | VARCHAR(100)   | NULL                                                                                                                    |                          |
| tracking_number     | VARCHAR(100)   | NULL                                                                                                                    |                          |
| updated_at          | TIMESTAMPTZ    | DEFAULT CURRENT_TIMESTAMP                                                                                               |                          |

14. **OrderItems Table**
    Stores details of specific inventory items within each order.

| Column Name           | Data Type      | Constraints/Notes             | Foreign Key                |
| :-------------------- | :------------- | :---------------------------- | :------------------------- |
| order_item_id         | SERIAL         | PK                            |                            |
| order_id              | INT            | NOT NULL, ON DELETE CASCADE   | -> Orders(order_id)        |
| inventory_id          | INT            | NOT NULL, ON DELETE RESTRICT  | -> Inventory(inventory_id) |
| book_id               | INT            | NOT NULL, ON DELETE RESTRICT  | -> Books(book_id)          |
| seller_id             | INT            | NOT NULL, ON DELETE RESTRICT  | -> Sellers(seller_id)      |
| quantity              | INT            | NOT NULL CHECK (quantity > 0) |                            |
| price_per_item        | DECIMAL(10, 2) | NOT NULL                      |                            |
| condition_at_purchase | VARCHAR(50)    | NOT NULL                      |                            |
