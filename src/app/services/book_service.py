from ..model import Book
from ..model import Category
from ..extensions import db

class BookService:

    def create_book(self, data, user_id):
        try:
            book = Book(
                title=data['title'],
                author_name=data.get('author_name'),
                publisher_name=data.get('publisher_name'),
                description=data.get('description'),
                price=data['price'],
                quantity=data.get('quantity', 0),
                discount_percent=data.get('discount_percent', 0),
                image_url_1=data.get('image_url_1'),
                image_url_2=data.get('image_url_2'),
                image_url_3=data.get('image_url_3'),
                user_id=user_id,
                user_name=data.get('user_name')
            )

            category_id = data.get('category_id')
            if category_id:
                category = Category.query.get(category_id)
                if category:
                    book.category = category

            db.session.add(book)
            db.session.commit()

            return {
                "status": "success",
                "message": "Book created successfully",
                "data": book.to_dict(),
                "status_code": 201
            }

        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": str(e),
                "status_code": 500
            }

    def get_all_books(self, args=None):
        try:
            query = Book.query
            if args:
                search = args.get("search")
                if search:
                    query = query.filter(Book.title.ilike(f"%{search}%"))
            books = query.order_by(Book.created_at.desc()).all()

            return {
                "status": "success",
                "message": f"{len(books)} book(s) retrieved successfully",  # ✅ FIX
                "data": [book.to_dict() for book in books],
                "status_code": 200
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "status_code": 500
            }


    def get_book_by_id(self, book_id):
        try:
            book = Book.query.get(book_id)
            if not book:
                return {
                    "status": "error",
                    "message": f"Book with ID {book_id} not found.",
                    "status_code": 404
                }

            return {
                "status": "success",
                "message": "Book fetched successfully",
                "data": book.to_dict(),
                "status_code": 200
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "status_code": 500
            }

    def get_books_by_user(self, user_id, args=None):
        try:
            query = Book.query.filter_by(user_id=user_id)
            if args:
                search = args.get("search")
                if search:
                    query = query.filter(Book.title.ilike(f"%{search}%"))
            books = query.order_by(Book.created_at.desc()).all()

            return {
                "status": "success",
                "data": [book.to_dict() for book in books],
                "status_code": 200
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "status_code": 500
            }

    def update_book(self, book_id, data, user_id):
        book = Book.query.filter_by(id=book_id, user_id=user_id).first()
        if not book:
            return {
                "status": "error",
                "message": "Book not found or unauthorized",
                "status_code": 404
            }

        try:
            # Update fields if present
            for field in ['title', 'author_name', 'publisher_name', 'description', 'price', 'quantity', 'discount_percent', 'image_url_1', 'image_url_2', 'image_url_3']:
                if field in data:
                    setattr(book, field, data[field])

            # Optional: update categories
            if "category_ids" in data:
                categories = Category.query.filter(Category.id.in_(data["category_ids"])).all()
                book.categories = categories

            db.session.commit()

            return {
                "status": "success",
                "message": "Book updated successfully",
                "data": book.to_dict(),
                "status_code": 200
            }

        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": str(e),
                "status_code": 500
            }

    def delete_book(self, book_id, user_id):
        book = Book.query.filter_by(id=book_id, user_id=user_id).first()
        if not book:
            return {
                "status": "error",
                "message": "Book not found or unauthorized",
                "status_code": 404
            }

        try:
            db.session.delete(book)
            db.session.commit()
            return {
                "status": "success",
                "message": "Book deleted successfully",
                "status_code": 200  # Changed from 204 to 200
            }
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": str(e),
                "status_code": 500
            }

