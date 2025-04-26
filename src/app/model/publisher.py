from ..extensions import db

class Publisher(db.Model):
    """Model for the Publishers table."""
    __tablename__ = "publishers"

    publisher_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publisher_name = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f"Publisher(id={self.publisher_id}, name='{self.publisher_name}')"