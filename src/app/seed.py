import random
import click
import traceback
from faker import Faker
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash # Use a proper password hasher

from .extensions import db
from .model import *

# Configuration for the number of records to generate
NUM_USERS = 50
NUM_SELLERS_PERCENT = 0.2 # Percentage of users who are also sellers
NUM_AUTHORS = 30
NUM_PUBLISHERS = 15
NUM_CATEGORIES = 20
NUM_BOOKS = 100
NUM_RATINGS_PER_USER = 5 # Max ratings per user

fake = Faker()

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seeds the database with fake data."""

    # --- DEBUG: Print the database URI being used ---
    try:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        print(f"--- Attempting to seed database: {db_uri}")
        if not db_uri:
             print("--- WARNING: SQLALCHEMY_DATABASE_URI not found in config!")
             return # Stop if URI is missing
    except Exception as e:
        print(f"--- Error accessing database URI from config: {e}")
        return # Stop if there's an error getting the URI

    print("Clearing existing data...")
    # Order matters due to foreign key constraints
    # Use try-except blocks for each delete in case some tables don't exist yet
    # or have dependencies that prevent deletion initially.
    try: Rating.query.delete()
    except Exception as e: print(f"Could not delete Ratings: {e}")
    try: Book.query.delete() # Assuming cascade delete is set for book associations or handle manually
    except Exception as e: print(f"Could not delete Books: {e}")
    try: Seller.query.delete()
    except Exception as e: print(f"Could not delete Sellers: {e}")
    try: User.query.delete() # Deleting users should cascade to sellers if set up correctly
    except Exception as e: print(f"Could not delete Users: {e}")
    try: Author.query.delete()
    except Exception as e: print(f"Could not delete Authors: {e}")
    try: Publisher.query.delete()
    except Exception as e: print(f"Could not delete Publishers: {e}")
    try: Category.query.delete()
    except Exception as e: print(f"Could not delete Categories: {e}")

    try:
        db.session.commit()
        print("Existing data cleared (or tables were empty).")
    except Exception as e:
        db.session.rollback()
        print(f"Error during clearing data commit: {e}")
        print("--- Full Traceback for Clearing Error: ---")
        traceback.print_exc() # Print detailed traceback for clearing error
        print("------------------------------------------")
        return # Stop if clearing fails

    print("Seeding database...")

    users = []
    sellers = []
    authors = []
    publishers = []
    categories = []
    books = []
    referral_codes = set()

    # --- Generate Users ---
    print(f"Generating {NUM_USERS} users...")
    user_roles = ['customer', 'seller']
    num_sellers_target = int(NUM_USERS * NUM_SELLERS_PERCENT)
    seller_count = 0

    # Generate unique referral codes first
    while len(referral_codes) < NUM_USERS:
        referral_codes.add(fake.unique.bothify(text='??????##'))
    referral_codes_list = list(referral_codes)
    random.shuffle(referral_codes_list) # Shuffle for random assignment

    # Keep track of used emails and usernames
    used_emails = set()
    used_usernames = set()

    for i in range(NUM_USERS):
        # Ensure unique username
        username = fake.unique.user_name()
        while User.query.filter_by(username=username).first() or username in used_usernames:
             print(f"Username '{username}' collision, generating new one.")
             username = fake.unique.user_name() + str(random.randint(100,999)) # Add random digits
        used_usernames.add(username)

        # Ensure unique email
        email = fake.unique.email()
        while User.query.filter_by(email=email).first() or email in used_emails:
            print(f"Email '{email}' collision, generating new one.")
            email = f"{fake.unique.user_name()}{random.randint(100,999)}@example.com" # Generate safer unique email
        used_emails.add(email)

        # Assign role - ensure we get enough sellers
        if seller_count < num_sellers_target:
            role = 'seller'
            seller_count += 1
        else:
            role = 'customer'

        # Assign referral - make sure not to refer self, handle first user
        referred_by_code = None
        if i > 0 and random.random() < 0.5: # 50% chance to be referred
             # Ensure the referred_by code exists and isn't the user's own code
            possible_referrers = [rc for rc in referral_codes_list[:i] if rc != referral_codes_list[i]]
            if possible_referrers:
                 referred_by_code = random.choice(possible_referrers)


        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(f"password{i}"),
            balance=random.uniform(0, 500),
            referral_code=referral_codes_list[i], # Already unique
            referred_by=referred_by_code,
            role=role
        )
        users.append(user)

    db.session.add_all(users)
    # Flush here can help catch early errors like duplicate users if checks above fail
    try:
        print("Flushing Users...")
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        print(f"Error during User flush: {e}")
        print("--- Full Traceback for User Flush Error: ---")
        traceback.print_exc()
        print("--------------------------------------------")
        return # Stop if users can't be flushed

    # --- Generate Sellers ---
    print("Generating sellers...")
    for user in users:
        if user.role == 'seller':
             # Check if a seller profile already exists for this user_id (shouldn't due to unique constraint, but good practice)
             if not Seller.query.filter_by(user_id=user.id).first():
                 seller = Seller(
                     user_id=user.id,
                     name=fake.company(),
                     location=fake.address()
                 )
                 sellers.append(seller)

    db.session.add_all(sellers)
    try:
        print("Flushing Sellers...")
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        print(f"Error during Seller flush: {e}")
        print("--- Full Traceback for Seller Flush Error: ---")
        traceback.print_exc()
        print("---------------------------------------------")
        # Decide if you want to stop or continue without these sellers
        # return

    # --- Generate Authors ---
    print(f"Generating {NUM_AUTHORS} authors...")
    for _ in range(NUM_AUTHORS):
        author = Author(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            bio=fake.paragraph(nb_sentences=3)
        )
        authors.append(author)
    db.session.add_all(authors)

    # --- Generate Publishers ---
    print(f"Generating {NUM_PUBLISHERS} publishers...")
    used_publisher_names = set()
    for _ in range(NUM_PUBLISHERS):
        name = fake.unique.company()
        # Check against DB and local set for uniqueness
        while Publisher.query.filter_by(name=name).first() or name in used_publisher_names:
             print(f"Publisher name '{name}' collision, generating new one.")
             name = fake.unique.company() + f" {random.randint(100,999)}"
        used_publisher_names.add(name)
        publisher = Publisher(name=name)
        publishers.append(publisher)
    db.session.add_all(publishers)

    # --- Generate Categories ---
    print(f"Generating {NUM_CATEGORIES} categories...")
    predefined_categories = [
        "Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller", "Romance",
        "Historical Fiction", "Non-Fiction", "Biography", "History", "Science",
        "Technology", "Programming", "Business", "Self-Help", "Cooking", "Travel",
        "Art", "Poetry", "Children's Books"
    ]
    random.shuffle(predefined_categories)
    used_category_names = set()

    for i in range(min(NUM_CATEGORIES, len(predefined_categories))):
         name = predefined_categories[i]
         # Check against DB and local set
         if not Category.query.filter_by(name=name).first() and name not in used_category_names:
             category = Category(name=name)
             categories.append(category)
             used_category_names.add(name)

    # Generate more if needed
    while len(categories) < NUM_CATEGORIES:
        name = fake.unique.word().capitalize()
        # Simple check, might need better category name generation
        # Check against DB and local set
        if len(name) > 3 and not Category.query.filter_by(name=name).first() and name not in used_category_names:
            category = Category(name=name)
            categories.append(category)
            used_category_names.add(name)
        else:
             print(f"Category name '{name}' collision or too short, skipping.")
             # Ensure fake.unique doesn't get stuck if all words are used/short
             if len(used_category_names) > 500: # Safety break
                 break


    db.session.add_all(categories)

    # Flush Authors, Publishers, Categories before creating Books
    try:
        print("Flushing Authors, Publishers, Categories...")
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        print(f"Error during Author/Publisher/Category flush: {e}")
        print("--- Full Traceback for APC Flush Error: ---")
        traceback.print_exc()
        print("------------------------------------------")
        return # Stop if these fail, as Books depend on them

    # Refresh lists to ensure we have IDs (especially important if not stopping on seller flush error)
    db.session.expire_all() # Clears local session cache, forces reload on access
    users = User.query.all()
    sellers = Seller.query.all()
    authors = Author.query.all()
    publishers = Publisher.query.all()
    categories = Category.query.all()

    # --- Generate Books ---
    print(f"Generating {NUM_BOOKS} books...")
    if not sellers:
        print("Error: No sellers available in the database. Books cannot be created.")
        return
    if not authors:
        print("Warning: No authors available in the database.")
        # Decide if you want to proceed without authors or stop
    if not categories:
        print("Warning: No categories available in the database.")
        # Decide if you want to proceed without categories or stop

    for _ in range(NUM_BOOKS):
        # Choose relationships safely
        book_publisher = random.choice(publishers + [None]) if publishers else None
        book_seller = random.choice(sellers) # Already checked sellers exist
        book_authors = random.sample(authors, k=random.randint(1, min(3, len(authors)))) if authors else []
        book_categories = random.sample(categories, k=random.randint(1, min(4, len(categories)))) if categories else []

        book = Book(
            title=fake.catch_phrase(),
            publisher_id=book_publisher.id if book_publisher else None,
            description=fake.text(max_nb_chars=500),
            quantity=random.randint(0, 100),
            price=round(random.uniform(5.0, 150.0), 2),
            discount_percent=random.randint(0, 50),
            image_url_1=fake.image_url(width=480, height=640),
            image_url_2=fake.image_url(width=480, height=640) if random.random() > 0.5 else None,
            image_url_3=fake.image_url(width=480, height=640) if random.random() > 0.8 else None,
            seller_id=book_seller.id,
        )

        # Add many-to-many relationships
        for author in book_authors:
            book.authors.append(author)
        for category in book_categories:
            book.categories.append(category)

        books.append(book)

    db.session.add_all(books)
    try:
        print("Flushing Books...")
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        print(f"Error during Book flush: {e}")
        print("--- Full Traceback for Book Flush Error: ---")
        traceback.print_exc()
        print("-----------------------------------------")
        # Decide if you want to stop or continue without these books
        # return

    # Refresh books list after potential flush errors
    db.session.expire_all()
    books = Book.query.all()
    users = User.query.all() # Refresh users too

    # --- Generate Ratings ---
    print("Generating ratings...")
    if not users or not books:
        print("Warning: No users or books available to generate ratings.")
    else:
        ratings = []
        # Ensure we don't try to rate the same book twice by the same user
        user_book_pairs = set()
        for user in users:
            num_ratings_to_add = random.randint(0, min(NUM_RATINGS_PER_USER, len(books)))
            if num_ratings_to_add > 0:
                available_books = [b for b in books if (user.id, b.id) not in user_book_pairs]
                # Ensure we don't request more samples than available
                k = min(num_ratings_to_add, len(available_books))
                if k > 0:
                    rated_books = random.sample(available_books, k=k)
                    for book in rated_books:
                        # Check if rating already exists (paranoid check)
                        if not Rating.query.filter_by(user_id=user.id, book_id=book.id).first():
                            rating = Rating(
                                user_id=user.id,
                                book_id=book.id,
                                score=random.randint(1, 5),
                                text=fake.paragraph(nb_sentences=2) if random.random() > 0.3 else None
                            )
                            ratings.append(rating)
                            user_book_pairs.add((user.id, book.id)) # Track added rating
        db.session.add_all(ratings)

    # --- Final Commit ---
    print(f"--- Attempting final commit for {len(users)} users, {len(sellers)} sellers, {len(authors)} authors, {len(publishers)} publishers, {len(categories)} categories, {len(books)} books, {len(ratings)} ratings...")
    try:
        db.session.commit()
        print("--- Database seeded successfully! ---")
    except Exception as e:
        db.session.rollback()
        print(f"--- FINAL COMMIT FAILED! Error: {e}")
        print("--- Full Traceback for Commit Error: ---")
        traceback.print_exc() # Print detailed traceback
        print("----------------------------------------")
        print("--- Transaction rolled back. Database might be partially cleared or unchanged from before seeding attempt. ---")
