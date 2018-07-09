import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Open file
file = open("zips.csv")
reader = csv.reader(file)

# Skip known header line
next(reader)

progress = 0

for zipcode, city, state, lat, lon, pop in reader:
    try:
        db.execute("INSERT INTO locations (zipcode, city, state, lat, long, pop) VALUES (:zipcode, :city, :state, :lat, :lon, :pop);", 
                { "zipcode": zipcode, "city": city, "state": state, "lat": lat, "lon": lon, "pop":pop })
        progress = progress + 1
        if progress % 100 == 0:
            print(f"Inserted {progress} zip codes...")
        
    except:
        raise RuntimeError(f"Error inserting zipcode {zipcode} into the table.")

try:
    print("Committing changes to database...")
    db.commit()
except:
    raise RuntimeError("Failed to commit changes.")
    
print(f"Successfully imported {progress} zip codes.")