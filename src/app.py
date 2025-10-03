"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""


from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import copy


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# Initial activities data for pre-population
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in local leagues",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly matches",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act in plays and participate in theater productions",
        "schedule": "Mondays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["noah@mergington.edu", "isabella@mergington.edu"]
    },
    "Art Workshop": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["amelia@mergington.edu", "benjamin@mergington.edu"]
    },
    "Math Olympiad": {
        "description": "Prepare for math competitions and solve challenging problems",
        "schedule": "Fridays, 2:00 PM - 3:30 PM",
        "max_participants": 15,
        "participants": ["charlotte@mergington.edu", "elijah@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 16,
        "participants": ["james@mergington.edu", "harper@mergington.edu"]
    }
}

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
db = client["mergington_high"]
activities_col = db["activities"]
activities_col.create_index("name", unique=True)

# Pre-populate activities if not already present
def prepopulate_activities():
    for name, details in initial_activities.items():
        if not activities_col.find_one({"name": name}):
            doc = copy.deepcopy(details)
            doc["name"] = name
            try:
                activities_col.insert_one(doc)
            except DuplicateKeyError:
                pass

prepopulate_activities()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")



@app.get("/activities")
def get_activities():
    # Return as dict keyed by activity name for frontend compatibility
    result = {}
    for doc in activities_col.find():
        d = dict(doc)
        name = d.pop("name")
        d.pop("_id", None)
        result[name] = d
    return result




@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    doc = activities_col.find_one({"name": activity_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Activity not found")
    if email in doc.get("participants", []):
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")
    # Add student
    activities_col.update_one(
        {"name": activity_name},
        {"$push": {"participants": email}}
    )
    return {"message": f"Signed up {email} for {activity_name}"}


# Unregister endpoint using MongoDB
@app.post("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Remove a student from an activity"""
    doc = activities_col.find_one({"name": activity_name})
    if not doc:
        raise HTTPException(status_code=404, detail="Activity not found")
    if email not in doc.get("participants", []):
        raise HTTPException(status_code=400, detail="Student is not registered for this activity")
    activities_col.update_one(
        {"name": activity_name},
        {"$pull": {"participants": email}}
    )
    return {"message": f"Removed {email} from {activity_name}"}
