from datetime import datetime, timedelta

import requests
from dateutil.relativedelta import relativedelta
from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def calculate_due_date_and_status(final_approval_date_str, competence_type, today=None):
    """
    Given a final approval date (YYYY-MM-DD string) and competence type,
    return (final_approval_date_obj, new_due_date_obj, status).
    """
    if today is None:
        today = datetime.today()

    # Parse the incoming date string
    final_approval_date_obj = datetime.strptime(final_approval_date_str, "%Y-%m-%d")

    # Determine new due date based on competence type
    if competence_type == "Initial":
        new_due_date_obj = final_approval_date_obj + relativedelta(months=6)
    elif competence_type == "6 month":
        new_due_date_obj = final_approval_date_obj + relativedelta(months=6)
    else:  # Assume "Annual"
        new_due_date_obj = final_approval_date_obj + relativedelta(years=1)

    # Compute the status based on the new due date
    two_months_before = new_due_date_obj - timedelta(days=60)

    if new_due_date_obj <= today:
        status = "OVERDUE"
    elif two_months_before <= today:
        status = "ALMOST DUE"
    else:
        status = "UP-TO-DATE"

    return final_approval_date_obj, new_due_date_obj, status

