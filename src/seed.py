import random
from decimal import Decimal
from faker import Faker
from src.app.extensions import db
# Assuming your models are structured like this
from src.app.model.user import User
from src.app.model.language import Language
from src.app.model.publisher import Publisher
# Import actual Author model and association table
from src.app.model.author import Author, book_authors
from src.app.model.category import Category # book_categories is likely defined here or in book.py
from src.app.model.book import Book
from src.app.model.seller import Seller
from src.app.model.inventory import Inventory
# Import actual Address model
from src.app.model.address import Address
from src.app.model.order import Order
from src.app.model.order_item import OrderItem
from src.app.model.review import Review


# --- Ensure User Model has necessary relationships ---
# Add relationships dynamically if they don't exist.
# This is useful if the User model definition is separate
# and might not always include all back-references.
if not hasattr(User, 'addresses'):
    User.addresses = db.relationship("Address", back_populates="user", cascade="all, delete-orphan")
if not hasattr(User, 'seller_profile'):
     User.seller_profile = db.relationship("Seller", uselist=False, back_populates="user", cascade="all, delete-orphan")
if not hasattr(User, 'orders'):
    User.orders = db.relationship("Order", back_populates="user")
if not hasattr(User, 'reviews'):
    User.reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan")


from src.app import create_app

# Initialize Flask app and Faker
app = create_app()
fake = Faker()

# --- Seeding Functions ---

def seed_users(n=10):
    """Seeds the database with dummy users."""
    with app.app_context():
        users = []
        for _ in range(n):
            user = User(
                username=fake.unique.user_name(),
                email=fake.unique.email(),
                password_hash=fake.password(length=12), # In production, hash passwords properly!
                balance=fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=10, max_value=5000),
                referral_code=fake.unique.bothify(text='??????'),
                referred_by=None, # Can be enhanced to link referrals
                role=random.choice(['user', 'admin', 'seller']), # Added seller role
            )
            users.append(user)
        db.session.add_all(users)
        db.session.commit()
        print(f"-> Seeded {len(users)} users.")

def clear_users():
    """Deletes all users from the database."""
    with app.app_context():
        # Need to clear dependent tables first if cascade delete isn't working as expected
        # For example, clear addresses, sellers, orders, reviews associated with users
        print("<- Clearing dependent data (addresses, sellers, orders, reviews)...")
        db.session.query(Address).delete() # Clear addresses linked to users
        db.session.query(Seller).delete() # Clear sellers linked to users
        db.session.query(Order).delete() # Clear orders linked to users (assuming cascade handles items)
        db.session.query(Review).delete() # Clear reviews linked to users
        db.session.commit() # Commit deletions of dependents

        print("<- Clearing users...")
        num_deleted = db.session.query(User).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} users.")

def seed_languages(n=5):
    """Seeds the database with dummy languages."""
    with app.app_context():
        languages = []
        # Add some common languages first
        common_languages = [('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('de', 'German'), ('id', 'Indonesian')]
        for code, name in common_languages:
             # Check if language already exists
            existing = db.session.query(Language).filter_by(language_code=code).first()
            if not existing:
                lang = Language(language_code=code, language_name=name)
                languages.append(lang)

        # Add more random ones if needed (less realistic)
        for _ in range(max(0, n - len(common_languages))): # Ensure non-negative range
            try:
                lang_code = fake.unique.language_code()
                # Ensure the generated code isn't already used by querying
                while db.session.query(Language).filter_by(language_code=lang_code).count() > 0:
                     lang_code = fake.unique.language_code() # Regenerate if exists

                lang = Language(
                    language_code=lang_code,
                    language_name=fake.unique.country().capitalize() # Use country name as a proxy for language name
                )
                languages.append(lang)
            except Exception as e: # Catch potential unique constraint errors during generation
                print(f"Warning: Could not generate unique language code/name: {e}")
                fake.unique.clear() # Clear unique cache if errors occur
                continue # Skip this iteration

        if languages:
            db.session.add_all(languages)
            try:
                db.session.commit()
                print(f"-> Seeded {len(languages)} languages.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding languages: {e}")
        else:
            print("-> Languages already seeded or none to add.")


def clear_languages():
    """Deletes all languages from the database."""
    with app.app_context():
        print("<- Clearing languages...")
        num_deleted = db.session.query(Language).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} languages.")

def seed_publishers(n=20):
    """Seeds the database with dummy publishers."""
    with app.app_context():
        publishers = []
        for _ in range(n):
            try:
                publisher = Publisher(
                    name=fake.unique.company(),
                    contact_email=fake.company_email(),
                    website=fake.url(),
                )
                publishers.append(publisher)
            except Exception as e:
                print(f"Warning: Could not generate unique publisher name: {e}")
                fake.unique.clear()
                continue

        if publishers:
            db.session.add_all(publishers)
            try:
                db.session.commit()
                print(f"-> Seeded {len(publishers)} publishers.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding publishers: {e}")
        else:
            print("-> No new publishers generated.")


def clear_publishers():
    """Deletes all publishers from the database."""
    with app.app_context():
        print("<- Clearing publishers...")
        # Consider dependencies: Books might reference publishers (SET NULL assumed)
        num_deleted = db.session.query(Publisher).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} publishers.")

# Use actual Author model now
def seed_authors(n=50):
    """Seeds the database with dummy authors using the actual Author model."""
    with app.app_context():
        authors = []
        for _ in range(n):
            try:
                first_name = fake.first_name()
                last_name = fake.last_name()
                # Check for existing author with the same name (optional, depends on desired uniqueness)
                # existing = db.session.query(Author).filter_by(first_name=first_name, last_name=last_name).first()
                # if existing:
                #     continue

                author = Author(
                    first_name=first_name,
                    last_name=last_name,
                    bio=fake.paragraph(nb_sentences=random.randint(2, 5)) # Generate a short bio
                )
                authors.append(author)
            except Exception as e: # Catch potential unique constraint errors if names need to be unique
                print(f"Warning: Could not generate unique author name (if required): {e}")
                continue # Skip this iteration

        if authors:
            db.session.add_all(authors)
            try:
                db.session.commit()
                print(f"-> Seeded {len(authors)} authors.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding authors: {e}")
        else:
             print("-> No new authors generated.")


# Use actual Author model now
def clear_authors():
    """Deletes all authors from the database."""
    with app.app_context():
        print("<- Clearing authors...")
        # Clear association table first (book_authors)
        db.session.execute(book_authors.delete())
        num_deleted = db.session.query(Author).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} authors and associations.")


def seed_categories(n=15, max_depth=3):
    """Seeds the database with dummy categories, including parent-child relationships."""
    with app.app_context():
        categories = []
        parent_candidates = [] # Store category objects that can be parents

        for i in range(n):
            parent_id = None
            potential_parent = None

            # Decide if this category should have a parent
            if parent_candidates and random.random() < 0.6: # 60% chance to have a parent if possible
                potential_parent = random.choice(parent_candidates)
                # Basic check to limit depth (can be improved)
                # This simple check assumes parent_id is None for top-level
                if potential_parent.parent_category_id is None or random.random() < 0.8: # Favor shallower nesting
                     parent_id = potential_parent.id # Assign parent ID

            try:
                category = Category(
                    name=fake.unique.bs().capitalize(), # Business Strategy terms as category names
                    description=fake.catch_phrase(),
                    parent_category_id=parent_id # Set the parent ID
                )
                categories.append(category)

            except Exception as e:
                 print(f"Warning: Could not generate unique category name: {e}")
                 fake.unique.clear()
                 continue


        if not categories:
            print("-> No categories generated.")
            return

        # Add all categories first
        db.session.add_all(categories)

        try:
            # Flush to assign IDs before potentially using them as parents in the same batch
            # Although in this simple loop, parents are chosen from *previous* iterations
            db.session.flush()

            # Update parent_candidates with the newly added categories
            # Only add those that *could* be parents (e.g., not too deep already, if depth check was more robust)
            # Simple version: all newly added categories can be parents for subsequent ones
            parent_candidates.extend(categories)

            # Commit all categories at the end
            db.session.commit()
            print(f"-> Seeded {len(categories)} categories.")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding categories: {e}")


def clear_categories():
    """Deletes all categories from the database."""
    with app.app_context():
        print("<- Clearing categories...")
        # Clear association table first (book_categories)
        # Assuming book_categories is imported or accessible
        try:
            from .category import book_categories # Adjust import if needed
            db.session.execute(book_categories.delete())
        except ImportError:
            print("Warning: book_categories table not found for clearing.")
        except Exception as e:
             print(f"Error clearing book_categories: {e}")

        # Clear categories themselves (consider parent/child relationships and SET NULL)
        num_deleted = db.session.query(Category).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} categories and associations.")


def seed_books(n=100):
    """Seeds the database with dummy books."""
    with app.app_context():
        # Fetch existing related data IDs
        publisher_ids = [p.id for p in db.session.query(Publisher.id).all()]
        language_codes = [l.language_code for l in db.session.query(Language.language_code).all()]
        author_ids = [a.id for a in db.session.query(Author.id).all()] # Use actual Author model
        category_ids = [c.id for c in db.session.query(Category.id).all()]

        if not all([publisher_ids, language_codes, author_ids, category_ids]):
            print("! Cannot seed books: Missing prerequisite data (Publishers, Languages, Authors, or Categories).")
            return

        books = []
        for _ in range(n):
            try:
                book = Book(
                    isbn=fake.unique.isbn13(),
                    title=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=500),
                    publisher_id=random.choice(publisher_ids) if publisher_ids else None,
                    publication_date=fake.date_between(start_date='-30y', end_date='today'),
                    num_pages=random.randint(50, 1200),
                    language_code=random.choice(language_codes) if language_codes else None,
                    cover_image_url=fake.image_url(width=400, height=600),
                    average_rating=Decimal(random.uniform(0, 5)).quantize(Decimal("0.01")),
                )

                # Add relationships (Many-to-Many)
                # Authors
                num_authors = random.randint(1, 3)
                if author_ids: # Check if authors exist
                    selected_author_ids = random.sample(author_ids, min(num_authors, len(author_ids)))
                    for author_id in selected_author_ids:
                         author = db.session.get(Author, author_id) # Use db.session.get for efficiency
                         if author:
                             book.authors.append(author) # Append the actual Author object

                # Categories
                num_categories = random.randint(1, 4)
                if category_ids: # Check if categories exist
                    selected_category_ids = random.sample(category_ids, min(num_categories, len(category_ids)))
                    for category_id in selected_category_ids:
                         category = db.session.get(Category, category_id) # Use db.session.get
                         if category:
                            book.categories.append(category) # Append the actual Category object

                books.append(book)

            except Exception as e:
                 print(f"Warning: Could not generate unique ISBN or error creating book: {e}")
                 fake.unique.clear() # Clear unique cache for ISBN
                 continue

        if books:
            db.session.add_all(books)
            try:
                db.session.commit()
                print(f"-> Seeded {len(books)} books with relationships.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding books: {e}")
        else:
            print("-> No new books generated.")


def clear_books():
    """Deletes all books from the database."""
    with app.app_context():
        print("<- Clearing books...")
        # Cascade delete should handle associations (book_authors, book_categories)
        # and relationships like inventory, reviews, order_items if configured correctly.
        # If cascade is not set, clear dependents manually first.
        # Example: clear inventory, reviews, order_items before books
        # clear_inventory()
        # clear_reviews()
        # clear_order_items()
        num_deleted = db.session.query(Book).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} books (ensure cascades handled dependents).")


def seed_sellers(n=15):
    """Seeds the database with dummy sellers, linked to existing users."""
    with app.app_context():
        # Fetch users who are not already sellers
        # Ensure User model has 'seller_profile' relationship defined correctly
        available_users = db.session.query(User).outerjoin(User.seller_profile).filter(Seller.id == None).limit(n).all()

        if not available_users:
            print("! Cannot seed sellers: No available users found (or limit reached). Ensure users are seeded first and relationship is set.")
            return

        sellers = []
        for user in available_users: # Iterate through the fetched User objects
            try:
                seller = Seller(
                    user_id=user.id, # Link to the user ID
                    store_name=fake.unique.company() + " Books", # Make store name unique
                    description=fake.catch_phrase(),
                    is_active=fake.boolean(chance_of_getting_true=90),
                )
                sellers.append(seller)
            except Exception as e:
                 print(f"Warning: Could not generate unique store name: {e}")
                 fake.unique.clear()
                 continue

        if sellers:
            db.session.add_all(sellers)
            try:
                db.session.commit()
                print(f"-> Seeded {len(sellers)} sellers.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding sellers: {e}")
        else:
             print("-> No new sellers generated.")


def clear_sellers():
    """Deletes all sellers from the database."""
    with app.app_context():
        print("<- Clearing sellers...")
        # Consider dependencies: Inventory might reference sellers (CASCADE assumed)
        # OrderItems might reference sellers (RESTRICT assumed - clear OrderItems first)
        # clear_order_items() # Uncomment if OrderItems RESTRICT seller deletion
        num_deleted = db.session.query(Seller).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} sellers.")


def seed_inventory(n=200):
    """Seeds the database with dummy inventory items."""
    with app.app_context():
        book_ids = [b.id for b in db.session.query(Book.id).all()]
        seller_ids = [s.id for s in db.session.query(Seller.id).all()]

        if not book_ids or not seller_ids:
            print("! Cannot seed inventory: Missing prerequisite data (Books or Sellers).")
            return

        inventory_items = []
        conditions = ["New", "Used - Like New", "Used - Very Good", "Used - Good", "Used - Acceptable"]
        # Keep track of existing book/seller/condition pairs to avoid duplicates (UniqueConstraint)
        existing_combinations = set((inv.book_id, inv.seller_id, inv.condition)
                                    for inv in db.session.query(Inventory.book_id, Inventory.seller_id, Inventory.condition).all())

        attempts = 0
        max_attempts = n * 5 # Try harder to find unique combinations

        while len(inventory_items) < n and attempts < max_attempts:
            attempts += 1
            book_id = random.choice(book_ids)
            seller_id = random.choice(seller_ids)
            condition = random.choice(conditions)

            # Check if this combination already exists in DB or current batch
            if (book_id, seller_id, condition) in existing_combinations:
                continue # Skip if duplicate

            try:
                inventory = Inventory(
                    book_id=book_id,
                    seller_id=seller_id,
                    price=fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=1, max_value=200),
                    quantity=random.randint(0, 50), # Allow 0 quantity initially
                    condition=condition,
                    condition_description=fake.sentence(nb_words=random.randint(5, 15)) if condition != "New" else None,
                    is_active=fake.boolean(chance_of_getting_true=85),
                )
                inventory_items.append(inventory)
                # Add to our temporary set to prevent adding duplicates within this batch
                existing_combinations.add((book_id, seller_id, condition))
            except Exception as e:
                 print(f"Error creating inventory item instance: {e}")
                 continue


        if inventory_items:
            db.session.add_all(inventory_items)
            try:
                db.session.commit()
                print(f"-> Seeded {len(inventory_items)} inventory items.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding inventory items (likely unique constraint): {e}")
        else:
             print("-> No new unique inventory items could be generated.")


def clear_inventory():
    """Deletes all inventory items from the database."""
    with app.app_context():
        print("<- Clearing inventory...")
        # Consider dependencies: OrderItems might reference inventory (RESTRICT assumed - clear OrderItems first)
        # clear_order_items() # Uncomment if OrderItems RESTRICT inventory deletion
        num_deleted = db.session.query(Inventory).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} inventory items.")

# Use actual Address model now
def seed_addresses(n=30):
    """Seeds the database with dummy addresses using the actual Address model."""
    with app.app_context():
        user_ids = [u.id for u in db.session.query(User.id).all()]
        if not user_ids:
            print("! Cannot seed addresses: No users found.")
            return

        addresses = []
        address_types = ['shipping', 'billing'] # From Address model constraint

        for _ in range(n):
            user_id = random.choice(user_ids)
            addr_type = random.choice(address_types)

            # Check if user already has a default address of this type (optional)
            # has_default = db.session.query(Address.id).filter_by(user_id=user_id, address_type=addr_type, is_default=True).count() > 0
            # make_default = not has_default # Make first one default

            address = Address(
                user_id=user_id,
                address_type=addr_type,
                street_address=fake.street_address(),
                city=fake.city(),
                state_province=fake.state_abbr(), # Use state abbreviation
                postal_code=fake.zipcode(),
                country=fake.country(),
                is_default=fake.boolean(chance_of_getting_true=15) # Small chance of being default
            )
            addresses.append(address)

        # Ensure at least one default shipping and billing per user (more complex logic)
        # Could query after adding and update if needed, or handle during creation loop.

        if addresses:
            db.session.add_all(addresses)
            try:
                db.session.commit()
                print(f"-> Seeded {len(addresses)} addresses.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding addresses: {e}")
        else:
             print("-> No addresses generated.")


# Use actual Address model now
def clear_addresses():
    """Deletes all addresses from the database."""
    with app.app_context():
        print("<- Clearing addresses...")
        # Consider dependencies: Orders might reference addresses (RESTRICT assumed - clear Orders first)
        # clear_orders() # Uncomment if Orders RESTRICT address deletion
        num_deleted = db.session.query(Address).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} addresses.")


def seed_orders(n=50):
    """Seeds the database with dummy orders."""
    with app.app_context():
        user_ids = [u.id for u in db.session.query(User.id).all()]
        # Fetch actual addresses, ensuring they exist
        all_address_ids = [a.id for a in db.session.query(Address.id).all()]

        if not user_ids:
            print("! Cannot seed orders: No users found.")
            return
        if not all_address_ids:
            print("! Cannot seed orders: No addresses found. Seed addresses first.")
            return

        orders = []
        statuses = ["pending", "processing", "shipped", "delivered", "cancelled", "returned"]
        shipping_methods = ["Standard", "Express", "Next Day"]

        for _ in range(n):
            user_id = random.choice(user_ids)
            # Get addresses specifically associated with the chosen user
            user_addresses = db.session.query(Address).filter(Address.user_id == user_id).all()

            shipping_addr = None
            billing_addr = None

            if user_addresses:
                # Try to find specific types or defaults
                shipping_addr = next((addr for addr in user_addresses if addr.address_type == 'shipping'), None)
                billing_addr = next((addr for addr in user_addresses if addr.address_type == 'billing'), None)
                # Fallback to any address if specific type not found
                if not shipping_addr:
                    shipping_addr = random.choice(user_addresses)
                if not billing_addr:
                    billing_addr = random.choice(user_addresses) # Can be same as shipping
            else:
                # If user has NO addresses, maybe skip order or assign random global address (less realistic)
                 print(f"Warning: User {user_id} has no addresses. Skipping order or assigning random global address.")
                 # Option 1: Skip
                 # continue
                 # Option 2: Assign random global address (use IDs)
                 shipping_addr_id = random.choice(all_address_ids)
                 billing_addr_id = random.choice(all_address_ids)


            # Use IDs from the selected Address objects
            shipping_id = shipping_addr.id if shipping_addr else (shipping_addr_id if 'shipping_addr_id' in locals() else None)
            billing_id = billing_addr.id if billing_addr else (billing_addr_id if 'billing_addr_id' in locals() else None)

            if not shipping_id or not billing_id:
                 print(f"Warning: Could not determine shipping/billing address for user {user_id}. Skipping order.")
                 continue # Skip if addresses couldn't be determined


            order = Order(
                user_id=user_id,
                order_date=fake.date_time_between(start_date='-2y', end_date='now', tzinfo=None), # Adjust timezone as needed
                status=random.choice(statuses),
                total_amount=Decimal("0.00"), # Placeholder, will be calculated by items
                shipping_address_id=shipping_id,
                billing_address_id=billing_id,
                shipping_method=random.choice(shipping_methods),
                tracking_number=fake.bothify(text='??########??') if random.random() > 0.3 else None, # 70% chance of tracking#
            )
            orders.append(order)

        if orders:
            db.session.add_all(orders)
            try:
                # Commit orders first to get IDs before creating items
                db.session.commit()
                print(f"-> Seeded {len(orders)} orders (Items need to be seeded separately).")
                # Return the created order objects if needed for item seeding
                return orders # Return the list of newly created order objects
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding orders: {e}")
                return [] # Return empty list on error
        else:
            print("-> No orders generated.")
            return [] # Return empty list if none generated


def clear_orders():
    """Deletes all orders from the database."""
    with app.app_context():
        print("<- Clearing orders...")
        # OrderItems should be deleted first due to cascade on OrderItem.order_id
        clear_order_items()
        num_deleted = db.session.query(Order).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} orders.")


def seed_order_items(n_items_per_order_range=(1, 5)):
    """Seeds order items for existing orders, updating order totals."""
    with app.app_context():
        orders = db.session.query(Order).all()
        # Fetch available inventory items with quantity > 0
        # Use with_for_update() if concurrency is a concern, but likely not needed for seeding
        available_inventory_query = db.session.query(Inventory).filter(Inventory.quantity > 0)
        available_inventory = available_inventory_query.all()


        if not orders:
            print("! Cannot seed order items: No orders found. Seed orders first.")
            return
        if not available_inventory:
            print("! Cannot seed order items: No available inventory found (with quantity > 0). Seed inventory first.")
            return

        order_items_added = []
        updated_orders_map = {} # Store order objects to update totals {order_id: order_object}
        inventory_map = {inv.id: inv for inv in available_inventory} # For quick lookup and quantity update

        print(f"-> Attempting to add items for {len(orders)} orders using {len(inventory_map)} available inventory types.")

        for order in orders:
            num_items_to_add = random.randint(*n_items_per_order_range)
            # Ensure we don't try to add more items than available inventory types
            num_items_to_add = min(num_items_to_add, len(inventory_map))

            if num_items_to_add == 0:
                continue # Skip if no inventory available

            # Select unique inventory items for this order from available ones
            available_inv_ids = list(inventory_map.keys())
            if not available_inv_ids: # Stop if no more inventory globally
                 print("! Ran out of available inventory globally.")
                 break
            selected_inventory_ids = random.sample(available_inv_ids, min(num_items_to_add, len(available_inv_ids)))

            current_order_total = Decimal(order.total_amount or "0.00") # Start with existing total if any

            items_added_this_order = 0
            for inv_id in selected_inventory_ids:
                inventory_item = inventory_map.get(inv_id)

                # Double check if item still exists in map and has quantity
                if not inventory_item or inventory_item.quantity <= 0:
                    # This might happen if another order depleted it in this run
                    if inv_id in inventory_map: del inventory_map[inv_id] # Remove if depleted
                    continue # Skip if inventory became unavailable

                # Determine quantity to order (e.g., 1 to 3, or available quantity if less)
                max_qty_possible = inventory_item.quantity
                quantity_to_order = random.randint(1, min(3, max_qty_possible))

                try:
                    order_item = OrderItem(
                        order_id=order.id,
                        inventory_id=inventory_item.id,
                        book_id=inventory_item.book_id, # Get from inventory item
                        seller_id=inventory_item.seller_id, # Get from inventory item
                        quantity=quantity_to_order,
                        price_per_item=inventory_item.price, # Price at the time of order
                        condition_at_purchase=inventory_item.condition, # Condition at the time of order
                    )
                    order_items_added.append(order_item)
                    items_added_this_order += 1

                    # Update order total
                    current_order_total += (inventory_item.price * quantity_to_order)

                    # !!! IMPORTANT: Decrement inventory quantity in the map !!!
                    inventory_item.quantity -= quantity_to_order

                    # Remove from map if quantity reaches 0 to prevent re-selection
                    if inventory_item.quantity <= 0:
                        print(f"--- Inventory item {inventory_item.id} depleted.")
                        del inventory_map[inv_id] # Remove from available pool

                    # Mark the order for total amount update
                    if order.id not in updated_orders_map:
                        updated_orders_map[order.id] = order # Store the actual order object


                except Exception as e:
                    print(f"Error creating order item instance for order {order.id}, inv {inv_id}: {e}")
                    continue # Skip this item

            # Update the order's total amount after trying all items for this order
            if order.id in updated_orders_map:
                 updated_orders_map[order.id].total_amount = current_order_total
                 # No need to db.session.add(order) yet, will be handled by commit later


        if order_items_added:
            db.session.add_all(order_items_added)
            # Also add the updated inventory items (those with decremented quantity)
            # This relies on the inventory_map containing the modified objects
            inventory_to_update = [inv for inv in available_inventory if inv.id not in inventory_map or inventory_map[inv.id].quantity != inv.quantity]
            # A cleaner way might be to track modified inventory IDs
            db.session.add_all(updated_orders_map.values()) # Add updated orders

            try:
                db.session.commit()
                print(f"-> Seeded {len(order_items_added)} order items for {len(updated_orders_map)} orders and updated totals/inventory.")
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding order items or updating related data: {e}")
        else:
            print("-> No order items were added (check available inventory and orders).")


def clear_order_items():
    """Deletes all order items from the database."""
    with app.app_context():
        print("<- Clearing order items...")
        num_deleted = db.session.query(OrderItem).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} order items.")
        # Optionally, reset order totals if clearing items but not orders
        # print("<- Resetting order totals...")
        # db.session.query(Order).update({Order.total_amount: Decimal("0.00")})
        # db.session.commit()


def seed_reviews(n=150):
    """Seeds the database with dummy reviews."""
    with app.app_context():
        user_ids = [u.id for u in db.session.query(User.id).all()]
        book_ids = [b.id for b in db.session.query(Book.id).all()]

        if not user_ids or not book_ids:
            print("! Cannot seed reviews: Missing prerequisite data (Users or Books).")
            return

        reviews = []
        # Keep track of existing user/book pairs to avoid duplicate reviews (UniqueConstraint)
        existing_reviews = set((r.user_id, r.book_id)
                              for r in db.session.query(Review.user_id, Review.book_id).all())

        attempts = 0
        max_attempts = n * 5 # Allow more attempts to find unique pairs

        while len(reviews) < n and attempts < max_attempts:
            attempts += 1
            user_id = random.choice(user_ids)
            book_id = random.choice(book_ids)

            # Check if this user already reviewed this book in DB or current batch
            if (user_id, book_id) in existing_reviews:
                continue # Skip if duplicate

            try:
                review = Review(
                    book_id=book_id,
                    user_id=user_id,
                    rating=random.randint(1, 5),
                    review_text=fake.paragraph(nb_sentences=random.randint(1, 5)) if random.random() > 0.1 else None, # 90% chance of text
                    review_date=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=None),
                    is_approved=fake.boolean(chance_of_getting_true=75), # 75% chance of being approved
                )
                reviews.append(review)
                # Add to our temporary set to prevent adding duplicates within this batch
                existing_reviews.add((user_id, book_id))
            except Exception as e:
                 print(f"Error creating review instance: {e}")
                 continue


        if reviews:
            db.session.add_all(reviews)
            try:
                db.session.commit()
                print(f"-> Seeded {len(reviews)} reviews.")
                # Optional: Recalculate average ratings for books after adding reviews
                # update_book_average_ratings() # Call the helper function
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding reviews (likely unique constraint): {e}")
        else:
             print("-> No new unique reviews could be generated.")


def clear_reviews():
    """Deletes all reviews from the database."""
    with app.app_context():
        print("<- Clearing reviews...")
        num_deleted = db.session.query(Review).delete()
        db.session.commit()
        print(f"<- Cleared {num_deleted} reviews.")
        # Optional: Reset average ratings for books after clearing reviews
        # reset_book_average_ratings() # Call the helper function


# --- Helper function to update book ratings (Optional) ---
def update_book_average_ratings():
    """Recalculates and updates the average rating for all books based on approved reviews."""
    with app.app_context():
        print("-> Updating book average ratings...")
        books = db.session.query(Book).all()
        updated_count = 0
        if not books:
            print("-> No books found to update ratings.")
            return

        for book in books:
            # Calculate average rating from approved reviews using SQLAlchemy functions
            avg_rating_query = db.session.query(db.func.avg(Review.rating))\
                .filter(Review.book_id == book.id, Review.is_approved == True)

            avg_rating = avg_rating_query.scalar() # Returns the average or None

            # Handle cases where there are no approved reviews (avg_rating is None)
            # Ensure the target column type (Numeric) matches the input type (Decimal)
            new_rating = Decimal(avg_rating or 0).quantize(Decimal("0.01")) # Convert None to 0, ensure Decimal

            # Check if update is needed
            if book.average_rating != new_rating:
                book.average_rating = new_rating
                db.session.add(book) # Mark book for update
                updated_count += 1

        if updated_count > 0:
            try:
                db.session.commit()
                print(f"-> Updated average ratings for {updated_count} books.")
            except Exception as e:
                db.session.rollback()
                print(f"Error updating book average ratings: {e}")
        else:
            print("-> No book average ratings needed updating.")

def reset_book_average_ratings():
     """Resets the average rating for all books to 0.00."""
     with app.app_context():
        print("-> Resetting book average ratings...")
        try:
            # Ensure the value being set matches the column type (Decimal)
            updated_count = db.session.query(Book).update({Book.average_rating: Decimal("0.00")})
            db.session.commit()
            print(f"-> Reset average ratings for {updated_count} books.")
        except Exception as e:
             db.session.rollback()
             print(f"Error resetting book average ratings: {e}")


# --- Main Execution ---

def seed_all(num_users=20, num_langs=5, num_pubs=15, num_authors=50, num_cats=25, num_books=100, num_sellers=10, num_inventory=300, num_addresses=40, num_orders=60, num_reviews=200):
    """Clears and seeds all data in a specific order, handling dependencies."""
    print("--- Starting Database Seed ---")
    # Clear data in reverse order of dependency (or rely on cascade deletes)
    # Clearing explicitly can be safer if cascades are complex or uncertain
    print("\n--- Clearing Data (Reverse Dependency Order) ---")
    clear_order_items()          # Depends on Orders, Inventory, Books, Sellers
    clear_reviews()              # Depends on Books, Users
    clear_orders()               # Depends on Users, Addresses (RESTRICT assumed) -> Cleared after items
    clear_inventory()            # Depends on Books, Sellers (CASCADE assumed for Book/Seller deletion) -> Cleared after items
    clear_sellers()              # Depends on Users (CASCADE assumed) -> Cleared after inventory/orders
    clear_addresses()            # Depends on Users (CASCADE assumed) -> Cleared after orders
    clear_books()                # Depends on Publishers, Languages, Authors, Categories -> Cleared after inventory/reviews/items
    clear_categories()           # Self-referencing, depends on Books (assoc table cleared)
    clear_authors()              # Depends on Books (assoc table cleared)
    clear_publishers()           # Depends on Books (SET NULL assumed)
    clear_languages()            # Depends on Books (SET NULL assumed)
    clear_users()                # Base table - clear last (or handle cascades in User clear)

    # Reset calculated fields after clearing dependents
    reset_book_average_ratings()

    print("\n--- Seeding Data (Dependency Order) ---")
    # Seed data in order of dependency
    seed_users(num_users)
    seed_languages(num_langs)
    seed_publishers(num_pubs)
    seed_authors(num_authors)     # Use actual model
    seed_categories(num_cats)
    seed_books(num_books)         # Depends on Pubs, Langs, Authors, Cats
    seed_sellers(num_sellers)     # Depends on Users
    seed_inventory(num_inventory) # Depends on Books, Sellers
    seed_addresses(num_addresses) # Use actual model, Depends on Users
    created_orders = seed_orders(num_orders) # Depends on Users, Addresses
    if created_orders: # Only seed items if orders were created
        seed_order_items()        # Depends on Orders, Inventory
    seed_reviews(num_reviews)     # Depends on Books, Users

    # Update calculated fields after seeding everything
    update_book_average_ratings()

    print("\n--- Database Seed Complete ---")


if __name__ == "__main__":
    # Example usage: Seed with default numbers
    seed_all()

    # Example usage: Clear all data
    # print("\n--- Clearing All Data ---")
    # clear_order_items()
    # clear_reviews()
    # clear_orders()
    # clear_inventory()
    # clear_sellers()
    # clear_addresses()
    # clear_books()
    # clear_categories()
    # clear_authors()
    # clear_publishers()
    # clear_languages()
    # clear_users()
    # reset_book_average_ratings() # Reset calculated fields too
    # print("--- All Data Cleared ---")

    # Example: Seed only users
    # clear_users()
    # seed_users(5)
