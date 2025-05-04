# CRUD Plan for Bookstore Models

This document outlines the CRUD operations, corresponding API endpoints, and role-based access control for the provided SQLAlchemy models.

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
