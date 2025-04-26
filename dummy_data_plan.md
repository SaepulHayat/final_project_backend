# Plan for Creating Dummy Data using Faker

This document outlines the steps to create dummy data for the application's database using the Faker library in Python.

## 1. Install Faker

If you haven't already, install the Faker library using pip:

```bash
pip install Faker
```

## 2. Initialize Faker

Import and initialize the Faker generator. You can optionally specify a locale for localized data.

```python
from faker import Faker

fake = Faker()
# Or for a specific locale, e.g., British English
# fake = Faker('en_GB')
```

## 3. Generate Dummy Data

Faker provides various methods to generate different types of data. Here are some examples relevant to the application's models:

- **Users:**

  - `fake.user_name()`: Generates a username.
  - `fake.email()`: Generates an email address.
  - `fake.password(length=12)`: Generates a password.
  - `fake.pydecimal(left_digits=5, right_digits=2, positive=True)`: Generates a decimal number for balance.
  - `fake.bothify(text='??????')`: Generates a string with random characters (useful for referral codes).
  - `fake.random_element(elements=('admin', 'user'))`: Selects a random element from a list (useful for roles).

- **Books:**

  - `fake.isbn13()`: Generates an ISBN-13.
  - `fake.sentence(nb_words=6, variable_nb_words=True)`: Generates a sentence for a title.
  - `fake.text(max_nb_chars=200)`: Generates a block of text for a description.
  - `fake.date_object()`: Generates a date object for publication date.
  - `fake.language_name()`: Generates a language name.
  - `fake.random_int(min=50, max=1000)`: Generates a random integer for number of pages.
  - `fake.random_element(elements=('Hardcover', 'Paperback', 'Ebook'))`: Generates a format.
  - `fake.image_url()`: Generates a dummy image URL.

- **Authors, Genres, Publishers, Stores, Product Listings, Reviews:**
  - Faker has methods for names (`fake.name()`), company names (`fake.company()`), addresses (`fake.address()`), prices (`fake.pydecimal()`), dates (`fake.date_time_this_year()`), and text (`fake.paragraph()`, `fake.text()`) that can be used for these models.

## 4. Integrate with Database Seeding

Use the generated data to create instances of your SQLAlchemy models and add them to the database session.

Here's an example based on the `seed_users` function in `src/seed.py`:

```python
from faker import Faker
from src.app.extensions import db
from src.app.model.user import User
from src.app import create_app

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

if __name__ == "__main__":
    seed_users(5)
```

You can extend this approach to create seeding functions for other models, ensuring you handle relationships appropriately (e.g., by fetching existing publishers or authors when creating books).

This plan provides a foundation for generating diverse dummy data to populate your database for testing and development purposes.
