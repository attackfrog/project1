# Project 1: Rainy Day

*CSCI S-33 - Web Programming with Python and JavaScript*

Get weather information and post comments on your favorite locations in the US! Rainy day is a community approach to weather information, and comes with an API for easy developer access.

## Setup

* Set the DATABASE_URL environment variable to the appropriate database URI
* Set DARKSKY_KEY to your Dark Sky API key
* Install all requirements
* Set up database as described by `database.sql`
* Import zip code data from `zips.csv` with `python import.py`
* `flask run`!

## Structure

`application.py` - all server code, including the following routes: 
* `/` - home page, displaying welcome for new visitors and search box for logged in users
* `/login` - login page
* `/signup` - account creation page
* `/logout` - logout route, redirects to index
* `/search` - called with the "loc" argument for location queries, gives a list of results in the database that match the query
* `/weather/<zipcode>` - displays current and forecast weather for a location along with user comments and some location info
* `/checkin` - POST only, used for submitting comments
* `/api/<zipcode>` - returns JSON-formatted information about a zip code

`import.py` - imports zip code information from `zips.csv` into the database

`templates/*` - templated HTML files to serve to the user, using Bootstrap for styling

* `basic.html` - the standard template, including nav bar. Displays "log out" and a search bar if logged in.
* `index.html` - the home page: displays welcome message if not logged in and search box if logged in
* `login.html` - displays login box
* `signup.html` - displays signup box
* `search.html` - displays search results list
* `weather.html` - displays location weather and comments

`css/index.css` - custom styling for various components
