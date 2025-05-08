from decimal import Decimal
from datetime import datetime

from .extensions import db
from .model.country import Country
from .model.state import State
from .model.city import City
from .model.location import Location
from .model.user import User
from .model.category import Category
from .model.author import Author
from .model.publisher import Publisher
from .model.book import Book
from .model.rating import Rating
# Assuming book_category_table is implicitly handled by SQLAlchemy relationships
# If direct manipulation is needed, it would be imported from .model.book_category_table

# Utility for password hashing if not handled by model's @password.setter
# from .utils.security import hash_password # User model handles this

def seed_geographical_data():
    """Seeds countries, states, and cities."""
    print("Seeding geographical data...")

    # 1. Countries
    countries_data = [
        {"name": "Indonesia", "code": "ID"},
        {"name": "United States", "code": "US"},
        {"name": "Canada", "code": "CA"},
        {"name": "United Kingdom", "code": "GB"},
        {"name": "Germany", "code": "DE"},
        {"name": "France", "code": "FR"},
        {"name": "Japan", "code": "JP"},
        {"name": "Australia", "code": "AU"},
        {"name": "Brazil", "code": "BR"},
        {"name": "India", "code": "IN"},
        {"name": "China", "code": "CN"},
        {"name": "Mexico", "code": "MX"},
        {"name": "South Korea", "code": "KR"},
    ]
    
    created_countries = {}
    for country_data in countries_data:
        country = Country.query.filter_by(name=country_data["name"]).first()
        if not country:
            country = Country(name=country_data["name"], code=country_data["code"])
            db.session.add(country)
        created_countries[country_data["name"]] = country
    db.session.flush() # Flush to get IDs for countries

    # 2. States
    states_data = [
        {"name": "DKI Jakarta", "country_name": "Indonesia"},
        {"name": "West Java", "country_name": "Indonesia"},
        {"name": "California", "country_name": "United States"},
        {"name": "New York", "country_name": "United States"},
        {"name": "Ontario", "country_name": "Canada"},
        {"name": "Quebec", "country_name": "Canada"},
        {"name": "England", "country_name": "United Kingdom"},
        {"name": "Bavaria", "country_name": "Germany"},
        {"name": "Île-de-France", "country_name": "France"},
        {"name": "Tokyo", "country_name": "Japan"}, # Tokyo is often treated as a prefecture with state-like status
        {"name": "New South Wales", "country_name": "Australia"},
    ]
    # Added more states
    states_data.extend([
        {"name": "Rio de Janeiro", "country_name": "Brazil"},
        {"name": "São Paulo", "country_name": "Brazil"},
        {"name": "Maharashtra", "country_name": "India"},
        {"name": "Delhi", "country_name": "India"},
        {"name": "Guangdong", "country_name": "China"},
        {"name": "Beijing", "country_name": "China"},
        {"name": "Mexico City", "country_name": "Mexico"}, # Mexico City is a state-level entity
        {"name": "Gyeonggi", "country_name": "South Korea"},
    ])

    created_states = {}
    for state_data in states_data:
        country = created_countries.get(state_data["country_name"])
        if country:
            state = State.query.filter_by(name=state_data["name"], country_id=country.id).first()
            if not state:
                state = State(name=state_data["name"], country=country)
                db.session.add(state)
            created_states[state_data["name"]] = state
    db.session.flush() # Flush to get IDs for states

    # 3. Cities
    cities_data = [
        {"name": "Jakarta", "state_name": "DKI Jakarta"},
        {"name": "Bandung", "state_name": "West Java"},
        {"name": "Los Angeles", "state_name": "California"},
        {"name": "San Francisco", "state_name": "California"},
        {"name": "New York City", "state_name": "New York"},
        {"name": "Toronto", "state_name": "Ontario"},
        {"name": "Montreal", "state_name": "Quebec"},
        {"name": "London", "state_name": "England"},
        {"name": "Munich", "state_name": "Bavaria"},
        {"name": "Paris", "state_name": "Île-de-France"},
        {"name": "Shibuya", "state_name": "Tokyo"}, # A special ward within Tokyo
        {"name": "Sydney", "state_name": "New South Wales"},
    ]
    # Added more cities
    cities_data.extend([
        {"name": "Rio de Janeiro", "state_name": "Rio de Janeiro"},
        {"name": "São Paulo", "state_name": "São Paulo"},
        {"name": "Mumbai", "state_name": "Maharashtra"},
        {"name": "Delhi", "state_name": "Delhi"},
        {"name": "Guangzhou", "state_name": "Guangdong"},
        {"name": "Beijing", "state_name": "Beijing"},
        {"name": "Mexico City", "state_name": "Mexico City"},
        {"name": "Seoul", "state_name": "Gyeonggi"}, # Seoul is a special city, often treated separately, but linking to Gyeonggi for simplicity here
    ])

    for city_data in cities_data:
        state = created_states.get(city_data["state_name"])
        if state:
            city = City.query.filter_by(name=city_data["name"], state_id=state.id).first()
            if not city:
                city = City(name=city_data["name"], state=state)
                db.session.add(city)
    
    # Commit is handled by seed_all() after this function call
    print("Geographical data prepared for commit.")

def seed_users():
    """Seeds users."""
    print("Seeding users...")
    users_data = [
        {"full_name": "Alice Wonderland", "email": "alice@example.com", "password": "SecurePassword123", "role": "admin"},
        {"full_name": "Bob The Builder", "email": "bob@example.com", "password": "PasswordBob321", "role": "seller"},
        {"full_name": "Charlie Brown", "email": "charlie@example.com", "password": "CharlieSecure!", "role": "customer"},
        {"full_name": "Diana Prince", "email": "diana@example.com", "password": "WonderPass1", "role": "seller"},
        {"full_name": "Edward Scissorhands", "email": "edward@example.com", "password": "CutItOutPass", "role": "customer"},
        {"full_name": "Fiona Apple", "email": "fiona@example.com", "password": "MusicLover99", "role": "customer"},
        {"full_name": "George Orwell", "email": "george@example.com", "password": "BigBrotherPass", "role": "seller"},
        {"full_name": "Harry Potter", "email": "harry@example.com", "password": "ExpectoPass", "role": "customer"},
        {"full_name": "Ivy Green", "email": "ivy@example.com", "password": "IvyPassword", "role": "seller"},
        {"full_name": "Jack Black", "email": "jack@example.com", "password": "JackPass", "role": "customer"},
        {"full_name": "Kara Danvers", "email": "kara@example.com", "password": "SuperPass", "role": "customer"},
        {"full_name": "Liam Neeson", "email": "liam@example.com", "password": "TakenPass", "role": "seller"},
        {"full_name": "Mia Thermopolis", "email": "mia@example.com", "password": "PrincessPass", "role": "customer"},
        {"full_name": "Noah Builder", "email": "noah@example.com", "password": "ArkPass", "role": "customer"},
    ]

    for user_data in users_data:
        user = User.query.filter_by(email=user_data["email"]).first()
        if not user:
            # The User model's __init__ and @password.setter handle password hashing and referral_code
            user = User(
                full_name=user_data["full_name"],
                email=user_data["email"],
                password=user_data["password"], # Password will be hashed by the setter
                role=user_data["role"]
            )
            db.session.add(user)
            
    # Commit is handled by seed_all()
    print("Users prepared for commit.")

def seed_locations():
    """Seeds locations."""
    print("Seeding locations...")

    locations_data = [
        {"name": "Central Park Apartment", "address": "123 Green St", "zip_code": "10110", "city_name": "Jakarta"},
        {"name": "Tech Hub Office", "address": "456 Innovation Ave", "zip_code": "94107", "city_name": "San Francisco"},
        {"name": "Downtown Bookstore", "address": "789 Main St", "zip_code": "M5H2N2", "city_name": "Toronto"},
        {"name": "Riverside Cafe", "address": "101 River Rd", "zip_code": "75001", "city_name": "Paris"},
        {"name": "Mountain View House", "address": "22 Peak Cir", "zip_code": "80302", "city_name": "Bandung"},
        {"name": "Beachside Villa", "address": "33 Ocean Dr", "zip_code": "90210", "city_name": "Los Angeles"},
        {"name": "Shibuya Crossing Point", "address": "1 Chome Dogenzaka", "zip_code": "150-0043", "city_name": "Shibuya"},
        {"name": "The Rocks Historical Site", "address": "10 Playfair St", "zip_code": "2000", "city_name": "Sydney"},
        {"name": "Copacabana Beach Kiosk", "address": "Av. Atlântica, S/N", "zip_code": "22070-010", "city_name": "Rio de Janeiro"},
        {"name": "Ibirapuera Park Entrance", "address": "Av. Pedro Álvares Cabral, S/N", "zip_code": "04094-050", "city_name": "São Paulo"},
        {"name": "Gateway of India", "address": "Apollo Bunder", "zip_code": "400001", "city_name": "Mumbai"},
        {"name": "Red Fort Area", "address": "Netaji Subhash Marg", "zip_code": "110006", "city_name": "Delhi"},
        {"name": "Canton Tower Observation Deck", "address": "Yuejiang W Rd", "zip_code": "510623", "city_name": "Guangzhou"},
        {"name": "Forbidden City Entrance", "address": "4 Jingshan Front St", "zip_code": "100009", "city_name": "Beijing"},
        {"name": "Zocalo Square", "address": "Plaza de la Constitución S/N", "zip_code": "06060", "city_name": "Mexico City"},
        {"name": "Gangnam Station Area", "address": "Gangnam-daero", "zip_code": "06242", "city_name": "Seoul"},
    ]

    for loc_data in locations_data:
        city = City.query.filter_by(name=loc_data["city_name"]).first()
        if city:
            location = Location.query.filter_by(address=loc_data["address"], city_id=city.id).first()
            if not location:
                location = Location(
                    name=loc_data["name"],
                    address=loc_data["address"],
                    zip_code=loc_data["zip_code"],
                    city_id=city.id  # Link to the fetched city
                )
                db.session.add(location)
        else:
            print(f"Warning: City '{loc_data['city_name']}' not found for location '{loc_data['name']}'. Skipping.")

    # Commit is handled by seed_all()
    print("Locations prepared for commit.")

def assign_locations_to_users():
    """Assigns locations to existing users."""
    print("Assigning locations to users...")

    users = User.query.all()
    locations = Location.query.all()

    if not users:
        print("No users found to assign locations to. Skipping.")
        return
    if not locations:
        print("No locations found to assign to users. Skipping.")
        return

    # Simple assignment: distribute locations among users
    # More sophisticated logic could be used for specific assignments
    for i, user in enumerate(users):
        if user.location_id is None: # Assign only if user doesn't have a location
            location_to_assign = locations[i % len(locations)] # Cycle through locations
            user.location_id = location_to_assign.id
            print(f"Assigning location '{location_to_assign.name}' (ID: {location_to_assign.id}) to user '{user.full_name}' (ID: {user.id})")
            db.session.add(user)

    # Commit is handled by seed_all()
    print("Locations assigned to users, prepared for commit.")

def seed_book_metadata():
    """Seeds categories, authors, and publishers."""
    print("Seeding book metadata (categories, authors, publishers)...")

    # 1. Categories
    categories_data = [
        "Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller",
        "Non-Fiction", "Biography", "History", "Science", "Technology",
        "Self-Help", "Business", "Programming", "Children's Books", "Comics",
        "Thriller", "Biography", "History", "Science", "Technology",
        "Art", "Music", "Cooking", "Travel", "Health", "Fitness"
    ]
    created_categories = {}
    for cat_name in categories_data:
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
        created_categories[cat_name] = category
    db.session.flush() # Get IDs if needed later, though direct objects are fine

    # 2. Authors
    authors_data = [
        {"full_name": "J.K. Rowling", "bio": "Author of the Harry Potter series."},
        {"full_name": "George R.R. Martin", "bio": "Author of A Song of Ice and Fire."},
        {"full_name": "J.R.R. Tolkien", "bio": "Author of The Lord of the Rings."},
        {"full_name": "Agatha Christie", "bio": "Queen of Mystery."},
        {"full_name": "Stephen King", "bio": "Master of Horror."},
        {"full_name": "Isaac Asimov", "bio": "Prolific science fiction writer."},
        {"full_name": "Walter Isaacson", "bio": "Biographer of innovators."},
        {"full_name": "Yuval Noah Harari", "bio": "Historian and author of Sapiens."},
        {"full_name": "Charles Petzold", "bio": "Author of Code: The Hidden Language of Computer Hardware and Software"},
        {"full_name": "Eric Matthes", "bio": "Author of Python Crash Course."}
    ]
    # Added more authors
    authors_data.extend([
        {"full_name": "Jane Austen", "bio": "Known for her six major novels."},
        {"full_name": "George Orwell", "bio": "Author of Nineteen Eighty-Four and Animal Farm."},
        {"full_name": "Aldous Huxley", "bio": "Author of Brave New World."},
        {"full_name": "Carl Sagan", "bio": "Astronomer, planetary scientist, cosmologist, astrophysicist, astrobiologist, author, and science communicator."},
        {"full_name": "Bill Bryson", "bio": "Author of popular science and travel books."},
    ])
    created_authors = {}
    for author_data in authors_data:
        author = Author.query.filter_by(full_name=author_data["full_name"]).first()
        if not author:
            author = Author(full_name=author_data["full_name"], bio=author_data.get("bio"))
            db.session.add(author)
        created_authors[author_data["full_name"]] = author
    db.session.flush()

    # 3. Publishers
    publishers_data = [
        "Bloomsbury", "Bantam Spectra", "Allen & Unwin", "HarperCollins",
        "Scribner", "Doubleday", "Simon & Schuster", "Harvill Secker", "Microsoft Press", "No Starch Press",
        # Added more publishers
        "Penguin Books", "Vintage Books", "Harper", "W. W. Norton & Company", "Broadway Books"
    ]
    created_publishers = {}
    for pub_name in publishers_data:
        publisher = Publisher.query.filter_by(name=pub_name).first()
        if not publisher:
            publisher = Publisher(name=pub_name)
            db.session.add(publisher)
        created_publishers[pub_name] = publisher
    
    # Commit is handled by seed_all()
    print("Book metadata (categories, authors, publishers) prepared for commit.")

def seed_books():
    """Seeds books and their relationships to categories."""
    print("Seeding books...")

    # Ensure previous data is available or query it
    # For simplicity, we'll query, but in a large seeder, passing created objects might be better.
    authors = {author.full_name: author for author in Author.query.all()}
    publishers = {publisher.name: publisher for publisher in Publisher.query.all()}
    categories_map = {category.name: category for category in Category.query.all()}
    # Sellers are users with the 'seller' role, or any user for this example
    sellers = {user.email: user for user in User.query.filter_by(role='seller').all()}
    if not sellers: # Fallback to any user if no specific sellers found
        all_users = User.query.all()
        if all_users:
            sellers = {user.email: user for user in all_users} # Use any user as a seller
        else:
            print("Warning: No users found to act as sellers. Books cannot be seeded without a user_id.")
            return


    books_data = [
        {
            "title": "Harry Potter and the Sorcerer's Stone", "author_name": "J.K. Rowling",
            "publisher_name": "Bloomsbury", "seller_email": "bob@example.com", # Bob is a seller
            "description": "The first book in the Harry Potter series.", "quantity": 50, "price": Decimal("19000"),
            "discount_percent": 10, "image_url_1": "https://example.com/hp1.jpg",
            "category_names": ["Fantasy", "Children's Books"]
        },
        {
            "title": "A Game of Thrones", "author_name": "George R.R. Martin",
            "publisher_name": "Bantam Spectra", "seller_email": "diana@example.com", # Diana is a seller
            "description": "The first book in A Song of Ice and Fire.", "quantity": 30, "price": Decimal("250000"),
            "discount_percent": 0, "image_url_1": "https://example.com/got1.jpg",
            "category_names": ["Fantasy", "Fiction"]
        },
        {
            "title": "The Hobbit", "author_name": "J.R.R. Tolkien",
            "publisher_name": "Allen & Unwin", "seller_email": "bob@example.com",
            "description": "A prelude to The Lord of the Rings.", "quantity": 40, "price": Decimal("150000"),
            "discount_percent": 5, "image_url_1": "https://example.com/hobbit.jpg",
            "category_names": ["Fantasy", "Children's Books"]
        },
        {
            "title": "Murder on the Orient Express", "author_name": "Agatha Christie",
            "publisher_name": "HarperCollins", "seller_email": "diana@example.com",
            "description": "A classic Hercule Poirot mystery.", "quantity": 25, "price": Decimal("120099"),
            "discount_percent": 0, "image_url_1": "https://example.com/orient.jpg",
            "category_names": ["Mystery", "Thriller"]
        },
        {
            "title": "Sapiens: A Brief History of Humankind", "author_name": "Yuval Noah Harari",
            "publisher_name": "Harvill Secker", "seller_email": "george@example.com", # George is a seller
            "description": "A captivating account of human history.", "quantity": 60, "price": Decimal("69999"),
            "discount_percent": 15, "image_url_1": "https://example.com/sapiens.jpg",
            "category_names": ["Non-Fiction", "History", "Science"]
        },
        {
            "title": "Code: The Hidden Language of Computer Hardware and Software", "author_name": "Charles Petzold",
            "publisher_name": "Microsoft Press", "seller_email": "bob@example.com",
            "description": "Explains the C# language.", "quantity": 35, "price": Decimal("49.99"),
            "discount_percent": 10, "image_url_1": "https://example.com/code_petzold.jpg",
            "category_names": ["Technology", "Programming", "Non-Fiction"]
        },
        {
            "title": "Python Crash Course", "author_name": "Eric Matthes",
            "publisher_name": "No Starch Press", "seller_email": "diana@example.com",
            "description": "A hands-on, project-based introduction to programming.", "quantity": 70, "price": Decimal("35595"),
            "discount_percent": 5, "image_url_1": "https://example.com/python_crash.jpg",
            "category_names": ["Technology", "Programming", "Self-Help"]
        },
        {
            "title": "Pride and Prejudice", "author_name": "Jane Austen",
            "publisher_name": "Penguin Books", "seller_email": "ivy@example.com", # Ivy is a seller
            "description": "A novel of manners.", "quantity": 20, "price": Decimal("10.50"),
            "discount_percent": 0, "image_url_1": "https://example.com/pride_prejudice.jpg",
            "category_names": ["Fiction"]
        },
        {
            "title": "Nineteen Eighty-Four", "author_name": "George Orwell",
            "publisher_name": "Vintage Books", "seller_email": "liam@example.com", # Liam is a seller
            "description": "A dystopian social science fiction novel.", "quantity": 30, "price": Decimal("14.00"),
            "discount_percent": 10, "image_url_1": "https://example.com/1984.jpg",
            "category_names": ["Fiction", "Science Fiction", "Thriller"]
        },
        {
            "title": "Brave New World", "author_name": "Aldous Huxley",
            "publisher_name": "Harper", "seller_email": "ivy@example.com",
            "description": "A dystopian novel.", "quantity": 25, "price": Decimal("13.50"),
            "discount_percent": 5, "image_url_1": "https://example.com/brave_new_world.jpg",
            "category_names": ["Fiction", "Science Fiction"]
        },
        {
            "title": "Cosmos", "author_name": "Carl Sagan",
            "publisher_name": "W. W. Norton & Company", "seller_email": "liam@example.com",
            "description": "A personal exploration of the cosmos.", "quantity": 40, "price": Decimal("18.00"),
            "discount_percent": 0, "image_url_1": "https://example.com/cosmos.jpg",
            "category_names": ["Non-Fiction", "Science"]
        },
        {
            "title": "A Short History of Nearly Everything", "author_name": "Bill Bryson",
            "publisher_name": "Broadway Books", "seller_email": "ivy@example.com",
            "description": "A journey through the history of science.", "quantity": 35, "price": Decimal("16.50"),
            "discount_percent": 15, "image_url_1": "https://example.com/short_history.jpg",
            "category_names": ["Non-Fiction", "Science", "History"]
        }
    ]

    for book_data in books_data:
        # Check if book already exists by title and author to prevent duplicates
        author = authors.get(book_data["author_name"])
        if not author:
            print(f"Warning: Author '{book_data['author_name']}' not found for book '{book_data['title']}'. Skipping.")
            continue
        
        existing_book = Book.query.filter_by(title=book_data["title"], author_id=author.id).first()
        if existing_book:
            print(f"Book '{book_data['title']}' by '{book_data['author_name']}' already exists. Skipping.")
            continue

        publisher = publishers.get(book_data["publisher_name"])
        seller = sellers.get(book_data["seller_email"])

        if not publisher:
            print(f"Warning: Publisher '{book_data['publisher_name']}' not found for book '{book_data['title']}'. Skipping.")
            continue
        if not seller:
            print(f"Warning: Seller with email '{book_data['seller_email']}' not found for book '{book_data['title']}'. Trying any seller.")
            # Fallback: try to get any seller if the specified one is not found or not a seller
            if sellers: # Check if sellers dict is not empty
                seller = next(iter(sellers.values())) # Get the first available seller
                print(f"Using fallback seller '{seller.full_name}' for book '{book_data['title']}'.")
            else: # If still no seller, then skip
                print(f"Critical: No seller available for book '{book_data['title']}'. Skipping.")
                continue


        book = Book(
            title=book_data["title"],
            author_id=author.id,
            publisher_id=publisher.id,
            user_id=seller.id, # Seller's ID
            description=book_data["description"],
            quantity=book_data["quantity"],
            price=book_data["price"],
            discount_percent=book_data["discount_percent"],
            image_url_1=book_data.get("image_url_1"),
            # rating will be calculated or set by ratings seed
        )

        # Add categories
        for cat_name in book_data["category_names"]:
            category = categories_map.get(cat_name)
            if category:
                book.categories.append(category)
            else:
                print(f"Warning: Category '{cat_name}' not found for book '{book_data['title']}'.")
        
        db.session.add(book)

    # Commit is handled by seed_all()
    print("Books prepared for commit.")

def seed_ratings():
    """Seeds ratings for books by users."""
    print("Seeding ratings...")

    users = {user.email: user for user in User.query.all()}
    books = {book.title: book for book in Book.query.all()}

    if not users or not books:
        print("Warning: No users or books found. Cannot seed ratings.")
        return

    ratings_data = [
        {
            "user_email": "alice@example.com", "book_title": "Harry Potter and the Sorcerer's Stone",
            "score": 5, "text": "A magical start to a fantastic series!"
        },
        {
            "user_email": "charlie@example.com", "book_title": "Harry Potter and the Sorcerer's Stone",
            "score": 4, "text": "Enjoyed it, very imaginative."
        },
        {
            "user_email": "bob@example.com", "book_title": "A Game of Thrones", # Bob is a seller, but can also rate
            "score": 5, "text": "Epic fantasy, couldn't put it down."
        },
        {
            "user_email": "diana@example.com", "book_title": "The Hobbit",
            "score": 4, "text": "A charming adventure."
        },
        {
            "user_email": "edward@example.com", "book_title": "Murder on the Orient Express",
            "score": 5, "text": "Classic mystery, brilliantly plotted."
        },
        {
            "user_email": "fiona@example.com", "book_title": "Sapiens: A Brief History of Humankind",
            "score": 5, "text": "Mind-expanding and thought-provoking."
        },
        {
            "user_email": "alice@example.com", "book_title": "Sapiens: A Brief History of Humankind",
            "score": 4, "text": "Very insightful read."
        },
        {
            "user_email": "harry@example.com", "book_title": "Python Crash Course",
            "score": 5, "text": "Excellent for beginners! Helped me a lot."
        },
        {
            "user_email": "george@example.com", "book_title": "Code: The Hidden Language of Computer Hardware and Software",
            "score": 4, "text": "A foundational book for understanding computers."
        },
        {
            "user_email": "charlie@example.com", "book_title": "A Game of Thrones",
            "score": 5, "text": "Incredible world-building!"
        },
        {
            "user_email": "edward@example.com", "book_title": "The Hobbit",
            "score": 1, "text": "A lovely fantasy story."
        },
        {
            "user_email": "fiona@example.com", "book_title": "Murder on the Orient Express",
            "score": 5, "text": "Kept me guessing until the end."
        },
        {
            "user_email": "harry@example.com", "book_title": "Sapiens: A Brief History of Humankind",
            "score": 5, "text": "Changed my perspective on history."
        },
        {
            "user_email": "jack@example.com", "book_title": "Python Crash Course",
            "score": 5, "text": "Easy to follow and practical."
        },
        {
            "user_email": "kara@example.com", "book_title": "Pride and Prejudice",
            "score": 2, "text": "A charming classic."
        },
        {
            "user_email": "mia@example.com", "book_title": "Nineteen Eighty-Four",
            "score": 5, "text": "A chilling and important read."
        },
        {
            "user_email": "noah@example.com", "book_title": "Brave New World",
            "score": 4, "text": "Thought-provoking dystopian vision."
        },
        {
            "user_email": "alice@example.com", "book_title": "Cosmos",
            "score": 5, "text": "Sagan makes complex ideas accessible."
        },
        {
            "user_email": "bob@example.com", "book_title": "A Short History of Nearly Everything",
            "score": 3, "text": "Entertaining and informative."
        },
        {
            "user_email": "charlie@example.com", "book_title": "A Game of Thrones",
            "score": 5, "text": "Incredible world-building!"
        },
        {
            "user_email": "edward@example.com", "book_title": "The Hobbit",
            "score": 1, "text": "A lovely fantasy story."
        },
        {
            "user_email": "fiona@example.com", "book_title": "Murder on the Orient Express",
            "score": 5, "text": "Kept me guessing until the end."
        },
        {
            "user_email": "harry@example.com", "book_title": "Sapiens: A Brief History of Humankind",
            "score": 5, "text": "Changed my perspective on history."
        },
        {
            "user_email": "jack@example.com", "book_title": "Python Crash Course",
            "score": 2, "text": "Easy to follow and practical."
        },
        {
            "user_email": "kara@example.com", "book_title": "Pride and Prejudice",
            "score": 4, "text": "A charming classic."
        },
        {
            "user_email": "mia@example.com", "book_title": "Nineteen Eighty-Four",
            "score": 5, "text": "A chilling and important read."
        },
        {
            "user_email": "noah@example.com", "book_title": "Brave New World",
            "score": 2, "text": "Thought-provoking dystopian vision."
        },
        {
            "user_email": "alice@example.com", "book_title": "Cosmos",
            "score": 5, "text": "Sagan makes complex ideas accessible."
        },
        {
            "user_email": "bob@example.com", "book_title": "A Short History of Nearly Everything",
            "score": 4, "text": "Entertaining and informative."
        },
        {
            "user_email": "charlie@example.com", "book_title": "A Game of Thrones",
            "score": 2, "text": "Incredible world-building!"
        },
        {
            "user_email": "edward@example.com", "book_title": "The Hobbit",
            "score": 2, "text": "A lovely fantasy story."
        },
        {
            "user_email": "fiona@example.com", "book_title": "Murder on the Orient Express",
            "score": 5, "text": "Kept me guessing until the end."
        },
        {
            "user_email": "harry@example.com", "book_title": "Sapiens: A Brief History of Humankind",
            "score": 5, "text": "Changed my perspective on history."
        },
        {
            "user_email": "jack@example.com", "book_title": "Python Crash Course",
            "score": 5, "text": "Easy to follow and practical."
        },
        {
            "user_email": "kara@example.com", "book_title": "Pride and Prejudice",
            "score": 4, "text": "A charming classic."
        },
        {
            "user_email": "mia@example.com", "book_title": "Nineteen Eighty-Four",
            "score": 5, "text": "A chilling and important read."
        },
        {
            "user_email": "noah@example.com", "book_title": "Brave New World",
            "score": 3, "text": "Thought-provoking dystopian vision."
        },
        {
            "user_email": "alice@example.com", "book_title": "Cosmos",
            "score": 5, "text": "Sagan makes complex ideas accessible."
        },
        {
            "user_email": "bob@example.com", "book_title": "A Short History of Nearly Everything",
            "score": 3, "text": "Entertaining and informative."
        }
    ]

    for rating_data in ratings_data:
        user = users.get(rating_data["user_email"])
        book = books.get(rating_data["book_title"])

        if not user:
            print(f"Warning: User with email '{rating_data['user_email']}' not found for rating. Skipping.")
            continue
        if not book:
            print(f"Warning: Book with title '{rating_data['book_title']}' not found for rating. Skipping.")
            continue

        existing_rating = Rating.query.filter_by(user_id=user.id, book_id=book.id).first()
        if existing_rating:
            print(f"User '{user.full_name}' has already rated book '{book.title}'. Skipping duplicate rating seed.")
            continue
            
        rating = Rating(
            user_id=user.id,
            book_id=book.id,
            score=rating_data["score"],
            text=rating_data.get("text")
        )
        db.session.add(rating)

    # Commit is handled by seed_all()
    print("Ratings prepared for commit.")

def clear_data():
    """Clears all data from the relevant tables."""
    print("Clearing existing data...")
    # Order matters due to foreign key constraints:
    # Start with tables that are depended upon by others, or disable FK checks temporarily
    # For simplicity, we'll delete in reverse order of creation/dependency
    
    # This is a basic approach. For more complex scenarios,
    # you might need to handle circular dependencies or use raw SQL.
    # Disabling FK checks is database-specific (e.g., `SET FOREIGN_KEY_CHECKS=0;` for MySQL)

    # Order of deletion: Rating, Book (and its association table),
    # Author, Publisher, Category, User, Location, City, State, Country.
    # The book_category_table is an association table and might be cleared when books/categories are.

    try:
        # Delete records, respecting foreign key constraints by order
        Rating.query.delete()
        # For many-to-many like book_category, SQLAlchemy handles it if cascade is set,
        # or you might need to clear the association table directly if not.
        # db.session.execute(book_category_table.delete()) # If direct clearing is needed
        Book.query.delete()
        Author.query.delete()
        Publisher.query.delete()
        Category.query.delete()
        # Users might have FKs to Location, and also `referred_by` self-referential FK.
        # Need to be careful here. Setting FKs to NULL before deleting might be one strategy
        # or ensure no users refer to others before deleting.
        # For now, a simple delete; might need refinement.
        User.query.delete() # This might fail if other tables still reference User
        Location.query.delete()
        City.query.delete()
        State.query.delete()
        Country.query.delete()
        
        db.session.commit()
        print("Data cleared successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing data: {e}")


def seed_all():
    """
    Main function to orchestrate the seeding process.
    Clears existing data and then seeds new data in the correct order.
    """
    # Option: Clear data before seeding. Use with caution.
    # clear_data() 

    print("Starting database seeding process...")

    seed_geographical_data()
    db.session.commit()

    seed_users()
    db.session.commit()

    seed_locations()
    db.session.commit()

    assign_locations_to_users()
    db.session.commit()

    seed_book_metadata()
    db.session.commit()

    seed_books()
    db.session.commit()

    seed_ratings()
    db.session.commit()

    print("Database seeding process completed successfully!")

if __name__ == '__main__':
    # This part is for running the seeder directly.
    # You'll need to set up the Flask app context if you run this standalone.
    # from app import create_app # Assuming your app factory is in app.py or similar
    # app = create_app()
    # with app.app_context():
    #     seed_all()
    print("To run the seeder, you need to execute it within the Flask app context.")
    print("Example: flask seed run") # Or however you set up your CLI command