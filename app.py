import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from helpers import apology, login_required, calculate_due_date_and_status

# Role constants
ROLE_TECH = "Lab Technologist"
ROLE_RECORDS = "Records Officer"
ROLE_DIRECTOR = "Lab Director"

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///competence.db")


def update_overdue_statuses():
    """
    Monitor approved competences and update status based on due_date.

    Lock rule: rows in pending approval statuses are ignored by only targeting
    rows currently marked UP-TO-DATE / ALMOST DUE (and compatible variants).

    Note: due_date is stored as a string like "18-Mar-2026" (or "Pending"),
    so we parse in Python and then issue targeted SQL UPDATEs only for rows
    that actually need a status change.
    """
    today = date.today()

    monitored_statuses = ("UP-TO-DATE", "ALMOST DUE", "Up-to-Date", "Almost Due")
    rows = db.execute(
        f"SELECT id, due_date, status FROM competences WHERE status IN ({','.join(['?'] * len(monitored_statuses))})",
        *monitored_statuses,
    )

    overdue_ids = []
    almost_due_ids = []
    back_to_uptodate_ids = []

    for row in rows:
        due_date_str = row.get("due_date")
        if not due_date_str or due_date_str == "Pending":
            continue

        try:
            due = datetime.strptime(due_date_str, "%d-%b-%Y").date()
        except (ValueError, TypeError):
            continue

        days_until_due = (due - today).days

        if days_until_due <= 0:
            if row["status"] != "OVERDUE":
                overdue_ids.append(row["id"])
        elif days_until_due <= 30:
            if row["status"] != "ALMOST DUE":
                almost_due_ids.append(row["id"])
        else:
            if row["status"] in ("ALMOST DUE", "Almost Due"):
                back_to_uptodate_ids.append(row["id"])

    updatable_current_statuses = ("UP-TO-DATE", "ALMOST DUE", "Up-to-Date", "Almost Due")
    updatable_placeholders = ",".join(["?"] * len(updatable_current_statuses))

    if overdue_ids:
        placeholders = ",".join(["?"] * len(overdue_ids))
        db.execute(
            f"UPDATE competences SET status = 'OVERDUE' WHERE id IN ({placeholders}) AND status IN ({updatable_placeholders})",
            *overdue_ids,
            *updatable_current_statuses,
        )

    if almost_due_ids:
        placeholders = ",".join(["?"] * len(almost_due_ids))
        db.execute(
            f"UPDATE competences SET status = 'ALMOST DUE' WHERE id IN ({placeholders}) AND status IN ({updatable_placeholders})",
            *almost_due_ids,
            *updatable_current_statuses,
        )

    if back_to_uptodate_ids:
        placeholders = ",".join(["?"] * len(back_to_uptodate_ids))
        db.execute(
            f"UPDATE competences SET status = 'UP-TO-DATE' WHERE id IN ({placeholders}) AND status IN ({updatable_placeholders})",
            *back_to_uptodate_ids,
            *updatable_current_statuses,
        )


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():
    """Redirect user to role-specific dashboard."""
    user_id = session["user_id"]

    # Keep backend monitoring
    update_overdue_statuses()

    Role = session.get("Role")
    if not Role:
        rows = db.execute("SELECT Role FROM users WHERE id = ?", user_id)
        if not rows:
            return apology("User not found", 400)
        Role = rows[0].get("Role")
        session["Role"] = Role

    if Role == ROLE_TECH:
        return redirect("/dashboard/tech")
    if Role == ROLE_RECORDS:
        return redirect("/dashboard/records")
    if Role == ROLE_DIRECTOR:
        return redirect("/dashboard/director")
    return redirect("/dashboard/other")


@app.route("/dashboard/tech", methods=["GET"])
@login_required
def dashboard_tech():
    """Dashboard for Lab Technologists: show own competences."""
    user_id = session["user_id"]
    
    # Adding SQL queries to get statistics (Individual statistics)
    stats_rows = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('UP-TO-DATE', 'Up-to-Date') THEN 1 ELSE 0 END) as compliant,
            SUM(CASE WHEN status IN ('ALMOST DUE', 'Almost Due') THEN 1 ELSE 0 END) as warning,
            SUM(CASE WHEN status = 'OVERDUE' THEN 1 ELSE 0 END) as urgent
        FROM competences 
        WHERE user_id = ?
    """, user_id)
    
    stats = stats_rows[0] if stats_rows and stats_rows[0]['total'] > 0 else {"total": 0, "compliant": 0, "warning": 0, "urgent": 0}
    
    competences_tech = db.execute(
        "SELECT competences.id AS id, competence, done_date, final_approval_date, due_date, status FROM competences WHERE user_id = ?",
        user_id,
    )
    return render_template("indexTech.html", competencesTech=competences_tech, stats=stats)


@app.route("/dashboard/records", methods=["GET", "POST"])
@login_required
def dashboard_records():
    """Dashboard for Records Officers."""
    if session.get("role") != ROLE_RECORDS:
        return redirect("/")

    if request.method == "POST":
        competence_id = request.form.get("competenceId")
        final_approval_date_str = request.form.get("final_approval_date")

        if not competence_id or not final_approval_date_str:
            return apology("Missing competence or final approval date", 400)

        competence_type_rows = db.execute(
            "SELECT Type FROM competences WHERE id = ?", competence_id
        )
        if not competence_type_rows:
            return apology("Competence not found", 400)

        competence_type = competence_type_rows[0].get("Type")

        final_approval_date_obj, new_due_date_obj, _computed_status = (
            calculate_due_date_and_status(final_approval_date_str, competence_type)
        )

        # Start as UP-TO-DATE; monitoring transitions over time.
        updated_status = "UP-TO-DATE"

        db.execute(
            "UPDATE competences SET final_approval_date = ?, due_date = ?, status = ? WHERE id = ?",
            final_approval_date_obj.strftime("%d-%b-%Y"),
            new_due_date_obj.strftime("%d-%b-%Y"),
            updated_status,
            competence_id,
        )

        return redirect("/dashboard/records")
    
    # Adding SQL queries to get statistics (Global statistics)
    stats_rows = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('UP-TO-DATE', 'Up-to-Date') THEN 1 ELSE 0 END) as compliant,
            SUM(CASE WHEN status IN ('ALMOST DUE', 'Almost Due') THEN 1 ELSE 0 END) as warning,
            SUM(CASE WHEN status = 'OVERDUE' THEN 1 ELSE 0 END) as urgent
        FROM competences
    """)
    stats = stats_rows[0] if stats_rows and stats_rows[0]['total'] > 0 else {"total": 0, "compliant": 0, "warning": 0, "urgent": 0}

    competences_records = db.execute(
        "SELECT competences.id, username AS name, users.Department AS department, competence, done_date, final_approval_date, due_date, status "
        "FROM competences INNER JOIN users ON user_id = users.id"
    )
    return render_template("indexRecords.html", competencesRecords=competences_records, stats=stats)


@app.route("/dashboard/director", methods=["GET", "POST"])
@login_required
def dashboard_director():
    """Dashboard for Lab Director."""
    if session.get("role") != ROLE_DIRECTOR:
        return redirect("/")

    if request.method == "POST":
        updated_status = request.form.get("status")
        competence_id = request.form.get("competenceId")

        if not competence_id or not updated_status:
            return apology("Missing competence or status", 400)

        if updated_status == "Submitted for ED's approval":
            db.execute(
                "UPDATE competences SET status = ? WHERE id = ?",
                updated_status,
                competence_id,
            )
        else:
            db.execute(
                "UPDATE competences SET done_date = ?, final_approval_date = ?, status = ? WHERE id = ?",
                "Pending",
                "Pending",
                updated_status,
                competence_id,
            )

        return redirect("/dashboard/director")
    
    # Adding SQL queries to get statistics (Global statistics)
    stats_rows = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('UP-TO-DATE', 'Up-to-Date') THEN 1 ELSE 0 END) as compliant,
            SUM(CASE WHEN status IN ('ALMOST DUE', 'Almost Due') THEN 1 ELSE 0 END) as warning,
            SUM(CASE WHEN status = 'OVERDUE' THEN 1 ELSE 0 END) as urgent
        FROM competences
    """)
    stats = stats_rows[0] if stats_rows and stats_rows[0]['total'] > 0 else {"total": 0, "compliant": 0, "warning": 0, "urgent": 0}

    competences_director = db.execute(
        "SELECT competences.id, username AS name, users.Department AS department, competence, done_date, final_approval_date, due_date, status "
        "FROM competences INNER JOIN users ON user_id = users.id"
    )
    return render_template("indexDLS.html", competencesRecords=competences_director, stats=stats)


@app.route("/dashboard/other", methods=["GET"])
@login_required
def dashboard_other():
    """Fallback dashboard for any other roles."""
    # Adding SQL queries to get statistics (Global statistics)
    stats_rows = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('UP-TO-DATE', 'Up-to-Date') THEN 1 ELSE 0 END) as compliant,
            SUM(CASE WHEN status IN ('ALMOST DUE', 'Almost Due') THEN 1 ELSE 0 END) as warning,
            SUM(CASE WHEN status = 'OVERDUE' THEN 1 ELSE 0 END) as urgent
        FROM competences
    """)
    stats = stats_rows[0] if stats_rows and stats_rows[0]['total'] > 0 else {"total": 0, "compliant": 0, "warning": 0, "urgent": 0}
    competences_other = db.execute(
        "SELECT competences.id, username AS name, users.Department AS department, competence, done_date, final_approval_date, due_date, status "
        "FROM competences INNER JOIN users ON user_id = users.id"
    )
    return render_template("indexOther.html", competencesRecords=competences_other, stats=stats)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        if not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if not rows or len(rows) != 1:
            return apology("invalid username and/or password", 403)

        if request.form.get("role") != rows[0].get("Role"):
            return apology("Please select the correct role")

        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        session["Role"] = rows[0].get("Role")
        session["username"] = rows[0].get("username")
        session["Department"] = rows[0].get("Department")

        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
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
        if not password:
            return apology("Please provide a Password!")
        if not confirm:
            return apology("Please confirm Password!")
        if not role:
            return apology("Please select a role")
        if password != confirm:
            return apology("Passwords do not match!")

        password_hash = generate_password_hash(password)

        try:
            db.execute(
                "INSERT INTO users (username, hash, Role, Department) VALUES (?, ?, ?, ?)",
                username,
                password_hash,
                role,
                section,
            )
            return redirect("/")
        except Exception:
            return apology("Username has already been registered!")

    return render_template("register.html")


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Add competence"""
    user_id = session["user_id"]

    if request.method == "POST":
        competence = request.form.get("competence")
        competence_type = request.form.get("competence_type")
        done_date = request.form.get("done_date")

        due_date = "Pending"
        status = "Submitted for DLS approval"

        done_date_obj = datetime.strptime(done_date, "%Y-%m-%d")

        db.execute(
            "INSERT INTO competences(user_id, competence, done_date, due_date, status, Type) VALUES (?, ?, ?, ?, ?, ?)",
            user_id,
            competence,
            done_date_obj.strftime("%d-%b-%Y"),
            due_date,
            status,
            competence_type,
        )
        return redirect("/")

    return render_template("new.html")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update competence"""
    user_id = session["user_id"]
    Role = session.get("Role")

    if request.method == "POST":
        competence = request.form.get("competence")
        updated_done_date = request.form.get("done_date")
        competence_type = request.form.get("competence_type")

        db.execute(
            "UPDATE competences SET done_date = ?, final_approval_date = ?, status = ?, Type = ? WHERE user_id = ? AND competence = ?",
            updated_done_date,
            "Pending",
            "Submitted for DLS approval",
            competence_type,
            user_id,
            competence,
        )
        return redirect("/")

    competences = db.execute("SELECT * FROM competences WHERE user_id = ?", user_id)
    return render_template("update.html", competences=competences, Role=Role)


if __name__ == "__main__":
    app.run(debug=True)
