import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy import text
from .extensions import db
from src.app.model.author import Author
from src.app.model.blacklist_token import BlacklistToken
from src.app.model.book import Book
from src.app.model.category import Category
from src.app.model.city import City
from src.app.model.country import Country
from src.app.model.location import Location
from src.app.model.publisher import Publisher
from src.app.model.rating import Rating
from src.app.model.state import State
from src.app.model.user import User
from src.app.model.voucher import Voucher, VoucherType # Ensure VoucherType is importable
from src.app.utils.security import hash_password, generate_referral_code

fake = Faker()
fake_id = Faker(['id_ID']) # For Indonesian-specific data if needed

def clear_data():
    """Clears all data from relevant tables."""
    # app = create_app() # Ensure app context if run standalone outside Flask CLI
    # with app.app_context():
    # For MySQL/MariaDB to temporarily disable foreign key checks
    # db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # Order is important due to foreign key constraints
    BlacklistToken.query.delete()
    Rating.query.delete()
    Voucher.query.delete()
    # book_category_table is implicitly handled by Book.categories relationship
    # If direct manipulation: db.session.execute(book_category_table.delete())
    Book.query.delete()
    Category.query.delete()
    Author.query.delete()
    Publisher.query.delete()
    User.query.delete()
    Location.query.delete()
    City.query.delete()
    State.query.delete()
    Country.query.delete()
    
    db.session.commit()
    
    # For MySQL/MariaDB to re-enable foreign key checks
    # db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    print("All data cleared.")

def seed_countries(count=5):
    countries = []
    for _ in range(count):
        try:
            country = Country(name=fake.unique.country(), code=fake.unique.country_code())
            db.session.add(country)
            countries.append(country)
        except Exception as e: # Catch potential unique constraint violation if Faker runs out
            print(f"Skipping country due to error: {e}")
            db.session.rollback()
            fake.unique.clear() # Clear unique history for this provider
            country = Country(name=fake.unique.country(), code=fake.unique.country_code()) # Try once more
            db.session.add(country)
            countries.append(country)
    db.session.flush() # Flush to get IDs for relationships
    return countries

def seed_states(countries, states_per_country=2):
    states = []
    for country in countries:
        for _ in range(states_per_country):
            state = State(name=fake.state(), country_id=country.id)
            db.session.add(state)
            states.append(state)
    db.session.flush()
    return states

def seed_cities(states, cities_per_state=2):
    cities = []
    for state in states:
        for _ in range(cities_per_state):
            city = City(name=fake.city(), state_id=state.id)
            db.session.add(city)
            cities.append(city)
    db.session.flush()
    return cities

def seed_locations(cities, count=30):
    locations = []
    for _ in range(count):
        if not cities:
            print("No cities to assign locations to. Skipping location seeding.")
            return locations
        location = Location(
            name=fake.street_name(),
            address=fake.address(),
            zip_code=fake.zipcode(),
            city_id=random.choice(cities).id
        )
        db.session.add(location)
        locations.append(location)
    db.session.flush()
    return locations

def seed_users(locations, count=20):
    users = []
    for _ in range(count):
        user = User(
            full_name=fake.name(),
            email=fake.unique.email(),
            password_hash=hash_password("password123"), # Default password
            role=random.choice(['customer', 'admin', 'seller']),
            balance=fake.pydecimal(left_digits=5, right_digits=2, min_value=0, max_value=100000),
            # referral_code=generate_referral_code(), # User model handles this on init
            location_id=random.choice([loc.id for loc in locations] + [None]) if locations else None,
            is_active=True
        )
        db.session.add(user)
        users.append(user)
    db.session.flush()
    return users

def seed_authors(count=10):
    authors = []
    for _ in range(count):
        author = Author(full_name=fake.name(), bio=fake.text(max_nb_chars=300))
        db.session.add(author)
        authors.append(author)
    db.session.flush()
    return authors

def seed_publishers(count=5):
    publishers = []
    for _ in range(count):
        try:
            publisher = Publisher(name=fake.unique.company())
            db.session.add(publisher)
            publishers.append(publisher)
        except Exception as e:
            print(f"Skipping publisher due to error: {e}")
            db.session.rollback()
            fake.unique.clear()
            publisher = Publisher(name=fake.unique.company())
            db.session.add(publisher)
            publishers.append(publisher)
    db.session.flush()
    return publishers

def seed_categories(count=8):
    categories_data = ['Fiction', 'Science', 'History', 'Technology', 'Fantasy', 'Biography', 'Mystery', 'Thriller', 'Romance', 'Kids', 'Self-Help', 'Business']
    selected_category_names = random.sample(categories_data, min(count, len(categories_data)))
    
    categories = []
    for name in selected_category_names:
        category = Category.query.filter_by(name=name).first()
        if not category:
            category = Category(name=name)
            db.session.add(category)
        categories.append(category)
    db.session.flush()
    return categories

def seed_books(authors, publishers, users, categories, count=50):
    books = []
    if not authors or not publishers or not users or not categories:
        print("Missing prerequisite data for books (authors, publishers, users, or categories). Skipping book seeding.")
        return books

    seller_users = [u for u in users if u.role in ['seller', 'admin']]
    if not seller_users:
        print("No seller/admin users found to assign books to. Skipping book seeding.")
        return books

    for _ in range(count):
        book = Book(
            title=fake.catch_phrase(),
            author_id=random.choice(authors).id,
            publisher_id=random.choice(publishers).id,
            user_id=random.choice(seller_users).id,
            description=fake.paragraph(nb_sentences=3),
            rating=Decimal(str(fake.random_int(min=1, max=5)) + '.' + str(fake.random_int(min=0, max=99))).quantize(Decimal('0.01')) if random.random() > 0.2 else None,
            quantity=fake.random_int(min=0, max=50),
            price=fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=Decimal('5.00'), max_value=Decimal('200.00')),
            discount_percent=fake.random_int(min=0, max=50),
            image_url_1=fake.image_url(),
            image_url_2=fake.image_url() if random.random() > 0.5 else None,
            image_url_3=fake.image_url() if random.random() > 0.7 else None,
        )
        # Add categories
        book.categories.extend(random.sample(categories, k=random.randint(1, min(3, len(categories)))))
        db.session.add(book)
        books.append(book)
    db.session.flush()
    return books

def seed_ratings(users, books, count=100):
    ratings = []
    if not users or not books:
        print("Missing users or books for ratings. Skipping rating seeding.")
        return ratings
    
    # To avoid duplicate ratings (user_id, book_id)
    rated_pairs = set()

    for _ in range(count):
        user = random.choice(users)
        book = random.choice(books)
        
        if (user.id, book.id) in rated_pairs:
            continue # Skip if this pair has already been rated

        rating = Rating(
            user_id=user.id,
            book_id=book.id,
            score=fake.random_int(min=1, max=5),
            text=fake.sentence() if random.random() > 0.3 else None
        )
        db.session.add(rating)
        ratings.append(rating)
        rated_pairs.add((user.id, book.id))
    db.session.flush()
    return ratings

def seed_vouchers(users, count=15):
    vouchers = []
    if not users:
        print("Missing users for vouchers. Skipping voucher seeding.")
        return vouchers

    for _ in range(count):
        voucher_type_choice = random.choice([VoucherType.PERCENTAGE, VoucherType.FIXED_AMOUNT, VoucherType.WELCOME])
        value = Decimal(fake.random_int(min=5, max=30)) if voucher_type_choice == VoucherType.PERCENTAGE else fake.pydecimal(left_digits=2, right_digits=2, positive=True, min_value=Decimal('5.00'), max_value=Decimal('50.00'))
        
        # Ensure Voucher code is unique using its own generator
        code = Voucher._generate_voucher_code()

        voucher = Voucher(
            code=code,
            name=fake.bs().title() + ' Offer',
            description=fake.sentence(nb_words=6),
            type=voucher_type_choice,
            value=value,
            min_transaction=fake.pydecimal(left_digits=3, right_digits=2, positive=True, min_value=Decimal('10.00'), max_value=Decimal('100.00')),
            max_discount=fake.pydecimal(left_digits=2, right_digits=2, positive=True, min_value=Decimal('10.00'), max_value=Decimal('30.00')) if voucher_type_choice == VoucherType.PERCENTAGE else None,
            expired_date=datetime.utcnow() + timedelta(days=fake.random_int(min=30, max=120)),
            usage_limit=fake.random_int(min=1, max=100),
            user_id=random.choice([u.id for u in users] + [None] * 5) # Some user-specific, many general
        )
        db.session.add(voucher)
        vouchers.append(voucher)
    db.session.flush()
    return vouchers

def seed_blacklist_tokens(count=3):
    tokens = []
    for _ in range(count):
        token = BlacklistToken(
            token=fake.sha256(),
            blacklisted_on=fake.past_datetime()
        )
        db.session.add(token)
        tokens.append(token)
    db.session.flush()
    return tokens

def seed_all():
    # app = create_app() # Ensure app context if run standalone
    # with app.app_context():
    # clear_data() # Uncomment to clear data before seeding

    print("Seeding countries...")
    countries = seed_countries(count=5)
    db.session.commit()

    print("Seeding states...")
    states = seed_states(countries, states_per_country=2)
    db.session.commit()

    print("Seeding cities...")
    cities = seed_cities(states, cities_per_state=2)
    db.session.commit()

    print("Seeding locations...")
    locations = seed_locations(cities, count=30)
    db.session.commit()

    print("Seeding users...")
    users = seed_users(locations, count=20)
    db.session.commit()

    print("Seeding authors...")
    authors = seed_authors(count=10)
    db.session.commit()

    print("Seeding publishers...")
    publishers = seed_publishers(count=5)
    db.session.commit()

    print("Seeding categories...")
    categories = seed_categories(count=8)
    db.session.commit()

    print("Seeding books and book_categories...")
    books = seed_books(authors, publishers, users, categories, count=50)
    db.session.commit()

    print("Seeding ratings...")
    seed_ratings(users, books, count=100)
    db.session.commit()

    print("Seeding vouchers...")
    seed_vouchers(users, count=15)
    db.session.commit()

    # print("Seeding blacklist tokens...")
    # seed_blacklist_tokens(count=3)
    # db.session.commit()

    print("Database seeding complete!")