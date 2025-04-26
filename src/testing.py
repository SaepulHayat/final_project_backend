# Ensure Flask and Faker are installed:
# pip install Flask Faker

from flask import Flask, jsonify
from faker import Faker  # Library to generate fake data
import random
from datetime import datetime

# --- Provided Publisher Model (for reference) ---
# (We won't interact with the database directly in this example,
# but we'll structure our fake data based on this model)
'''
from ..extensions import db # Assuming db is SQLAlchemy instance

class Publisher(db.Model):
    """Model for the Publisher table."""
    __tablename__ = "publishers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    contact_email = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    books = db.relationship("Book", back_populates="publisher")

    def __repr__(self):
        return f"Publisher({self.id}, {self.name})"
'''
# --- Flask Application ---

app = Flask(__name__)
fake = Faker() # Initialize Faker

def create_random_publisher(publisher_id):
    """Generates a dictionary representing a random publisher."""
    # Decide if nullable fields should be None sometimes
    has_email = random.choice([True, False])
    has_website = random.choice([True, True, False]) # Make website slightly more common

    return {
        "id": publisher_id,
        "name": fake.company() + (" Press" if random.choice([True, False]) else " Books"), # Make it sound like a publisher
        "contact_email": fake.email() if has_email else None,
        "website": fake.url() if has_website else None,
        # Generate ISO 8601 formatted date strings for JSON compatibility
        "created_at": fake.past_datetime(start_date="-2y", tzinfo=None).isoformat() + "Z", # Z indicates UTC
        "updated_at": fake.past_datetime(start_date="-1y", tzinfo=None).isoformat() + "Z",
        # We won't include the 'books' relationship in this simple GET list
    }

@app.route('/publishers', methods=['GET'])
def get_publishers():
    """
    GET route to retrieve a list of random publishers.
    """
    # Generate a list of 5 random publishers for this example
    publishers_list = [create_random_publisher(i + 1) for i in range(5)]

    # Return the list as a JSON response
    return jsonify(publishers_list)

# --- Run the application ---
if __name__ == '__main__':
    # debug=True allows auto-reloading on code changes and provides detailed error pages
    # Use host='0.0.0.0' to make it accessible on your network
    app.run(host='0.0.0.0', port=5000, debug=True)