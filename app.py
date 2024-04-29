
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from datetime import datetime, timedelta



app = Flask(__name__)


# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:April2003@127.0.0.1:3306/myproject' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)
currDate = datetime.now().date()
dDate = currDate + timedelta(days=14)





"""

Models for each Table and their attributes

"""

class Books(db.Model):
    __tablename__ = 'Books'
    BookID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(100), nullable=False)
    Author = db.Column(db.String(100), nullable=False, index=True)
    ISBN = db.Column(db.Integer, nullable=False)
    Category = db.Column(db.String(100), nullable=False, index=True)
    Status = db.Column(db.String(1), default='available')

    def __repr__(self):
        return f'<Book {self.title}>'

class Loan(db.Model):
    __tablename__ = 'Loans'
    LoanID = db.Column(db.Integer, primary_key=True)
    BookID = db.Column(db.Integer, db.ForeignKey('Books.BookID'), nullable=False)
    PatronID = db.Column(db.Integer, db.ForeignKey('Patrons.PatronID'), nullable=False)
    LoanDate = db.Column(db.Date, nullable=False)
    DueDate = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Loan {self.title}>'


class Patron(db.Model):
    __tablename__ = 'Patrons'
    PatronID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    MembershipDate = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Patron {self.title}>'


class Reservation(db.Model):
    __tablename__ = 'Reservations'
    ReservationID = db.Column(db.Integer, primary_key=True)
    BookID = db.Column(db.Integer, db.ForeignKey('Books.BookID'), nullable=False)
    PatronID = db.Column(db.Integer, db.ForeignKey('Patrons.PatronID'), nullable=False)
    ReserveDate = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<Reservation {self.title}>'












"""

Routes for different pages for each table 

"""

@app.route('/')
def home():
    return render_template('index.html');


# Routes for Patrons table

@app.route('/view_patrons')
def view_patrons():
    sql = text("SELECT * FROM Patrons")
    patrons = db.session.execute(sql).fetchall()
    return render_template('view_patrons.html', patrons=patrons)

@app.route('/add_patron', methods=['GET'])
def add_patron():
    return render_template('add_patron.html')

@app.route('/add_patron', methods=['POST'])
def insert_patron():
    name = request.form['name']
    email = request.form['email']
    new_patron = Patron(Name=name, Email=email, MembershipDate=datetime.now().date())
    try:
        db.session.add(new_patron)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}"
    return redirect(url_for('view_patrons'))  # Redirect to the patrons view or another appropriate page

@app.route('/edit_patron/<int:patron_id>', methods=['GET', 'POST'])
def edit_patron(patron_id):
    patron = Patron.query.get_or_404(patron_id)
    if request.method == 'POST':
        try:
            patron.Name = request.form['name']
            patron.Email = request.form['email']
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}"
        return redirect(url_for('view_patrons'))
    return render_template('edit_patron.html', patron=patron)





#  Routes for Books table 

@app.route('/view_books')
def view_books():
    # Code to handle viewing patrons
    #all_books = Books.query.filter_by(Status=='available').all()  # Get all books from the database
    #return render_template('books.html', books=all_books)
    return redirect(url_for('view_books_by_availability', availability='available'))


@app.route('/view_books/<availability>')
def view_books_by_availability(availability):
    if availability not in ['unavailable', 'available']:
        return "Invalid availability", 400  # Adding a simple check for valid input
    
    sql = text("SELECT * FROM Books WHERE Status = :status")
    books = db.session.execute(sql, {'status':availability}).fetchall()
    
    return render_template('books.html', books=books, availability=availability)


@app.route('/reserve_books', methods=['POST'])
def reserve_books():
    global currDate
    global dDate
    book_ids = request.form.getlist('book_id')
    try:
        for book_id in book_ids:
            book = Books.query.get(book_id)
            if book:
                new_reservation = Reservation(
                        BookID=book.BookID, 
                        PatronID=1, 
                        ReserveDate=dDate, 
                        Status='Reserved')
            # add new reservation to table
                db.session.add(new_reservation)
        db.session.commit()
    except Exeception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}"
    return redirect(url_for('view_books_by_availability', availability='unavailable'))

@app.route('/checkout_books', methods=['POST'])

def checkout_books():
    global currDate
    global dDate
    book_ids = request.form.getlist('book_id')
    try:
        for book_id in book_ids:
            book = Books.query.get(book_id)
            if book:
                book.Status = 'unavailable'
                new_loan = Loan(
                        BookID=book.BookID,
                        PatronID=1, 
                        LoanDate=currDate, 
                        DueDate=dDate, 
                        Status='Loaned')
                # add book to loan table
                db.session.add(new_loan)
        # save changes
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}"
    return redirect(url_for('view_books_by_availability', availability='available'))

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Books.query.get_or_404(book_id)
    if request.method == 'POST':
        try:
            book.Title = request.form['title']
            book.Author = request.form['author']
            book.ISBN = request.form['isbn']
            book.Category = request.form['category']
            book.Status = request.form['status']
            # Save changes
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}"
        return redirect(url_for('view_books'))
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Books.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}"
    return redirect(url_for('view_books'))


@app.route('/add_book', methods=['POST'])
def add_book():
    new_book = Books(
        Title=request.form['title'],
        Author=request.form['author'],
        ISBN=request.form['isbn'],
        Category=request.form['category'],
        Status= 'available' # Assuming a new book is available by default
    )
    if new_book.Title == 'Concurrency Sleep Test':
        time.sleep(15)
    try:
        # add new book and save changes
        db.session.add(new_book)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}"
    return redirect(url_for('view_books'))



# Routes for Loans and Reservations tables

@app.route('/view_loans')
def view_loans():
    sql = text("SELECT * FROM Loans")
    loans = db.session.execute(sql).fetchall()
    #loans = Loan.query.all()  # Fetch all patrons from the database
    return render_template('loans.html', loans=loans)

@app.route('/view_reservations')
def view_reservations():
    sql = text("SELECT * FROM Reservations")
    reservations = db.session.execute(sql).fetchall()
    #reservations = Reservation.query.all()  # Fetch all patrons from the database
    return render_template('reservations.html', reservations=reservations)

@app.route('/report_books', methods=['GET', 'POST'])
def report_books():
    if request.method == 'POST':
        # Fetch the filter values from the form
        category = request.form.get('category', None)
        author = request.form.get('author', None)

        # Build the query based on the presence of filters
        query = Books.query
        if category:
            query = query.filter(Books.Category == category)
        if author:
            query = query.filter(Books.Author == author)

        # Execute the query and fetch results

        query = query.outerjoin(Loan, Loan.BookID == Books.BookID) \
            .outerjoin(Patron, Loan.PatronID == Patron.PatronID) \
            .add_columns(
                Books.BookID, Books.Title, Books.Author, Books.ISBN, Books.Category, Books.Status,
                Patron.Name.label('PatronName')
            )

            #bookC = Books.query.all()
        category_count = db.session.query(
                    Books.Category, func.count(Books.BookID).label('count')
        ).group_by(Books.Category).all()

        author_count = db.session.query(
                Books.Author, func.count(Books.BookID).label('author')
                ).group_by(Books.Author).all()


        # Execute the query and fetch results
        books = query.all()
        return render_template('books_report.html', books=books, category_count=category_count, author_count=author_count)

    # GET request: prepare data for dropdowns
    categories = db.session.query(Books.Category.distinct()).all()
    authors = db.session.query(Books.Author.distinct()).all()
    return render_template('report_books.html', categories=categories, authors=authors)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
