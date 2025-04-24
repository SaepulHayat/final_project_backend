from faker import Faker
from src.app.extensions import db
from src.app.model.user import User
from src.app import create_app

# Inisialisasi aplikasi Flask dan Faker
app = create_app()
fake = Faker()

def seed_users(n=10):
    """Fungsi untuk menambahkan data dummy ke tabel users."""
    with app.app_context():
        for _ in range(n):
            user = User(
                username=fake.user_name(),
                email=fake.email(),
                password_hash=fake.password(length=12),
                balance=fake.pydecimal(left_digits=5, right_digits=2, positive=True),
                referral_code=fake.bothify(text='??????'),
                referred_by=None,  # Bisa diatur sesuai kebutuhan
                role=fake.random_element(elements=('admin', 'user')),
            )
            db.session.add(user)
        db.session.commit()
        print(f"{n} users have been added to the database.")
        
def clear_users():
    """Menghapus semua data dari tabel users."""
    with app.app_context():
        User.query.delete()
        db.session.commit()
        print("All users have been deleted.")

if __name__ == "__main__":
    seed_users(5)
    # clear_users()
    