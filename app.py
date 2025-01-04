import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

from helpers import apology, login_required

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///competence.db")


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
    """Show portfolio of competences"""
    user_id = session["user_id"]

    competences = db.execute(
        "SELECT competence, done_date, due_date, status FROM competences WHERE user_id = ?", user_id)


    return render_template("index.html", competences=competences)


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

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        if not username:
            return apology("Please provide a Username!")
        elif not password:
            return apology("Please provide a Password!")
        elif not confirm:
            return apology("Please confirm Password!")

        if password != confirm:
            return apology("Passwords do not match!")

        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
            return redirect("/")
        except:
            return apology("Username has already been registered!")
    else:
        return render_template("register.html")

@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Add competence"""
    user_id = session["user_id"]

    if request.method == "POST":
        competence = request.form.get("competence")
        done_date = request.form.get("done_date")

        # Convert done_date string to a datetime object
        done_date_obj = datetime.strptime(done_date, "%Y-%m-%d")

        # Add one year to the done_date
        try:
            due_date_obj = done_date_obj.replace(year=done_date_obj.year + 1)
        except ValueError:
            # Handle leap year cases
            due_date_obj = done_date_obj + timedelta(days=365)

        # Compute the status based on the due_date
        today = datetime.today()
        two_months_before = due_date_obj - timedelta(days=60)

        if due_date_obj <= today:
            status = "OVERDUE"
        elif two_months_before <= today:
            status = "ALMOST DUE"
        else:
            status = "UP-TO-DATE"

        # Insert the new competence into the database
        db.execute("INSERT INTO competences(user_id, competence, done_date, due_date, status) VALUES (?, ?, ?, ?, ?)",
                   user_id, competence, done_date, due_date_obj.strftime("%d-%b-%Y"), status)
        return redirect("/")
    else:
        # Dynamically update statuses for all competences before rendering the page
        competences = db.execute("SELECT * FROM competences WHERE user_id = ?", user_id)
        today = datetime.today()

        for competence in competences:
            due_date_obj = datetime.strptime(competence['due_date'], "%d-%b-%Y")
            two_months_before = due_date_obj - timedelta(days=60)

            if due_date_obj <= today:
                status = "OVERDUE"
            elif two_months_before <= today:
                status = "ALMOST DUE"
            else:
                status = "UP-TO-DATE"

            if competence['status'] != status:
                db.execute("UPDATE competences SET status = ? WHERE id = ?", status, competence['id'])

        return render_template("new.html")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update Competence"""
    user_id = session["user_id"]

    if request.method == "POST":
        competence = request.form.get("competence")
        new_done_date = request.form.get("done_date")

        # Convert done_date string to a datetime object
        new_done_date_obj = datetime.strptime(new_done_date, "%Y-%m-%d")

        # Add one year to the done_date
        try:
            new_due_date_obj = new_done_date_obj.replace(year=new_done_date_obj.year + 1)
        except ValueError:
            # Handle leap year cases
            new_due_date_obj = new_done_date_obj + timedelta(days=365)

        # Compute the status based on the new_due_date
        today = datetime.today()
        two_months_before = new_due_date_obj - timedelta(days=60)

        if new_due_date_obj <= today:
            new_status = "OVERDUE"
        elif two_months_before <= today:
            new_status = "ALMOST DUE"
        else:
            new_status = "UP-TO-DATE"

        # Update the competence in the database
        db.execute("UPDATE competences SET done_date = ?, due_date = ?, status = ? WHERE user_id = ? AND competence = ?",
                   new_done_date, new_due_date_obj.strftime("%d-%b-%Y"), new_status, user_id, competence)
        return redirect("/")
    else:
        # Dynamically update statuses for all competences before rendering the page
        competences = db.execute("SELECT * FROM competences WHERE user_id = ?", user_id)
        today = datetime.today()

        for competence in competences:
            due_date_obj = datetime.strptime(competence['due_date'], "%d-%b-%Y")
            two_months_before = due_date_obj - timedelta(days=60)

            if due_date_obj <= today:
                status = "OVERDUE"
            elif two_months_before <= today:
                status = "ALMOST DUE"
            else:
                status = "UP-TO-DATE"

            if competence['status'] != status:
                db.execute("UPDATE competences SET status = ? WHERE id = ?", status, competence['id'])

        return render_template("update.html", competences=competences)
