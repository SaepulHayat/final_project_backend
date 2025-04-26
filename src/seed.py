from faker import Faker
from src.app.extensions import db
from src.app.model.user import User

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

if __name__ == "__main__":
    with app.app_context():
        seed_users(10)

        print("\nDatabase seeding complete.")