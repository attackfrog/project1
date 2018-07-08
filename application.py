import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
if not os.getenv("DARKSKY_KEY"):
    raise RuntimeError("DARKSKY_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    logged_in = session.get("user") is not None
    return render_template("index.html", logged_in=logged_in)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if session.get("user") is None:
            return render_template("login.html")
        else:
            flash("You are already logged in.")
            return redirect(url_for("index"))
            
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        
        if user is None or not pbkdf2_sha256.verify(password, user.password):
            flash("Incorrect username or password.")
            return render_template("login.html")
        else:
            session["user"] = username
            flash("You have successfully logged in.")
            return redirect(url_for("index"))


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        passconfirm = request.form.get("passconfirm")
        
        if password != passconfirm:
            flash("Your passwords didn't match.")
            return render_template("signup.html")
        else:
            passhash = pbkdf2_sha256.hash(password)
            try:
                db.execute("INSERT INTO users (username, password) VALUES (:username, :passhash)", {"username": username, "passhash": passhash})
                db.commit()
            except:
                flash("That username already exists. Please select a different one.")
                return render_template("signup.html")
            
            flash("Congratulations, you have created your account. Now please log in.")
            return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session["user"] = None
    flash("You have been logged out.")
    return redirect(url_for("index"))