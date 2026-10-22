from functools import wraps
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
DB_PATH = os.path.join(os.path.dirname(__file__), "blog.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    with get_db() as db:
        posts = db.execute("""
            SELECT posts.*, users.username,
                   (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) AS comment_count
            FROM posts JOIN users ON users.id = posts.user_id
            ORDER BY posts.created_at DESC
        """).fetchall()
    return render_template("index.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 6:
            flash("Username must be at least 3 characters and password at least 6.", "error")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                           (username, generate_password_hash(password)))
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username is already taken.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You are logged out.", "success")
    return redirect(url_for("index"))


@app.route("/posts/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("Title and content are required.", "error")
        else:
            with get_db() as db:
                db.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                           (session["user_id"], title, content))
            flash("Post published!", "success")
            return redirect(url_for("index"))
    return render_template("post_form.html", post=None, page_title="Write a post")


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    with get_db() as db:
        post = db.execute("""
            SELECT posts.*, users.username FROM posts
            JOIN users ON users.id = posts.user_id WHERE posts.id = ?
        """, (post_id,)).fetchone()
        if post is None:
            abort(404)
        comments = db.execute("""
            SELECT comments.*, users.username FROM comments
            JOIN users ON users.id = comments.user_id
            WHERE comments.post_id = ? ORDER BY comments.created_at ASC
        """, (post_id,)).fetchall()
    return render_template("post_detail.html", post=post, comments=comments)


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    with get_db() as db:
        post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            abort(404)
        if post["user_id"] != session["user_id"]:
            abort(403)
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            if not title or not content:
                flash("Title and content are required.", "error")
            else:
                db.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?",
                           (title, content, post_id))
                flash("Post updated.", "success")
                return redirect(url_for("post_detail", post_id=post_id))
    return render_template("post_form.html", post=post, page_title="Edit post")


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    with get_db() as db:
        post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            abort(404)
        if post["user_id"] != session["user_id"]:
            abort(403)
        db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    flash("Post deleted.", "success")
    return redirect(url_for("index"))


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    content = request.form.get("content", "").strip()
    with get_db() as db:
        exists = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not exists:
            abort(404)
        if content:
            db.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                       (post_id, session["user_id"], content))
    if not content:
        flash("Comment cannot be empty.", "error")
    return redirect(url_for("post_detail", post_id=post_id))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
