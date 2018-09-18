import requests
import urllib.parse

import requests
from flask import redirect, render_template, request, session
from functools import wraps

#KEY
KEY = "zOSQOHTiC6c4jodQmYVNrA"

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(isbn):
    """Look up quote for symbol."""

    # Contact API
    try:
        response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbn": isbn})
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "review_count": quote('work_ratings_count'),
            "average_score": float(quote('average_rating'))
        }
    except (KeyError, TypeError, ValueError):
        return None


