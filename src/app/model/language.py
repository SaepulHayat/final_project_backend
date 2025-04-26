from ..extensions import db

class Language(db.Model):
    """Model for the Language table."""
    __tablename__ = "languages"

    language_code = db.Column(db.String(10), primary_key=True)
    language_name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"Language({self.language_code}, {self.language_name})"