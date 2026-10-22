# Ink & Ideas — Sample Blog Platform

A beginner-friendly blog platform built with Python Flask, SQLite, HTML, and CSS.

## Features
- Register, log in, and log out
- Secure password hashing with Werkzeug
- Browse all published posts
- Create, edit, and delete your own posts
- Add comments while logged in
- SQLite database tables for users, posts, and comments
- Basic authorization: users cannot edit or delete other users' posts
- Responsive layout

## Requirements
- Python 3.10+
- pip

## Run on Windows
Open a terminal in the `sample-blog-platform` folder and run:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Run on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

The `blog.db` database is created automatically when the app starts. Stop the server with Ctrl+C.

## Database overview
- `users`: username and password hash
- `posts`: author, title, body, creation timestamp
- `comments`: post, author, comment body, creation timestamp

## Notes
This is a learning sample, not a production-ready deployment. Before public deployment, set a strong random `SECRET_KEY` environment variable, add CSRF protection, use HTTPS, add rate limiting and moderation, and disable Flask debug mode. For simplicity, this sample uses regular form submissions while keeping the backend routes structured for future REST API conversion.
