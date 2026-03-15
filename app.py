import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of competences"""
    user_id = session["user_id"]
    role = db.execute("SELECT role FROM users WHERE id = ?", user_id)
    
    if request.method == "POST":
        updated_status = request.form.get("status")
        competence_id = request.form.get("competenceId")


        if session["role"] == "Lab Director":
            if updated_status == "Submitted for ED's approval":
                db.execute(
                    "UPDATE competences SET status = ? WHERE id = ?", updated_status, competence_id
                )
                competencesRecords = db.execute(
                    "SELECT competences.id, username AS name, competence, done_date, final_approval_date, due_date, status FROM competences INNER JOIN users ON user_id = users.id"
                )
                return render_template("indexDLS.html", competencesRecords=competencesRecords)
            else:
                done_date = "Pending"
                final_approval_date = "Pending"
                
                db.execute(
                    "UPDATE competences SET done_date = ?, final_approval_date = ?, status = ? WHERE id = ?", done_date, final_approval_date, updated_status, competence_id
                )
                competencesRecords = db.execute(
                    "SELECT competences.id, username AS name, competence, done_date, final_approval_date, due_date, status FROM competences INNER JOIN users ON user_id = users.id"
                )
                return render_template("indexDLS.html", competencesRecords=competencesRecords)
        else:
            final_approval_date = request.form.get("final_approval_date")


            # Convert final_approval_date string to a datetime object
            final_approval_date_obj = datetime.strptime(final_approval_date, "%Y-%m-%d")

            # Compute due_date from final_approval_date depending on competence type
            competence_type = db.execute("SELECT Type from competences WHERE id = ?",
                                         competence_id
                                    )
            
            # Determine new due date
            if competence_type[0]["Type"] == "Initial":
                # Add 6 months
                new_due_date_obj = final_approval_date_obj + relativedelta(months=6)
            elif competence_type[0]["Type"] == "6 month":
                # Add 6 months
                new_due_date_obj = final_approval_date_obj + relativedelta(months=6)
            else:  # Assume "Annual"
                # Add 1 year
                new_due_date_obj = final_approval_date_obj + relativedelta(years=1)

            # Compute the status based on the new_due_date
            today = datetime.today()
            two_months_before = new_due_date_obj - timedelta(days=60)

            if new_due_date_obj <= today:
                updated_status = "OVERDUE"
            elif two_months_before <= today:
                updated_status = "ALMOST DUE"
            else:
                updated_status = "UP-TO-DATE"


            db.execute("UPDATE competences SET final_approval_date = ?, due_date = ?, status = ? WHERE id = ?",
                   final_approval_date_obj.strftime("%d-%b-%Y"), new_due_date_obj.strftime("%d-%b-%Y"), updated_status, competence_id
                )
            
            competencesRecords1 = db.execute(
                "SELECT username AS name, competence, done_date, final_approval_date, due_date, status FROM competences INNER JOIN users ON user_id = users.id"
            )
            return render_template("indexRecords.html", competencesRecords=competencesRecords1)

    else:
        if role[0]["Role"] == "Lab Technologist":
            competencesTech = db.execute(
                "SELECT competences.id AS id, competence, done_date, final_approval_date, due_date, status FROM competences WHERE user_id = ?", user_id
            )
            return render_template("indexTech.html", competencesTech=competencesTech)
        elif role[0]["Role"] == "Records Officer":
            competencesRecords2 = db.execute(
                "SELECT competences.id, username AS name, competence, done_date, final_approval_date, due_date, status FROM competences INNER JOIN users ON user_id = users.id"
            )
            return render_template("indexRecords.html", competencesRecords=competencesRecords2)
        elif role[0]["Role"] == "Lab Director":
            competencesRecords3 = db.execute(
                "SELECT competences.id, username AS name, competence, done_date, final_approval_date, due_date, status FROM competences INNER JOIN users ON user_id = users.id"
            )
            return render_template("indexDLS.html", competencesRecords=competencesRecords3)
    competencesRecords4 = db.execute(
        "SELECT competences.id, username AS name, competence, done_date, final_approval_date, due_date, status FROM competences INNER JOIN users ON user_id = users.id"
    )
    return render_template("indexOther.html", competencesRecords=competencesRecords4)



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
        
        # Ensure the correct role has been input
        if request.form.get("role") != rows[0]["Role"]:
            return apology("Please select the correct role")

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Save role in session
        session["role"] = rows[0]["Role"]



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
        role = request.form.get("role")
        section = request.form.get("section")
        if not username:
            return apology("Please provide a Username!")
        elif not password:
            return apology("Please provide a Password!")
        elif not confirm:
            return apology("Please confirm Password!")
        elif not role:
            return apology("Please select a role")

        if password != confirm:
            return apology("Passwords do not match!")

        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash, role, Department) VALUES (?, ?, ?, ?)", username, hash, role, section)
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
        type = request.form.get("competence_type")
        done_date = request.form.get("done_date")
        due_date = "Pending"
        status = "Submitted for DLS approval"

        # Convert done_date string to a datetime object
        done_date_obj = datetime.strptime(done_date, "%Y-%m-%d")
       
        # Insert the new competence details into the database
        db.execute("INSERT INTO competences(user_id, competence, done_date, due_date, status, Type) VALUES (?, ?, ?, ?, ?, ?)",
                   user_id, competence, done_date_obj.strftime("%d-%b-%Y"), due_date, status, type)
        return redirect("/")
    else:
        return render_template("new.html")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update Competence"""
    user_id = session["user_id"]
    role = session["role"]
    

    if request.method == "POST":
        competence = request.form.get("competence")
        updated_done_date = request.form.get("done_date")
        type = request.form.get("competence_type")
        final_approval_date = "Pending"
        updated_status = "Submitted for DLS approval"


        # Update the competence in the database
        db.execute("UPDATE competences SET done_date = ?, final_approval_date = ?, status = ?, Type = ? WHERE user_id = ? AND competence = ?",
                   updated_done_date, final_approval_date, updated_status, type, user_id, competence)
        return redirect("/")
    else:
        # Store the contents of the competences table in a variable and pass it to render_template
        competences = db.execute("SELECT * FROM competences WHERE user_id = ?", user_id)

        return render_template("update.html", competences=competences, role=role)

if __name__ == "__main__":
    app.run(debug=True)