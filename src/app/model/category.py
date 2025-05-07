from ..extensions import db
from sqlalchemy import UniqueConstraint, func

class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    # One-to-many relationship
    books = db.relationship('Book', back_populates='category', cascade="all, delete")

    __table_args__ = (
        UniqueConstraint('name', name='uq_category_name'),
    )

    def to_dict(self, include_books=False):
        data = {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_books:
            data['books'] = [book.to_simple_dict() for book in self.books]
        return data