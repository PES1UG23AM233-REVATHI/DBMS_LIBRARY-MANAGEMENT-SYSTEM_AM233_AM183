from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import random, string
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import get_conn, query

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- LOGIN REQUIRED ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ---------- ADMIN REQUIRED ----------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "role" not in session or session["role"] != "librarian":
            flash("Access denied. Librarians only.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

# ---------- Template Filter ----------
@app.template_filter('datetime_local')
def datetime_local(dt):
    return dt.strftime('%Y-%m-%dT%H:%M')


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Try librarian login
        lib = query("SELECT * FROM librarians WHERE username=%s", (username,), fetch=True)
        if lib:
            lib = lib[0]
            if lib["password"] == password or check_password_hash(lib["password"], password):
                session["user_id"] = lib["id"]
                session["username"] = lib["username"]
                session["role"] = "librarian"
                flash("Logged in as Librarian!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid password!", "danger")
                return render_template("login.html")

        # Try member login
        member = query("SELECT * FROM members WHERE username=%s", (username,), fetch=True)
        if member:
            member = member[0]
            if member["password"] == password or check_password_hash(member["password"], password):
                session["user_id"] = member["id"]
                session["username"] = member["username"]
                session["role"] = "member"
                flash("Logged in as Member!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid password!", "danger")
                return render_template("login.html")

        flash("User not found!", "danger")
        return render_template("login.html")

    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# ---------- HOME ----------
@app.route("/")
@login_required
def index():
    total_books = query("SELECT COUNT(*) as cnt FROM books", fetch=True)
    total_members = query("SELECT COUNT(*) as cnt FROM members", fetch=True)
    active_issues = query("""
        SELECT COUNT(*) AS cnt
        FROM issues i
        LEFT JOIN returns r ON i.id = r.issue_id
        WHERE r.id IS NULL
    """, fetch=True)

    stats = {
        'Books': total_books[0]['cnt'] if total_books else 0,
        'Members': total_members[0]['cnt'] if total_members else 0,
        'Active Issues': active_issues[0]['cnt'] if active_issues else 0,
    }
    return render_template("index.html", stats=stats)

# ---------- BOOKS ----------
@app.route("/books")
@login_required
def books():
    sql = """
        SELECT b.*, 
               c.name AS category_name, 
               p.name AS publisher_name
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.id
        LEFT JOIN publishers p ON b.publisher_id = p.id
        ORDER BY b.title
    """
    rows = query(sql, fetch=True)
    return render_template("books.html", books=rows)

@app.route("/add_book", methods=["GET", "POST"])
@admin_required
def add_book():
    if request.method == "POST":
        book_id = ''.join(random.choices(string.digits, k=5))
        title = request.form["title"]
        author = request.form.get("author")
        category_id = request.form.get("category_id")
        publisher_id = request.form.get("publisher_id")
        publication_year = request.form.get("publication_year")
        quantity = int(request.form.get("quantity", 1))
        isbn = request.form.get("isbn")
        if not isbn or isbn.strip() == "":
            isbn = ''.join(random.choices(string.digits, k=13))

        query("""
            INSERT INTO books 
            (id, title, author, isbn, category_id, publisher_id, publication_year, quantity, available_copies)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (book_id, title, author, isbn, category_id, publisher_id, publication_year, quantity, quantity))

        flash(f"Book added successfully! ISBN: {isbn}", "success")
        return redirect(url_for("books"))

    categories = query("SELECT id, name FROM categories", fetch=True)
    publishers = query("SELECT id, name FROM publishers", fetch=True)
    return render_template("add_book.html", categories=categories, publishers=publishers)

@app.route("/delete_book/<string:book_id>")
@admin_required
def delete_book(book_id):
    try:
        query("DELETE FROM books WHERE id = %s", (book_id,))
        flash("Book deleted successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Error deleting book: {err}", "danger")
    return redirect(url_for("books"))

# ---------- MEMBERS ----------
@app.route("/members")
@login_required
def members():
    rows = query("""
        SELECT m.*, r.name AS referred_by_name 
        FROM members m 
        LEFT JOIN members r ON m.referred_by = r.id
    """, fetch=True)
    return render_template("member.html", members=rows)

@app.route("/add_member", methods=["GET", "POST"])
@admin_required
def add_member():
    members = query("SELECT id, name FROM members", fetch=True)

    if request.method == "POST":
        member_id = "M" + ''.join(random.choices(string.digits, k=5))
        name = request.form["name"]
        referred_by = request.form.get("referred_by") or None
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form.get("address", "")
        membership_status = request.form.get("membership_status", "Active")

        username = email
        hashed_password = generate_password_hash("password123")

        query("""
            INSERT INTO members 
            (id, name, referred_by, email, phone, address, membership_status, username, password)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (member_id, name, referred_by, email, phone, address, membership_status, username, hashed_password))

        flash(f"Member added! Default password = password123", "success")
        return redirect(url_for("members"))

    return render_template("add_member.html", members=members)

# ---------- ISSUE BOOK ----------
@app.route("/issue_add", methods=["GET", "POST"])
@admin_required
def issue_add():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        issue_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        book_id = request.form["book_id"]
        member_id = request.form["member_id"]
        issue_date = datetime.strptime(request.form.get("issue_date"), "%Y-%m-%dT%H:%M")
        due_date = datetime.strptime(request.form.get("due_date"), "%Y-%m-%dT%H:%M")

        cursor.execute("""
            INSERT INTO issues 
            (id, book_id, member_id, librarian_id, issue_date, due_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (issue_id, book_id, member_id, session["user_id"], issue_date, due_date))

        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id=%s AND available_copies > 0",
            (book_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Book issued successfully!", "success")
        return redirect(url_for("issues"))

    books = query("SELECT id, title, available_copies FROM books", fetch=True)
    members = query("SELECT id, name FROM members", fetch=True)
    return render_template("issue_add.html", books=books, members=members)

# ---------- ISSUES LIST ----------
@app.route("/issues")
@login_required
def issues():
    sql = """
        SELECT i.id AS issue_id,
               b.id AS book_id,
               b.title AS book_title,
               m.id AS member_id,
               m.name AS member_name,
               i.issue_date,
               i.due_date,
               i.penalty_amount,
               IF(r.id IS NULL, 0, 1) AS returned,
               r.return_date
        FROM issues i
        LEFT JOIN books b ON i.book_id = b.id
        LEFT JOIN members m ON i.member_id = m.id
        LEFT JOIN returns r ON i.id = r.issue_id
        ORDER BY i.issue_date DESC
    """
    rows = query(sql, fetch=True)
    return render_template("issues.html", issues=rows)

# ---------- RETURNS ----------
@app.route("/return_add/<string:issue_id>")
@admin_required
def return_add(issue_id):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, book_id, due_date FROM issues WHERE id=%s", (issue_id,))
    issue = cursor.fetchone()

    if issue:
        try:
            return_date = datetime.now()
            due_date = issue["due_date"]
            if not isinstance(due_date, datetime):
                due_date = datetime.combine(due_date, datetime.min.time())

            late_minutes = (return_date - due_date).total_seconds() / 60
            penalty = int(late_minutes) if late_minutes > 0 else 0

            cursor.execute(
                "INSERT INTO returns (issue_id, return_date, condition_notes) VALUES (%s,%s,%s)",
                (issue_id, return_date, "Book returned in good condition")
            )
            cursor.execute(
                "UPDATE issues SET penalty_amount=%s WHERE id=%s",
                (penalty, issue_id)
            )
            cursor.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE id=%s",
                (issue['book_id'],)
            )
            conn.commit()
            flash(f"Returned with penalty ₹{penalty}", "success")
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f"Error: {err}", "danger")
    else:
        flash("Issue not found!", "danger")

    cursor.close()
    conn.close()
    return redirect(url_for("issues"))

# ---------- RETURNS LIST ----------
@app.route("/returns")
@login_required
def returns():
    sql = """
        SELECT r.id AS return_id,
               i.id AS issue_id,
               b.id AS book_id,
               b.title AS book_title,
               m.id AS member_id,
               m.name AS member_name,
               i.issue_date,
               r.return_date,
               i.penalty_amount,
               r.condition_notes
        FROM returns r
        LEFT JOIN issues i ON r.issue_id = i.id
        LEFT JOIN books b ON i.book_id = b.id
        LEFT JOIN members m ON i.member_id = m.id
        ORDER BY r.return_date DESC
    """
    rows = query(sql, fetch=True)
    return render_template("returns.html", returns=rows)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
