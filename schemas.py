# --------------------------------------------------------------------------
# --- schemas.py for JalanSafe AI (Final Real-Time Version) ---
# --------------------------------------------------------------------------
# This file defines the exact structure of data exchanged between the API
# and the frontend. It must match services.py exactly.
# --------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# --- Base Models ---

class Point(BaseModel):
    lat: float = Field(..., example=3.1390)
    lon: float = Field(..., example=101.6869)

# --- User Schemas ---

class UserInDB(BaseModel):
    username: str

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    points: int

    class Config:
        from_attributes = True

class UserRank(BaseModel):
    username: str
    points: int

    class Config:
        from_attributes = True

# --- Report Schemas ---

class ReportTypeEnum(str, Enum):
    road_condition = "road_condition"
    traffic_light = "traffic_light"

# Used inside RouteResult
class RouteIssue(BaseModel):
    description: str
    photo_url: str
    type: str
    date: str

class ReportBase(BaseModel):
    latitude: float
    longitude: float
    report_type: ReportTypeEnum
    description: str
    quality_score: Optional[int] = None

class ReportCreate(ReportBase):
    user_id: int
    photo_url: str

class Report(ReportBase):
    id: int
    user_id: int
    photo_url: str
    created_at: datetime
    address: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Comment Schemas ---

class CommentBase(BaseModel):
    comment_text: str

class CommentCreate(CommentBase):
    user_id: int
    vote: str # 'agree' or 'disagree'

class Comment(CommentBase):
    id: int
    user_id: int
    created_at: datetime
    owner: UserInDB

    class Config:
        from_attributes = True
        
# --- Routing Schemas ---

class RouteRequest(BaseModel):
    start: Point
    end: Point

class RouteChoiceCreate(BaseModel):
    user_id: int
    chosen_route_hash: str

class RouteRequestByName(BaseModel):
    start_name: str = Field(..., example="Kuala Lumpur Tower")
    end_name: str = Field(..., example="Petronas Twin Towers")
    current_lat: Optional[float] = Field(None)
    current_lon: Optional[float] = Field(None)

class RouteRequestWithStartCoords(BaseModel):
    start_lat: float
    start_lon: float
    end_name: str
    
# --- CRITICAL UPDATE: Matching the Real-Time Logic ---
class RouteResult(BaseModel):
    id: str
    geometry: str
    distance: float
    base_travel_time: float
    color: str
    
    # New fields for the Real-Time System
    active_users: int
    issues: List[RouteIssue]
    weather: str
    tags: List[str]
    is_optimal: bool
    time_slower: float

    # final_score is removed because we now use direct rule-based logic