# 1. Languages (Admin Only)

- **Create:** Add a new language.
- **Read:** List available languages.
- **Update:** Modify language details.
- **Delete:** Remove a language (if unused).

# 2. Authors (Admin/Moderator)

- **Create:** Add a new author.
- **Read:** List authors, view author details & books.
- **Update:** Correct/update author information.
- **Delete:** Remove an author (handle associated books).

# 3. Publishers (Admin/Moderator)

- **Create:** Add a new publisher.
- **Read:** List publishers, view details.
- **Update:** Correct/update publisher information.
- **Delete:** Remove a publisher (handle associated books).

# 4. Categories (Admin/Moderator)

- **Create:** Add a new category (define parent if needed).
- **Read:** List categories, view books within a category.
- **Update:** Rename, describe, or re-parent a category.
- **Delete:** Remove a category (handle subcategories/books).

# 5. Users (Customer, Seller, Admin)

- **Create:** User registration (role assigned).
- **Read:** View own profile (Customer/Seller), View any user profile (Admin).
- **Update:** Update own profile (email, password) (Customer/Seller), Update any user profile/role (Admin).
- **Delete:** Request account deletion/deactivation (Customer/Seller), Delete/deactivate any user (Admin).

# 6. Sellers (Seller, Admin)

- **Create:** User with 'seller' role creates their seller profile (store name, etc.).
- **Read:** View own seller profile/dashboard (Seller), View public seller profile (Customer/Admin), List all sellers (Admin).
- **Update:** Update own store details (Seller), Update any seller profile/status (Admin).
- **Delete:** Deactivate seller profile (Seller/Admin), Delete seller profile (Admin).

# 7. Addresses (Customer/Seller)

- **Create:** Add a new shipping/billing address.
- **Read:** List own addresses.
- **Update:** Edit an existing address, set default.
- **Delete:** Remove an address (if not tied to active orders).

# 8. Books (Metadata) (Admin/Moderator, potentially Seller)

- **Create:** Add new book metadata (ISBN, title, author link, category link etc.). (Admin, maybe trusted Sellers).
- **Read:** Search/list books, view book details (description, authors, categories, avg rating, associated inventory listings). (All Roles).
- **Update:** Correct/update book metadata (Admin/Moderator).
- **Delete:** Remove a book record (Admin - handle listings/reviews).

# 9. Inventory (Listings) (Seller, Admin)

- **Create:** Add a new listing (price, quantity, condition) for an existing book (Seller).
- **Read:** View own listings (Seller), View all listings for a book (All Roles), List all inventory (Admin).
- **Update:** Modify own listing details (price, quantity, condition, active status) (Seller).
- **Delete:** Remove/deactivate own listing (Seller).

# 10. BookAuthors / BookCategories (Join Tables)

- Managed implicitly via Book, Author, Category CRUD.

# 11. Reviews (Customer, Admin)

- **Create:** Submit a review for a purchased book (Customer).
- **Read:** View reviews for a book (All Roles), View own reviews (Customer), List reviews for moderation (Admin).
- **Update:** Edit own review (Customer - limited?), Approve/reject review (Admin).
- **Delete:** Delete own review (Customer - limited?), Delete any review (Admin).

# 12. Orders (Customer, Seller, Admin, System)

- **Create:** Order created on checkout (System/Customer Action).
- **Read:** View own order history (Customer), View orders with own items (Seller), View any order (Admin).
- **Update:** Update order status, add tracking (Seller/Admin).
- **Delete:** Cancel order (Customer - if allowed, Admin), Delete order record (Admin - rare).

# 13. OrderItems (System, Admin)

- **Create:** Items added when Order is created.
- **Read:** Viewed as part of viewing an Order.
- **Update:** (Rare).
- **Delete:** Items removed if parent Order is deleted/cancelled.
