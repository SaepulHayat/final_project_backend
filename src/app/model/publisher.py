from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone

class Publisher(db.Model):
    __tablename__ = 'publisher'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    books = db.relationship('Book', back_populates='publisher')

    __table_args__ = (
        UniqueConstraint('name', name='uq_publisher_name'),
    )

    def __repr__(self):
        return f'<Publisher {self.id}: {self.name}>'