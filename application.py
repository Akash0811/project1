import os
import requests
from flask import Flask, session , redirect, render_template, request , jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import apology , login_required , lookup
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def index():
    return redirect("/search")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Check for password mismatch
        elif not request.form.get("confirmation") :
            return apology("must confirm password", 400)

        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords mismatched", 400)

        # Query database for username if it exists or insert it
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        db.commit()

        hash = generate_password_hash( request.form.get("password") )

        # If not insert into table
        if not rows:
            db.execute("INSERT INTO users( username , password ) VALUES ( :username , :hash )",
                          {"username": request.form.get("username") , "hash": hash})

            db.commit()

            rows1 = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

            db.commit()

            # Remember which user has logged in
            session["user_id"] = rows1["user_id"]

            # Redirect user to home page
            return redirect("/")

        else :
            return apology("username already exists", 400)



    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        db.commit()

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows["password"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)

@app.route("/search" , methods=["GET", "POST"])
@login_required
def search():
    """Search for places that match query"""

    if request.method == "GET":
        return render_template("search.html")

    # Add wildcards for better search
    q = request.form.get("search") + "%"
    rows = db.execute("SELECT * FROM books WHERE isbn LIKE :q OR title LIKE :q OR author LIKE :q"
                        ,{ "q": q }).fetchall()

    db.commit()

    if not rows:
        return apology("No matches found", 400)

    return render_template("books.html" , liste = rows )

@app.route("/books/<int:book_id>")
@login_required
def book(book_id):
    """Lists details about a single book."""

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE book_id = :book_id", {"book_id": book_id}).fetchone()
    db.commit()
    if book is None:
        return apology("No book found" , 400)

    reviews = lookup(book["isbn"])
    if not reviews:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "KEY", "isbns": "9781632168146"})
        print(res)
        return (res.json())

    return render_template("book.html", book=book, reviews=reviews)

@app.route("/api/<int:isbn>")
@login_required
def api(isbn):
    """api"""

    # Get all reviews and rating.
    reviews = db.execute("SELECT books.*, AVG(reviews.rating) as avg_score , COUNT(*) as rev_count FROM books JOIN reviews ON books.book_id = reviews.book_id GROUP BY books.book_id HAVING books.isbn = :isbn",
                            {"isbn": isbn}).fetchall()

    db.commit()

    if not reviews:
        return apology(" No reviews found " , 404)

    return jsonify(reviews)

@app.route("/submission", methods=["POST"])
@login_required
def submission():
    """Book a flight."""

    # Get form information.
    rating = request.form.get("rating")
    review = request.form.get("review")

    if not rating or not review:
        return apology(" Please enter rating and/or review ", 404)
    isbn = request.form.get("isbn")

    user_id = session["user_id"]

    book = db.execute("SELECT book_id FROM books where books.isbn = :isbn",
                {"isbn": isbn})
    db.commit()

    db.execute("INSERT INTO reviews ( user_id , book_id , rating , review ) VALUES (:user_id , :book_id , :rating , :review )",
            {"user_id": user_id, "book_id": book["book_id"] , rating: rating , review: review})
    db.commit()
    return redirect("/")

# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
