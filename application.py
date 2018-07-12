import os

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from passlib.hash import pbkdf2_sha256
import requests
from datetime import date

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
        
        if not username:
            flash("You must provide a username.")
            return render_template("signup.html")
        elif not password:
            flash("You must provide a password.")
            return render_template("signup.html")
        elif not passconfirm:
            flash("You must enter your password twice.")
            return render_template("signup.html")
        elif password != passconfirm:
            flash("Your passwords didn't match.")
            return render_template("signup.html")
        else:
            # hash the password and attempt to insert it into the users table
            passhash = pbkdf2_sha256.hash(password)
            try:
                db.execute("INSERT INTO users (username, password) VALUES (:username, :passhash);",
                           {"username": username, "passhash": passhash})
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
    results = db.execute("SELECT zipcode, city, state, pop FROM locations WHERE zipcode = :query OR city LIKE :querycity;", 
                         {"query": query, "querycity": querycity})
    
    resultslist = []
    for result in results:
        resultslist.append(result)
    
    return render_template("search.html", results=resultslist, query=query, logged_in=logged_in)


@app.route("/weather/<string:zipcode>")
def weather(zipcode):
    logged_in = session.get("user") is not None
    if not logged_in:
        flash("You must be logged in to view weather conditions.")
        return redirect(url_for("index"))
    if not validate_zipcode(zipcode):
        flash("That's not a valid zip code.")
        return redirect(url_for("index"))
    
    # get info for zip code
    zipinfo = db.execute("SELECT * FROM locations WHERE zipcode = :zipcode", {"zipcode": zipcode}).fetchone()
    if zipinfo is None:
        flash("That zip code is not in our database.")
        return redirect(url_for("index"))
    
    API_KEY = os.getenv("DARKSKY_KEY")
    try:
        # zipinfo[3] is latitude, zipinfo[4] is longitude
        response = requests.get(f"https://api.darksky.net/forecast/{API_KEY}/{zipinfo[3]},{zipinfo[4]}")
        weather = response.json()
    except:
        flash("Failed to communicate with the Dark Sky API.")
        return redirect(url_for("index"))
    
    comments = db.execute("SELECT * FROM checkins WHERE zipcode = :zipcode ORDER BY date DESC", {"zipcode": zipcode}).fetchall()
    # check if the user has commented today
    user = session.get("user")
    today = date.today()
    posted = False
    for comment in comments:
        print(comment)
        if comment.username == user:
            if comment.date == today:
                posted = True
                break
    
    return render_template("weather.html", zipinfo=zipinfo, weather=weather, 
                            comments=comments, posted=posted, logged_in=logged_in)
    

@app.route("/checkin", methods=["POST"])
def checkin():
    username = session.get("user")
    if username is None:
        flash("You must be logged in to submit a comment.")
        return redirect(url_for("index"))
    
    zipcode = request.form.get("zipcode")
    comment = request.form.get("comment")
    today = date.today()
    
    if not validate_zipcode(zipcode):
        flash("You tried to submit a comment for an invalid zipcode.")
        return redirect(url_for("index"))
    
    if len(comment) < 1:
        flash("You can't submit a blank comment.")
    
    try:
        db.execute("INSERT INTO checkins (zipcode, username, comment, date) VALUES (:zipcode, :username, :comment, :today);",
                    {"zipcode": zipcode, "username": username, "comment": comment, "today": today})
        db.commit()
    except:
        flash("Error submitting comment. Please try again later.")
    
    return redirect(url_for('weather', zipcode=zipcode))


@app.route("/api/<string:zipcode>")
def api(zipcode):
    if not validate_zipcode(zipcode):
        raise InvalidUsage("The provided zipcode is invalid.", status_code=400)
    
    try:
        # TODO: can this be merged into one database query?
        zipdata = db.execute("SELECT * FROM locations WHERE zipcode = :zipcode;", {"zipcode": zipcode}).fetchone()
        checkincount = db.execute("SELECT COUNT(*) FROM checkins WHERE zipcode = :zipcode", {"zipcode": zipcode}).fetchone()
    except:
        raise InvalidUsage("The database failed to respond properly to the request.", status_code=500)

    response = {"place_name": zipdata.city.capitalize(), "state": zipdata.state, "latitude": float(zipdata.lat), 
                "longitude": float(zipdata.long), "zip": zipdata.zipcode, "population": int(zipdata.pop), 
                "check_ins": int(checkincount[0])}
    return jsonify(response)
    

# the class and error handler below are from http://flask.pocoo.org/docs/1.0/patterns/apierrors/
class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def validate_zipcode(zipcode):
    try:
        int(zipcode)
        assert len(zipcode) == 5
    except:
        return False
    
    return True
    