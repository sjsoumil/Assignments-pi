from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional

app = FastAPI()

# MongoDB client
client = MongoClient("mongodb://localhost:27017/")
db = client["event_booking"]
users_collection = db["users"]
events_collection = db["events"]

# JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class User(BaseModel):
    username: str
    email: str
    password_hash: str  

    class Config:
        json_encoders = {
            ObjectId: str
        }

class Event(BaseModel):
    name: str
    date: datetime
    location: str
    description: Optional[str] = None
    creator_id: Optional[str] = None  

    class Config:
        json_encoders = {
            ObjectId: str
        }

# Helper Functions
def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = users_collection.find_one({"_id": ObjectId(payload["sub"])})
        if user:
            return user
        raise HTTPException(status_code=404, detail="User not found")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Routes
@app.post("/token")
async def login(username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/events/", response_model=Event)
async def create_event(event: Event, token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(token)
    event.creator_id = str(user["_id"])
    event_data = event.dict()
    event_data["_id"] = ObjectId()
    events_collection.insert_one(event_data)
    return event

@app.get("/events/", response_model=List[Event])
async def get_events(token: str = Depends(oauth2_scheme)):
    get_user_from_token(token)  
    events = list(events_collection.find())
    for event in events:
        event["_id"] = str(event["_id"])
    return events

@app.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str, token: str = Depends(oauth2_scheme)):
    get_user_from_token(token)  
    event = events_collection.find_one({"_id": ObjectId(event_id)})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event["_id"] = str(event["_id"])
    return event

@app.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event: Event, token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(token)
    existing_event = events_collection.find_one({"_id": ObjectId(event_id)})
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    if existing_event["creator_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    updated_event = event.dict(exclude_unset=True)
    events_collection.update_one(
        {"_id": ObjectId(event_id)}, {"$set": updated_event}
    )
    return {**existing_event, **updated_event}

@app.delete("/events/{event_id}")
async def delete_event(event_id: str, token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(token)
    event = events_collection.find_one({"_id": ObjectId(event_id)})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event["creator_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this event")
    events_collection.delete_one({"_id": ObjectId(event_id)})
    return {"message": "Event deleted successfully"}
