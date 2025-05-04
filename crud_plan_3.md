# CRUD Plan for Bookstore Models

This document outlines the CRUD operations, corresponding API endpoints, and role-based access control for the provided SQLAlchemy models.

---

## 1. Seller Model (`Seller`)

| Operation  | Action                                        | Notes                                                       |
| :--------- | :-------------------------------------------- | :---------------------------------------------------------- |
| **Create** | Create a seller profile for the current user. | Links to `User`, potentially changes user role to 'Seller'. |
| **Read**   | List all sellers (paginated).                 | Public listing.                                             |
| **Read**   | Get the current user's seller profile.        | Requires authentication.                                    |
| **Read**   | Get a specific seller's profile.              | Public profile view.                                        |
| **Update** | Update the current user's seller profile.     | Requires authentication. Can only update their own profile. |
| **Update** | Update any seller's profile.                  |                                                             |
| **Delete** | Delete a seller profile.                      | Consider implications for associated books and user role.   |

---

## 2. Book Model (`Book`)

| Operation  | Action                                              | Notes                                                                                |
| :--------- | :-------------------------------------------------- | :----------------------------------------------------------------------------------- |
| **Create** | Add a new book listing.                             | `seller_id` linked to current user. Handle author/category linking.                  |
| **Read**   | List all books (paginated, filterable, searchable). | Public listing. Filters: category, author, publisher, seller, price, rating, seller. |
| **Read**   | Get details of a specific book.                     | Public detail view.                                                                  |
| **Read**   | List books listed by the current seller.            | Requires authentication.                                                             |
| **Update** | Update a book's details.                            | Sellers can only update their own books. Admins can update any.                      |
| **Delete** | Remove a book listing.                              | Sellers can only delete their own books. Admins can delete any.                      |

---

## 3. Author Model (`Author`)

| Operation  | Action                                    | Notes                                                   |
| :--------- | :---------------------------------------- | :------------------------------------------------------ |
| **Create** | Add a new author.                         | Sellers might add authors when listing new books.       |
| **Read**   | List all authors (paginated, searchable). | Public listing.                                         |
| **Read**   | Get details of a specific author.         | Public detail view.                                     |
| **Read**   | List books by a specific author.          |                                                         |
| **Update** | Update an author's details.               |                                                         |
| **Delete** | Delete an author.                         | Consider impact on books (disassociate/prevent delete). |

---

## 4. Category Model (`Category`)

| Operation  | Action                                    | Notes                                                   |
| :--------- | :---------------------------------------- | :------------------------------------------------------ |
| **Create** | Add a new category.                       |                                                         |
| **Read**   | List all categories.                      | Public listing.                                         |
| **Read**   | Get details of a specific category.       | Public detail view.                                     |
| **Read**   | List books within a specific category.    |                                                         |
| **Update** | Update a category's details (e.g., name). |                                                         |
| **Delete** | Delete a category.                        | Consider impact on books (disassociate/prevent delete). |

---

## 5. Publisher Model (`Publisher`)

| Operation  | Action                                       | Notes                                                |
| :--------- | :------------------------------------------- | :--------------------------------------------------- |
| **Create** | Add a new publisher.                         | Sellers might add publishers when listing new books. |
| **Read**   | List all publishers (paginated, searchable). | Public listing.                                      |
| **Read**   | Get details of a specific publisher.         | Public detail view.                                  |
| **Read**   | List books by a specific publisher.          |                                                      |
| **Update** | Update a publisher's details.                |                                                      |
| **Delete** | Delete a publisher.                          | Consider impact on books (set null/prevent delete).  |

---

## 6. Rating Model (`Rating`)

| Operation  | Action                                      | Notes                                                                   |
| :--------- | :------------------------------------------ | :---------------------------------------------------------------------- |
| **Create** | Add a rating/review for a specific book.    | Requires authentication. `user_id` is current user. Prevent duplicates. |
| **Read**   | List all ratings for a specific book.       | Public listing.                                                         |
| **Read**   | List ratings submitted by the current user. | Requires authentication.                                                |
| **Read**   | List ratings submitted by a specific user.  |                                                                         |
| **Read**   | Get a specific rating.                      | User/Seller can view their own.                                         |
| **Update** | Update a rating/review.                     | User/Seller can only update their own. Admins can update any.           |
| **Delete** | Delete a rating/review.                     | User/Seller can only delete their own. Admins can delete any.           |

---

**General Notes:**

- **Authentication:** Most endpoints require authentication (e.g., JWT). Public read endpoints are exceptions.
- **Authorization:** Middleware should enforce role checks for each endpoint.
- **Relationships:** Creating/updating resources like `Book` will need logic to handle linking/unlinking related entities (Authors, Categories).
- **Data Validation:** Input data for `POST` and `PATCH` requests must be validated.
- **Error Handling:** Implement standard HTTP status codes for errors (400, 401, 403, 404, 500) using the utility functions in `src\app\utils\response.py`.
- **Average Rating:** The `Book.rating` field should ideally be updated automatically via triggers or application logic whenever a `Rating` is added, updated, or deleted.
