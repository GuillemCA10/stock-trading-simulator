import os
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize database if it doesn't exist
if not os.path.exists("app.db"):
    with sqlite3.connect("app.db") as conn:
        with open("schema.sql") as f:
            conn.executescript(f.read())

# Configure database
db = SQL("sqlite:///app.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Display HTML table

    # Fetch user holdings of each stock
    rows = db.execute(
        """
        SELECT symbol, SUM(shares) AS total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING total_shares > 0
        """,
        session["user_id"]
    )

    # Get current price for each stock and calculate the total value
    stocks = []
    portfolio_value = 0

    for row in rows:
        symbol = row["symbol"]
        shares = row["total_shares"]

        quote = lookup(symbol)
        price = quote["price"]

        total = shares * price

        stocks.append({
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": total
        })

        portfolio_value += total
    # Get user's cash balance
    rows = db.execute(
        "SELECT cash FROM users WHERE id = ?",
        session["user_id"]
    )
    cash = rows[0]["cash"]

    # Calculate grand total
    grand_total = cash + portfolio_value

    # Display user's portfolio
    return render_template(
        "index.html",
        stocks=stocks,
        cash=cash,
        portfolio_value=portfolio_value,
        grand_total=grand_total
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not all([symbol, shares]):
            return apology("Please fill in all fields")

        quote = lookup(symbol)

        if not quote:
            return apology("Invalid stock symbol")

        try:
            shares = int(shares)
        except ValueError:
            return apology("Shares must be a number greater than 0. No decimals.")

        if shares < 1:
            return apology("Shares must be a number greater than 0. No decimals.")

        # Access user's cash from database
        rows = db.execute(
            "SELECT cash FROM users WHERE id = ?",
            session["user_id"]
        )

        user_cash = rows[0]["cash"]

        transaction_cost = shares * quote["price"]

        if transaction_cost > user_cash:
            return apology("Insufficient funds")

        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            session["user_id"],
            quote["symbol"],
            shares,
            quote["price"]
        )

        db.execute(
            "UPDATE users SET cash = cash - ? WHERE id = ?",
            transaction_cost,
            session["user_id"]
        )

        return redirect("/")

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    rows = db.execute(
        """
        SELECT symbol, shares, price, timestamp
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp
        """,
        session["user_id"]
    )

    return render_template("history.html", transactions=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # If method = GET -> Render quote.html w/ a text field that allows the user to input a stock's symbol
    # If method = POST -> Render quoted.html

    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("You must provide a symbol")

        quote = lookup(symbol)

        if not quote:
            return apology("Invalid symbol")

        return render_template(
            "quoted.html",
            name=quote["name"],
            symbol=quote["symbol"],
            price=quote["price"]
        )

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # handle form submission
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not all([username, password, confirmation]):
            return apology("Please fill in all fields")

        if password != confirmation:
            return apology("Passwords do not match")

        password_hash = generate_password_hash(password, method='scrypt', salt_length=16)

        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username, password_hash
            )
        except ValueError:
            return apology("Username is already taken")
        rows = db.execute(
            "SELECT id FROM users WHERE username = ?",
            username
        )
        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        # show registration form
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not all([symbol, shares]):
            return apology("Please fill in all fields")

        # Validate input
        try:
            shares = int(shares)
        except ValueError:
            return apology("Shares must be a positive integer")

        if shares < 1:
            return apology("Shares must be a positive integer")

        # Check user's share ownership
        rows = db.execute(
            """
            SELECT SUM(shares) AS total_shares
            FROM transactions
            WHERE user_id = ? AND symbol = ?
            """,
            session["user_id"],
            symbol
        )

        owned_shares = rows[0]["total_shares"] or 0

        if shares > owned_shares:
            return apology("You don't own enough shares")

        # Get current stock price
        quote = lookup(symbol)
        price = quote["price"]

        proceeds = shares * price

        # Record the transaction (negative shares)
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            session["user_id"],
            symbol,
            -shares,
            price
        )

        # Update user's cash
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            proceeds,
            session["user_id"]
        )

        return redirect("/")

    else:
        rows = db.execute(
            """
            SELECT symbol
            FROM transactions
            WHERE user_id = ?
            GROUP BY symbol
            HAVING SUM(shares) > 0
            """,
            session["user_id"]
        )

    stocks = rows
    return render_template("sell.html", stocks=stocks)


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Add cash to user's account"""

    if request.method == "POST":
        amount = request.form.get("amount")

        if not amount:
            return apology("Please provide an amount")

        try:
            amount = float(amount)
        except ValueError:
            return apology("Amount must be a number")

        if amount <= 0:
            return apology("Amount must be positive")

        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            amount,
            session["user_id"]
        )

        return redirect("/")

    return render_template("add_cash.html")
