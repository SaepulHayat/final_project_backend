from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone

book_category_table = db.Table('book_category',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)