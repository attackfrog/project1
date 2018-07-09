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
            # redirect user to index if they got here somehow while logged in
            flash("You are already logged in.")
            return redirect(url_for("index"))
            
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = :username;", {"username": username}).fetchone()
        
        # fail to login if users table doesn't contain this username, or the password doesn't verify
        if user is None or not pbkdf2_sha256.verify(password, user.password):
            flash("Incorrect username or password.")
            return render_template("login.html")
        else:
            # on success, add username to the session as "user" to designate logged in status
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
            # hash the password and attempt to insert it into the users table
            passhash = pbkdf2_sha256.hash(password)
            try:
                db.execute("INSERT INTO users (username, password) VALUES (:username, :passhash);", {"username": username, "passhash": passhash})
                db.commit()
            except:
                # if there's an error, it's (probably) because the username already exists in the table
                flash("That username already exists. Please select a different one.")
                return render_template("signup.html")
            
            # could also just directly have them be logged in, but this should help people remember passwords?
            flash("Congratulations, you have created your account. Now please log in.")
            return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session["user"] = None
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/search")
def search():
    logged_in = session.get("user") is not None
    if not logged_in:
        flash("You must be logged in to search.")
        return redirect(url_for("login"))
    
    query = request.args.get("loc")
    if not query:
        return redirect(url_for('index'))
    
    querycity = f"%{query.upper()}%"
    results = db.execute("SELECT zipcode, city, state, pop FROM locations WHERE zipcode = :query OR city LIKE :querycity;", {"query": query, "querycity": querycity})
    
    resultslist = []
    # debug code
    for result in results:
        resultslist.append(result)
    
    return render_template("search.html", results=resultslist, query=query, logged_in=logged_in)