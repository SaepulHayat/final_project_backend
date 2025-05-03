from faker import Faker  
from datetime import datetime  
from src.app.extensions import db  
from src.app.model.user import User
from src.app.model.voucher import Voucher

from src.app import create_app  
import random  

# Inisialisasi aplikasi Flask dan Faker  
app = create_app()  
fake = Faker()  

def seed_users(n=10):  
    with app.app_context():  
        # Simpan referrer untuk digunakan sebagai referred_by  
        referrers = []  

        # Buat beberapa user referrer terlebih dahulu  
        for _ in range(max(3, n//3)):  
            referrer = User(  
                email=fake.unique.email(),  
                full_name=fake.name(),  
                password="user123",  
                referral_code=fake.bothify(text='??????'),  
                role=fake.random_element(elements=('seller', 'customer')),  
                created_at=datetime.utcnow(),  
                updated_at=datetime.utcnow()  
            )  
            referrers.append(referrer)  
            db.session.add(referrer)  

        # Commit referrers terlebih dahulu  
        db.session.commit()  

        # Buat user tambahan dengan referral  
        for _ in range(n):  
            # Secara acak pilih apakah user ini memiliki referrer  
            referred_by_user = random.choice(referrers) if referrers and random.random() < 0.5 else None  

            user = User(  
                email=fake.unique.email(),  
                full_name=fake.name(),  
                password="user123",  
                referral_code=fake.bothify(text='??????'),  
                referred_by=referred_by_user.id if referred_by_user else None,  
                role=fake.random_element(elements=('seller', 'customer')),  
                created_at=datetime.utcnow(),  
                updated_at=datetime.utcnow()  
            )  
            db.session.add(user)  

        try:  
            db.session.commit()  
            print(f"{n} users have been added to the database.")  
        except Exception as e:  
            db.session.rollback()  
            print(f"Error adding users: {e}")  

def seed_vouchers(n=5):
    with app.app_context():
        for _ in range(n):
            voucher = Voucher(
                code=Voucher._generate_voucher_code(),
                name=fake.word(),
                description=fake.sentence(),
                type=VoucherType.PERCENTAGE,
                value=Decimal('10.00'),
                min_transaction=Decimal('100.00'),
                expired_date=datetime.utcnow() + timedelta(days=30),
                usage_limit=10,
                usage_count=0,
                is_active=True
            )
            db.session.add(voucher)
        try:
            db.session.commit()
            print(f"{n} vouchers have been added to the database.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding vouchers: {e}")


def clear_users():  
    """Menghapus semua data dari tabel users."""  
    with app.app_context():  
        try:  
            User.query.delete()  
            db.session.commit()  
            print("All users have been deleted.")  
        except Exception as e:  
            db.session.rollback()  
            print(f"Error clearing users: {e}")  

def seed_data():  
    """Fungsi untuk melakukan seeding data"""  
    with app.app_context():  
        # Clear existing data  
        clear_users()  
        
        # Seed users  
        seed_users(10)  

def print_users():  
    """Menampilkan semua users untuk debugging"""  
    with app.app_context():  
        users = User.query.all()  
        print("\n=== Current Users ===")  
        for user in users:  
            referrer_info = user.referrer.email if user.referrer else "No Referrer"  
            print(f"ID: {user.id}, Name: {user.full_name}, Email: {user.email}, Referrer: {referrer_info}")  

if __name__ == "__main__":  
    # Pilih salah satu:  
    seed_vouchers(5)
    # Seed users baru  
    seed_users(10)  
    
    # Seed dengan clear data sebelumnya  
    # seed_data()  
    
    # Tampilkan users  
    print_users()