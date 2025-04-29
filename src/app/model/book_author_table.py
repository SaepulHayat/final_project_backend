from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone

book_author_table = db.Table('book_author',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)