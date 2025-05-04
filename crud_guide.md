# CRUD Plan for Bookstore Models

This document outlines the CRUD operations, corresponding API endpoints, and role-based access control for the provided SQLAlchemy models.

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

**General Notes:**

- **Authentication:** Most endpoints require authentication (e.g., JWT). Public read endpoints are exceptions.
- **Authorization:** Middleware should enforce role checks for each endpoint.
- **Relationships:** Creating/updating resources like `Book` will need logic to handle linking/unlinking related entities (Authors, Categories).
- **Data Validation:** Input data for `POST` and `PATCH` requests must be validated.
- **Error Handling:** Implement standard HTTP status codes for errors (400, 401, 403, 404, 500).
