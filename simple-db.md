# 1. Book

- id (primary key)
- title
- author (foreign key from "Author" table)
- publisher (foreign key from "Publisher" table)
- description
- category (this book can have multiple categories)
- rating (average rating of the book)
- quantity
- price (must above 0)
- discount (greater or equal to zero. range between (0.1 - 1))
- image url 1
- image url 2
- image url 3
- seller (foreign key from "Seller" table)
- created at
- updated at

# 2. Rating

- id (primary key)
- poster (foreign key from "User" table)
- score (from 1-5)
- text
- book id (foreign key from "Book" table. for which book is reviewed)
- created at
- updated at

# 3. Category

- id (primary key)
- name
- book id (foreign from "Book" table key)
- created at
- updated at

# 4. Author

- id (primary key)
- first_name
- last_name
- bio
- book id (foregin key from "Book" table. for book they wrote)
- created at
- updated at

# 5. Publisher

- id - (primary key)
- name
- book id (foregin key from "Book" table. for book they published)
- created at
- updated at

# 6. Seller (It's not my job to make it. So, ignore it)
