# CRUD Plan for Bookstore Models

This document outlines the CRUD operations, corresponding API endpoints, and role-based access control for the provided SQLAlchemy models.

---

## 1. User Model (`User`)

**Base Path:** `/api/v1/users`

| Operation  | HTTP Method | Endpoint             | Action                                       | Allowed Roles       | Notes                                              |
| :--------- | :---------- | :------------------- | :------------------------------------------- | :------------------ | :------------------------------------------------- |
| **Create** | `POST`      | `/register`          | Register a new user.                         | Guest               | Creates a `User` record with role 'User'.          |
| **Read**   | `GET`       | `/`                  | List all users (paginated).                  | Admin               |                                                    |
| **Read**   | `GET`       | `/me`                | Get current logged-in user's profile.        | User, Seller, Admin | Requires authentication.                           |
| **Read**   | `GET`       | `/{user_id}`         | Get a specific user's profile.               | Admin               | Potentially limited view for User/Seller roles.    |
| **Update** | `PATCH`     | `/me`                | Update current user's profile (e.g., email). | User, Seller, Admin | Requires authentication.                           |
| **Update** | `PATCH`     | `/me/password`       | Update current user's password.              | User, Seller, Admin | Requires current password verification.            |
| **Update** | `PATCH`     | `/{user_id}`         | Update any user's profile (e.g., role).      | Admin               |                                                    |
| **Update** | `PATCH`     | `/{user_id}/balance` | Update a user's balance.                     | Admin               | Use dedicated transaction endpoints for deposits.  |
| **Delete** | `DELETE`    | `/me`                | Delete current user's account.               | User, Seller, Admin | Requires confirmation. Cascades should be handled. |
| **Delete** | `DELETE`    | `/{user_id}`         | Delete any user's account.                   | Admin               | Cascades should be handled carefully.              |

---

## 2. Seller Model (`Seller`)

**Base Path:** `/api/v1/sellers`

| Operation  | HTTP Method | Endpoint       | Action                                        | Allowed Roles              | Notes                                                       |
| :--------- | :---------- | :------------- | :-------------------------------------------- | :------------------------- | :---------------------------------------------------------- |
| **Create** | `POST`      | `/`            | Create a seller profile for the current user. | User (Authenticated)       | Links to `User`, potentially changes user role to 'Seller'. |
| **Read**   | `GET`       | `/`            | List all sellers (paginated).                 | Guest, User, Seller, Admin | Public listing.                                             |
| **Read**   | `GET`       | `/me`          | Get the current user's seller profile.        | Seller, Admin              | Requires authentication.                                    |
| **Read**   | `GET`       | `/{seller_id}` | Get a specific seller's profile.              | Guest, User, Seller, Admin | Public profile view.                                        |
| **Update** | `PATCH`     | `/me`          | Update the current user's seller profile.     | Seller                     | Requires authentication. Can only update their own profile. |
| **Update** | `PATCH`     | `/{seller_id}` | Update any seller's profile.                  | Admin                      |                                                             |
| **Delete** | `DELETE`    | `/{seller_id}` | Delete a seller profile.                      | Admin                      | Consider implications for associated books and user role.   |

---

## 3. Book Model (`Book`)

**Base Path:** `/api/v1/books`

| Operation  | HTTP Method | Endpoint               | Action                                              | Allowed Roles              | Notes                                                                        |
| :--------- | :---------- | :--------------------- | :-------------------------------------------------- | :------------------------- | :--------------------------------------------------------------------------- |
| **Create** | `POST`      | `/`                    | Add a new book listing.                             | Seller, Admin              | `seller_id` linked to current user. Handle author/category linking.          |
| **Read**   | `GET`       | `/`                    | List all books (paginated, filterable, searchable). | Guest, User, Seller, Admin | Public listing. Filters: category, author, publisher, seller, price, rating. |
| **Read**   | `GET`       | `/{book_id}`           | Get details of a specific book.                     | Guest, User, Seller, Admin | Public detail view.                                                          |
| **Read**   | `GET`       | `/sellers/me`          | List books listed by the current seller.            | Seller                     | Requires authentication.                                                     |
| **Read**   | `GET`       | `/sellers/{seller_id}` | List books listed by a specific seller.             | Guest, User, Seller, Admin |                                                                              |
| **Update** | `PATCH`     | `/{book_id}`           | Update a book's details.                            | Seller, Admin              | Sellers can only update their own books. Admins can update any.              |
| **Delete** | `DELETE`    | `/{book_id}`           | Remove a book listing.                              | Seller, Admin              | Sellers can only delete their own books. Admins can delete any.              |

---

## 4. Author Model (`Author`)

**Base Path:** `/api/v1/authors`

| Operation  | HTTP Method | Endpoint             | Action                                    | Allowed Roles              | Notes                                                   |
| :--------- | :---------- | :------------------- | :---------------------------------------- | :------------------------- | :------------------------------------------------------ |
| **Create** | `POST`      | `/`                  | Add a new author.                         | Admin, Seller              | Sellers might add authors when listing new books.       |
| **Read**   | `GET`       | `/`                  | List all authors (paginated, searchable). | Guest, User, Seller, Admin | Public listing.                                         |
| **Read**   | `GET`       | `/{author_id}`       | Get details of a specific author.         | Guest, User, Seller, Admin | Public detail view.                                     |
| **Read**   | `GET`       | `/{author_id}/books` | List books by a specific author.          | Guest, User, Seller, Admin |                                                         |
| **Update** | `PATCH`     | `/{author_id}`       | Update an author's details.               | Admin                      |                                                         |
| **Delete** | `DELETE`    | `/{author_id}`       | Delete an author.                         | Admin                      | Consider impact on books (disassociate/prevent delete). |

---

## 5. Category Model (`Category`)

**Base Path:** `/api/v1/categories`

| Operation  | HTTP Method | Endpoint               | Action                                    | Allowed Roles              | Notes                                                   |
| :--------- | :---------- | :--------------------- | :---------------------------------------- | :------------------------- | :------------------------------------------------------ |
| **Create** | `POST`      | `/`                    | Add a new category.                       | Admin                      |                                                         |
| **Read**   | `GET`       | `/`                    | List all categories.                      | Guest, User, Seller, Admin | Public listing.                                         |
| **Read**   | `GET`       | `/{category_id}`       | Get details of a specific category.       | Guest, User, Seller, Admin | Public detail view.                                     |
| **Read**   | `GET`       | `/{category_id}/books` | List books within a specific category.    | Guest, User, Seller, Admin |                                                         |
| **Update** | `PATCH`     | `/{category_id}`       | Update a category's details (e.g., name). | Admin                      |                                                         |
| **Delete** | `DELETE`    | `/{category_id}`       | Delete a category.                        | Admin                      | Consider impact on books (disassociate/prevent delete). |

---

## 6. Publisher Model (`Publisher`)

**Base Path:** `/api/v1/publishers`

| Operation  | HTTP Method | Endpoint                | Action                                       | Allowed Roles              | Notes                                                |
| :--------- | :---------- | :---------------------- | :------------------------------------------- | :------------------------- | :--------------------------------------------------- |
| **Create** | `POST`      | `/`                     | Add a new publisher.                         | Admin, Seller              | Sellers might add publishers when listing new books. |
| **Read**   | `GET`       | `/`                     | List all publishers (paginated, searchable). | Guest, User, Seller, Admin | Public listing.                                      |
| **Read**   | `GET`       | `/{publisher_id}`       | Get details of a specific publisher.         | Guest, User, Seller, Admin | Public detail view.                                  |
| **Read**   | `GET`       | `/{publisher_id}/books` | List books by a specific publisher.          | Guest, User, Seller, Admin |                                                      |
| **Update** | `PATCH`     | `/{publisher_id}`       | Update a publisher's details.                | Admin                      |                                                      |
| **Delete** | `DELETE`    | `/{publisher_id}`       | Delete a publisher.                          | Admin                      | Consider impact on books (set null/prevent delete).  |

---

## 7. Rating Model (`Rating`)

**Base Path:** `/api/v1/ratings` (or nested)

| Operation  | HTTP Method | Endpoint                   | Action                                      | Allowed Roles              | Notes                                                                   |
| :--------- | :---------- | :------------------------- | :------------------------------------------ | :------------------------- | :---------------------------------------------------------------------- |
| **Create** | `POST`      | `/books/{book_id}/ratings` | Add a rating/review for a specific book.    | User, Seller               | Requires authentication. `user_id` is current user. Prevent duplicates. |
| **Read**   | `GET`       | `/books/{book_id}/ratings` | List all ratings for a specific book.       | Guest, User, Seller, Admin | Public listing.                                                         |
| **Read**   | `GET`       | `/users/me/ratings`        | List ratings submitted by the current user. | User, Seller, Admin        | Requires authentication.                                                |
| **Read**   | `GET`       | `/users/{user_id}/ratings` | List ratings submitted by a specific user.  | Admin                      |                                                                         |
| **Read**   | `GET`       | `/{rating_id}`             | Get a specific rating.                      | Admin                      | User/Seller can view their own.                                         |
| **Update** | `PATCH`     | `/{rating_id}`             | Update a rating/review.                     | User, Seller, Admin        | User/Seller can only update their own. Admins can update any.           |
| **Delete** | `DELETE`    | `/{rating_id}`             | Delete a rating/review.                     | User, Seller, Admin        | User/Seller can only delete their own. Admins can delete any.           |

---

**General Notes:**

- **Authentication:** Most endpoints require authentication (e.g., JWT). Public read endpoints are exceptions.
- **Authorization:** Middleware should enforce role checks for each endpoint.
- **Relationships:** Creating/updating resources like `Book` will need logic to handle linking/unlinking related entities (Authors, Categories).
- **Data Validation:** Input data for `POST` and `PATCH` requests must be validated.
- **Error Handling:** Implement standard HTTP status codes for errors (400, 401, 403, 404, 500).
- **Average Rating:** The `Book.rating` field should ideally be updated automatically via triggers or application logic whenever a `Rating` is added, updated, or deleted.
