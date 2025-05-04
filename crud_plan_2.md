# Programmer's Guide: Building Features with Separation of Concerns

This guide outlines a structured approach to developing features in the Flask application, emphasizing the separation of concerns. This pattern enhances maintainability, testability, and collaboration. We will use the existing authentication feature (`auth_route.py`, `auth_service.py`, etc.) as a primary example.

## Core Principle: Layered Architecture

We organize the codebase into distinct layers, each with a specific responsibility. Data and control flow primarily move vertically between these layers.

```mermaid
graph LR
    A[Client Request] --> B(Routes Layer);
    B -- Calls --> C(Service Layer);
    C -- Uses --> D(Model Layer);
    C -- Uses --> E(Utility Layer);
    D -- Interacts with --> F[(Database)];
    C -- Returns result --> B;
    B -- Uses --> E;  // e.g., for response formatting
    B -- Sends Response --> A;

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#cfc,stroke:#333,stroke-width:2px
    style E fill:#ffc,stroke:#333,stroke-width:2px

    subgraph Layers
        B(Routes / routes/)
        C(Services / services/)
        D(Models / model/)
        E(Utilities / utils/)
    end
```

## Layer Responsibilities

### 1. Routes Layer (`src/app/routes/`)

- **Purpose:** Handles incoming HTTP requests and outgoing responses. Acts as the entry point for API interactions.
- **Responsibilities:**
  - Define API endpoints using Flask Blueprints (`@bp.route('/path', methods=['GET', 'POST'])`).
  - Extract and parse data from requests (e.g., `request.get_json()`, `request.form`, `request.args`).
  - Perform _initial, basic_ input validation if necessary (though complex validation often belongs in the Service layer or Utilities).
  - Call the appropriate method in the corresponding Service Layer, passing the necessary data.
  - Receive results (data or status indicators) back from the Service Layer.
  - Format the final HTTP response (status code, headers, JSON body) using utility functions (like `src/app/utils/response.py`).
  - Handle exceptions specific to request handling and translate them into appropriate error responses.
- **Example:** `src/app/routes/auth_route.py` defines `/register`, `/login`, `/logout`. It parses request JSON, calls `auth_service.register_user()`, `auth_service.login_user()`, etc., and uses `success_response` / `error_response` to build the `jsonify` response.
- **Key Rule:** Keep business logic minimal. Focus on HTTP communication.

### 2. Service Layer (`src/app/services/`)

- **Purpose:** Encapsulates the core business logic and orchestrates operations for a specific domain or feature.
- **Responsibilities:**
  - Implement the main workflows and rules of the application feature.
  - Perform detailed input validation (often using utility validators).
  - Interact with the Model Layer to fetch, create, update, or delete data.
  - Coordinate actions involving multiple models or steps.
  - Call Utility functions for tasks like password hashing, sending emails, interacting with external APIs, applying bonuses, etc.
  - Handle business-specific errors and exceptions.
  - Return processed data or status information to the Route Layer.
- **Example:** `src/app/services/auth_service.py` contains `register_user`, `login_user`, `logout_user`. It validates input (`validate_register_input`), interacts with `User` and `BlacklistToken` models, hashes passwords (`hash_password`), verifies passwords (`verify_password`), generates tokens (`create_access_token`), handles referral logic (`ReferralBonusService`), and commits/rollbacks database sessions.
- **Key Rule:** Should be independent of HTTP concepts (request/response objects). It deals with data and logic.

### 3. Model Layer (`src/app/model/`)

- **Purpose:** Defines the application's data structures and interacts with the database.
- **Responsibilities:**
  - Define database table schemas using an ORM (like SQLAlchemy in `extensions.py` and used by model classes).
  - Represent data entities as Python classes (e.g., `User`, `Book`, `Category`).
  - May include methods directly related to the data itself (e.g., `User.verify_password(password)`).
  - Define relationships between models (e.g., one-to-many, many-to-many).
- **Example:** `src/app/model/user.py`, `src/app/model/blacklist_token.py`. These define the structure of the `users` and `blacklist_tokens` tables and their columns.
- **Key Rule:** Focus solely on data structure, persistence, and basic data-related operations. Avoid embedding complex business logic here.

### 4. Utility Layer (`src/app/utils/`)

- **Purpose:** Provides reusable, cross-cutting helper functions and classes.
- **Responsibilities:**
  - Offer common functionalities needed by multiple layers.
  - Examples:
    - Response Formatting (`response.py`): Standardizing API response structures.
    - Input Validation (`validators.py`): Defining reusable validation rules.
    - Security (`security.py`): Password hashing/verification, token generation helpers.
    - Decorators (`decorators.py`): Implementing reusable logic like authentication checks (`@jwt_required()`).
    - Specific Business Calculations/Helpers (`bonus.py`): Encapsulating specific, reusable logic like referral bonuses.
    - Constants/Enums (`roles.py`): Defining shared constants.
- **Example:** `src/app/utils/response.py`, `src/app/utils/validators.py`, `src/app/utils/security.py`, `src/app/utils/bonus.py`.
- **Key Rule:** Functions should be generic, self-contained, and easily testable in isolation.

## How to Implement a New Feature (Example: CRUD for "Books")

1.  **Model:** Define `src/app/model/book.py` with necessary fields (title, author_id, publisher_id, etc.) and relationships.
2.  **Utilities (if needed):** Create validation rules in `src/app/utils/validators.py` (e.g., `validate_book_input`).
3.  **Service:** Create `src/app/services/book_service.py` with methods like:
    - `create_book(data)`: Validates input, creates a `Book` instance, adds to DB session, commits.
    - `get_book_by_id(book_id)`: Queries the DB for the book.
    - `get_all_books(filters=None)`: Queries for multiple books, potentially applying filters.
    - `update_book(book_id, data)`: Finds the book, validates input, updates fields, commits.
    - `delete_book(book_id)`: Finds the book, deletes it, commits.
4.  **Routes:** Create `src/app/routes/book_route.py`:
    - Define endpoints: `POST /books`, `GET /books/<int:book_id>`, `GET /books`, `PUT /books/<int:book_id>`, `DELETE /books/<int:book_id>`.
    - In each route function:
      - Parse request data.
      - Call the corresponding `book_service` method.
      - Use `success_response` or `error_response` from `src/app/utils/response.py` to return the result.

By following this layered approach, the code becomes more organized, easier to understand, test, and modify. Each part has a clear job, reducing complexity and preventing unrelated concerns from mixing.

---
