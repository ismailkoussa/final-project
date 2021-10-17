import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from help import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///items.db")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#.....................................
@app.route("/")
@login_required
def index():
    item = db.execute(
            "select * from item ")

    return render_template("index.html",item=item)

#........................................................
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure the username was submitted
        if not username:
            message = "must provide username"
            return render_template("apology.html",message=message)
        # Ensure the username doesn't exists
        elif len(rows) != 0:
            message = "username already exists"
            return render_template("apology.html",message=message)

        # Ensure password was submitted
        elif not password:
            message = "must provide password"
            return render_template("apology.html",message=message)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            message = "must provide a confirmation password"
            return render_template("apology.html",message=message)
        # Ensure passwords match
        elif not password == confirmation:
            message = "Incorrect confirmation"
            return render_template("apology.html",message=message)
        else:
            # Insert the new user
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?) ", username, password,
            )
            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

#...................................

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            message = "must provide username!!"
            return render_template("apology.html",message=message)

        # Ensure password was submitted
        elif not request.form.get("password"):
            message = "must provide password"
            return render_template("apology.html",message=message)
        # Ensure username exists and password is correct
        password = request.form.get("password")
        username = request.form.get("username")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows)!=1:
            message = "username unexists"
            return render_template("apology.html",message=message)
        elif rows[0]["password"] != password:
            message = "Incorrect password"
            return render_template("apology.html",message=message)

     # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

#...........................................................

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
#..........................................

@app.route("/buy", methods=["GET", "POST"])

def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not shares:
            message = "must provide shares"
            return render_template("apology.html",message=message)
        price = db.execute(
            "SELECT price FROM item WHERE name = ? ", symbol)
        if len(price)==0:
            message = "No such item %s.. "%(symbol)
            return render_template("apology.html",message=message)
        price = int(price[0]["price"])

        current = db.execute(
            "SELECT cash FROM users WHERE id = ? ", session["user_id"]
        )[0]["cash"]
        shares = int(shares)
        current = int(current)
        value = int(shares) * price

        if current < value:
            message = "no enough cash"
            message = str(value)
            return render_template("apology.html",message=message)

        quantity = 0
        total = 0
        stock = db.execute("SELECT * FROM stock WHERE user_id = ? and item = ?", session["user_id"] , symbol)
        if len(stock) != 0:
           db.execute("update stock set quantity = quantity + ?, price = price + ? where user_id = ? and item = ?",
           shares, value, session["user_id"], symbol

           )
        else:
            db.execute("insert into stock (user_id, item, quantity, price) values(?,?,?,?)",
            session["user_id"],symbol,shares,value
            )
            db.execute(
             "UPDATE users SET cash = cash - ? WHERE id = ?",
             value,
             session["user_id"],
             )
        return redirect("/buy")
    else:
        return render_template("buy.html")
#....................................................................

@app.route("/bill")

def bill():
    total = 0
    stock = db.execute("SELECT * FROM stock WHERE user_id = ?", session["user_id"])
    for stockmin in stock:
        total += stockmin["price"]
    return render_template("bill.html", stock=stock,total=total)
#.........................................................................................
