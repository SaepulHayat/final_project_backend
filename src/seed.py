from faker import Faker
from src.app.extensions import db
from src.app.model.user import User
from src.app.model.author import Author
from src.app.model.book_author import BookAuthor
from src.app.model.book_genre import BookGenre
from src.app.model.book import Book
from src.app.model.genre import Genre
from src.app.model.product_listing import ProductListing
from src.app.model.publisher import Publisher
from src.app.model.review import Review
from src.app.model.store import Store
from src.app import create_app
import random

# Initialize Flask app and Faker
app = create_app()
fake = Faker()

def seed_users(n=10):
    """Function to add dummy data to the users table."""
    with app.app_context():
        for _ in range(n):
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                password_hash=fake.password(length=12),
                balance=fake.pydecimal(left_digits=5, right_digits=2, positive=True),
                referral_code=fake.bothify(text='??????'),
                referred_by=None,
                role=fake.random_element(elements=('admin', 'user')),
            )
            db.session.add(user)
        db.session.commit()
        print(f"{n} users have been added to the database.")

def clear_users():
    """Deletes all data from the users table."""
    with app.app_context():
        User.query.delete()
        db.session.commit()
        print("All users have been deleted.")

def seed_authors(n=10):
    """Function to add dummy data to the authors table."""
    with app.app_context():
        for _ in range(n):
            author = Author(
                name=fake.name(),
                bio=fake.text(max_nb_chars=200)
            )
            db.session.add(author)
        db.session.commit()
        print(f"{n} authors have been added to the database.")

def clear_authors():
    """Deletes all data from the authors table."""
    with app.app_context():
        Author.query.delete()
        db.session.commit()
        print("All authors have been deleted.")

def seed_genres(n=10):
    """Function to add dummy data to the genres table."""
    with app.app_context():
        for _ in range(n):
            genre = Genre(
                name=fake.word()
            )
            db.session.add(genre)
        db.session.commit()
        print(f"{n} genres have been added to the database.")

def clear_genres():
    """Deletes all data from the genres table."""
    with app.app_context():
        Genre.query.delete()
        db.session.commit()
        print("All genres have been deleted.")

def seed_publishers(n=10):
    """Function to add dummy data to the publishers table."""
    with app.app_context():
        for _ in range(n):
            publisher = Publisher(
                name=fake.company()
            )
            db.session.add(publisher)
        db.session.commit()
        print(f"{n} publishers have been added to the database.")

def clear_publishers():
    """Deletes all data from the publishers table."""
    with app.app_context():
        Publisher.query.delete()
        db.session.commit()
        print("All publishers have been deleted.")

def seed_stores(n=5):
    """Function to add dummy data to the stores table."""
    with app.app_context():
        for _ in range(n):
            store = Store(
                name=fake.company(),
                location=fake.address()
            )
            db.session.add(store)
        db.session.commit()
        print(f"{n} stores have been added to the database.")

def clear_stores():
    """Function to add dummy data to the stores table."""
    with app.app_context():
        Store.query.delete()
        db.session.commit()
        print("All stores have been deleted.")

def seed_books(n=20):
    """Function to add dummy data to the books table."""
    with app.app_context():
        publishers = Publisher.query.all()
        if not publishers:
            print("No publishers found. Please seed publishers first.")
            return

        for _ in range(n):
            book = Book(
                isbn=fake.isbn13(),
                title=fake.sentence(nb_words=6, variable_nb_words=True),
                description=fake.text(max_nb_chars=200),
                publisher_id=random.choice(publishers).publisher_id,
                publication_date=fake.date_object(),
                language=fake.language_name(),
                num_pages=fake.random_int(min=50, max=1000),
                format=fake.random_element(elements=('Hardcover', 'Paperback', 'Ebook')),
                cover_image_url=fake.image_url()
            )
            db.session.add(book)
        db.session.commit()
        print(f"{n} books have been added to the database.")

def clear_books():
    """Deletes all data from the books table."""
    with app.app_context():
        Book.query.delete()
        db.session.commit()
        print("All books have been deleted.")

def seed_book_authors():
    """Function to add dummy data to the book_author table."""
    with app.app_context():
        books = Book.query.all()
        authors = Author.query.all()
        if not books or not authors:
            print("No books or authors found. Please seed them first.")
            return

        for book in books:
            # Assign 1 to 3 authors per book
            num_authors = random.randint(1, 3)
            selected_authors = random.sample(authors, min(num_authors, len(authors)))
            for author in selected_authors:
                book_author = BookAuthor(
                    book_id=book.book_id,
                    author_id=author.author_id
                )
                db.session.add(book_author)
        db.session.commit()
        print("Book-author relationships have been added to the database.")

def clear_book_authors():
    """Deletes all data from the book_author table."""
    with app.app_context():
        BookAuthor.query.delete()
        db.session.commit()
        print("All book-author relationships have been deleted.")

def seed_book_genres():
    """Function to add dummy data to the book_genre table."""
    with app.app_context():
        books = Book.query.all()
        genres = Genre.query.all()
        if not books or not genres:
            print("No books or genres found. Please seed them first.")
            return

        for book in books:
            # Assign 1 to 3 genres per book
            num_genres = random.randint(1, 3)
            selected_genres = random.sample(genres, min(num_genres, len(genres)))
            for genre in selected_genres:
                book_genre = BookGenre(
                    book_id=book.book_id,
                    genre_id=genre.genre_id
                )
                db.session.add(book_genre)
        db.session.commit()
        print("Book-genre relationships have been added to the database.")

def clear_book_genres():
    """Deletes all data from the book_genre table."""
    with app.app_context():
        BookGenre.query.delete()
        db.session.commit()
        print("All book-genre relationships have been deleted.")

def seed_product_listings(n=30):
    """Function to add dummy data to the product_listings table."""
    with app.app_context():
        books = Book.query.all()
        stores = Store.query.all()
        if not books or not stores:
            print("No books or stores found. Please seed them first.")
            return

        for _ in range(n):
            listing = ProductListing(
                book_id=random.choice(books).book_id,
                store_id=random.choice(stores).store_id,
                price=fake.pydecimal(left_digits=3, right_digits=2, positive=True),
                stock=fake.random_int(min=0, max=100),
                condition=fake.random_element(elements=('New', 'Used - Like New', 'Used - Good', 'Used - Fair'))
            )
            db.session.add(listing)
        db.session.commit()
        print(f"{n} product listings have been added to the database.")

def clear_product_listings():
    """Deletes all data from the product_listings table."""
    with app.app_context():
        ProductListing.query.delete()
        db.session.commit()
        print("All product listings have been deleted.")

def seed_reviews(n=50):
    """Function to add dummy data to the reviews table."""
    with app.app_context():
        books = Book.query.all()
        users = User.query.all()
        if not books or not users:
            print("No books or users found. Please seed them first.")
            return

        for _ in range(n):
            review = Review(
                book_id=random.choice(books).book_id,
                user_id=random.choice(users).user_id,
                rating=fake.random_int(min=1, max=5),
                comment=fake.paragraph(nb_sentences=3),
                review_date=fake.date_time_this_year()
            )
            db.session.add(review)
        db.session.commit()
        print(f"{n} reviews have been added to the database.")

def clear_reviews():
    """Deletes all data from the reviews table."""
    with app.app_context():
        Review.query.delete()
        db.session.commit()
        print("All reviews have been deleted.")

if __name__ == "__main__":
    with app.app_context():
        # Clear existing data (optional, uncomment to clear)
        # clear_reviews()
        # clear_product_listings()
        # clear_book_authors()
        # clear_book_genres()
        # clear_books()
        # clear_authors()
        # clear_genres()
        # clear_publishers()
        # clear_stores()
        # clear_users()

        # Seed data
        seed_users(10)
        seed_authors(10)
        seed_genres(10)
        seed_publishers(10)
        seed_stores(5)
        seed_books(20)
        seed_book_authors() # Seeds based on existing books and authors
        seed_book_genres() # Seeds based on existing books and genres
        seed_product_listings(30) # Seeds based on existing books and stores
        seed_reviews(50) # Seeds based on existing books and users

        print("\nDatabase seeding complete.")