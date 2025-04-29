# 1. Book

- id (Primary Key)
- title
- publisher_id (Foreign Key -> Publisher.id)
- description
- rating (DECIMAL/FLOAT, derived, nullable) # Needs update logic
- quantity (INTEGER, CHECK >= 0)
- price (DECIMAL(10, 2), CHECK > 0) # Example precision
- discount_percent (INTEGER, CHECK BETWEEN 0 AND 100, DEFAULT 0)
- image_url_1 (VARCHAR, nullable)
- image_url_2 (VARCHAR, nullable)
- image_url_3 (VARCHAR, nullable)
- seller_id (Foreign Key -> Seller.id) # Ignoring Seller table itself as requested
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

# 2. Author

- id (Primary Key)
- first_name
- last_name
- bio (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

# 3. Publisher

- id (Primary Key)
- name (VARCHAR, UNIQUE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

# 4. Category

- id (Primary Key)
- name (VARCHAR, UNIQUE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

# 5. User (Assumed - needed for Ratings)

# - id (Primary Key)

# ... other user fields (username, email, password_hash, etc.)

# - created_at (TIMESTAMP)

# - updated_at (TIMESTAMP)

# 6. Rating

- id (Primary Key)
- user_id (Foreign Key -> User.id)
- book_id (Foreign Key -> Book.id)
- score (INTEGER, CHECK BETWEEN 1 AND 5)
- text (TEXT, nullable)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

# 7. BookAuthor (Join Table for Many-to-Many)

- book_id (Foreign Key -> Book.id)
- author_id (Foreign Key -> Author.id)
- PRIMARY KEY (book_id, author_id) # Composite primary key

# 8. BookCategory (Join Table for Many-to-Many)

- book_id (Foreign Key -> Book.id)
- category_id (Foreign Key -> Category.id)
- PRIMARY KEY (book_id, category_id) # Composite primary key

# 9. Seller (Structure shown, but ignored per request)

# - id (Primary Key)

# - name

# ... other seller fields

# - created_at (TIMESTAMP)

# - updated_at (TIMESTAMP)

final_project_backend
├── .env
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── simple-db.md
├── test_config.py
├── uv.lock
├── instance
├── src
│ ├── run.py
│ ├── app
│ │ ├── **init**.py
│ │ ├── config.py
│ │ ├── extensions.py
│ │ ├── seed.py
│ │ │ ├── **init**.cpython-311.pyc
│ │ │ ├── config.cpython-311.pyc
│ │ │ ├── extensions.cpython-311.pyc
│ │ │ └── seed.cpython-311.pyc
│ │ ├── model
│ │ │ ├── **init**.py
│ │ │ ├── author.py
│ │ │ ├── book_author_table.py
│ │ │ ├── book_category_table.py
│ │ │ ├── book.py
│ │ │ ├── category.py
│ │ │ ├── publisher.py
│ │ │ ├── rating.py
│ │ │ ├── seller.py
│ │ │ ├── user.py
│ │ ├── routes
│ │ │ ├── **init**.py
│ │ │ └── books.py
│ │ └── services
│ │ ├── **init**.py
│ │ └── average_rating.py
│ └── final_project_backend.egg-info
│ ├── dependency_links.txt
│ ├── PKG-INFO
│ ├── requires.txt
│ ├── SOURCES.txt
│ └── top_level.txt
└── test
└── **init**.py
