# Database Seeder Plan

**Objective:** Populate the database with initial data for development and testing purposes.

**Seeding Order & Rationale:**

The data will be seeded in the following order to respect foreign key constraints and logical dependencies:

1.  **Geographical Data:**
    - `Country`
    - `State` (depends on `Country`)
    - `City` (depends on `State`)
2.  **User Data:**
    - `User` (core entity, some users will be sellers)
3.  **Location Data:**
    - `Location` (depends on `City`)
4.  **Assign Location to User:**
    - Update `User` records with `location_id`.
5.  **Book Metadata:**
    - `Category`
    - `Author`
    - `Publisher`
6.  **Book Data:**
    - `Book` (depends on `Author`, `Publisher`, `User` (as seller), and `Category` through the `book_category_table`)
7.  **Rating Data:**
    - `Rating` (depends on `User` and `Book`)

**Detailed Plan:**

**Phase 1: Setup and Helper Functions**

- **File:** We can use the existing `src/app/seed.py` file or create a new one if preferred.
- **Imports:** Import all necessary models, `db` from `app.extensions`, and any other utilities.
- **Main Seeder Function:** Create a main function (e.g., `seed_all()`) that will orchestrate the seeding process by calling individual seeding functions in the correct order.
- **Error Handling & Idempotency:**
  - Consider adding checks to prevent duplicate data if the seeder is run multiple times.
  - Alternatively, include logic to clear existing data from tables before seeding (use with caution).

**Phase 2: Seeding Functions**

For each step in the "Seeding Order":

1.  **`seed_geographical_data()`**

    - **Countries:** Define a list of sample countries. Create `Country` objects and add them to `db.session`.
    - **States:** Define sample states, linking them to the created countries. Create `State` objects.
    - **Cities:** Define sample cities, linking them to created states. Create `City` objects.
    - Commit to save geographical data.

2.  **`seed_users()`**

    - Define a list of sample users with `full_name`, `email`, `password`, and `role`.
    - Create `User` objects and add them to `db.session`.
    - Commit to save users.

3.  **`seed_locations()`**

    - Define sample locations, fetching `city_id` from created cities.
    - Create `Location` objects and add them to `db.session`.
    - Commit to save locations.

4.  **`assign_locations_to_users()`**

    - Fetch created users and locations.
    - Assign a `location_id` to each user.
    - Update `User` objects in `db.session`.
    - Commit changes.

5.  **`seed_book_metadata()`**

    - **Categories:** Define category names. Create `Category` objects.
    - **Authors:** Define author names and bios. Create `Author` objects.
    - **Publishers:** Define publisher names. Create `Publisher` objects.
    - Add all to `db.session` and commit.

6.  **`seed_books()`**

    - Define sample books with `title`, `author_id`, `publisher_id`, `user_id` (seller), `description`, `quantity`, `price`, etc., and a list of category names.
    - For each book, create a `Book` object and associate categories.
    - Add `Book` objects to `db.session`.
    - Commit.

7.  **`seed_ratings()`**
    - Define sample ratings with `user_id`, `book_id`, `score`, and `text`.
    - Create `Rating` objects and add them to `db.session`.
    - Commit.

**Phase 3: Execution**

- The main `seed_all()` function will call individual seeding functions in order.
- Include `db.session.commit()` strategically.
- Add print statements for progress.

**Mermaid Diagram of Seeding Process Flow:**

```mermaid
graph TD
    A[Start Seeding Process] --> B{seed_geographical_data (Countries, States, Cities)};
    B -- Commit --> C{seed_users};
    C -- Commit --> D{seed_locations};
    D -- Commit --> E{assign_locations_to_users};
    E -- Commit --> F{seed_book_metadata (Categories, Authors, Publishers)};
    F -- Commit --> G{seed_books};
    G -- Commit --> H{seed_ratings};
    H -- Final Commit --> I[Seeding Complete];
```
