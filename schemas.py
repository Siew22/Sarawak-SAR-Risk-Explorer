# --------------------------------------------------------------------------
# --- schemas.py for JalanSafe AI ---
# --------------------------------------------------------------------------
# This file contains all the Pydantic models used for API data validation
# and response serialization. They define the "shape" of the data that
# our API expects to receive and send.
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
        orm_mode = True # This allows the model to be created from an ORM object

class UserRank(BaseModel):
    username: str
    points: int

    class Config:
        orm_mode = True

# --- Report Schemas ---

class ReportTypeEnum(str, Enum):
    road_condition = "road_condition"
    traffic_light = "traffic_light"

class RouteIssue(BaseModel):
    issue_type: str # Keep as string
    description: str
    photo_url: str
    latitude: float
    longitude: float

class ReportBase(BaseModel):
    # --- ADD these two lines ---
    latitude: float
    longitude: float
    
    report_type: ReportTypeEnum
    description: str
    quality_score: Optional[int] = None

class ReportCreate(ReportBase):
    user_id: int
    photo_url: str
    # latitude 和 longitude 会从 ReportBase 自动继承下来

class Report(ReportBase):
    id: int
    user_id: int
    photo_url: str
    created_at: datetime
    address: Optional[str] = None
    
    class Config:
        from_attributes = True # Pydantic v2 uses from_attributes instead of orm_mode

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
    # Add a field to hold the user's info
    owner: UserInDB # This will nest the user's username in the comment

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
    # 添加这两个可选字段
    current_lat: Optional[float] = Field(None, example=3.1390)
    current_lon: Optional[float] = Field(None, example=101.6869)

# --- 在这里添加下面的新模型 ---
class RouteRequestWithStartCoords(BaseModel):
    start_lat: float
    start_lon: float
    end_name: str
# --- 添加结束 ---
    
class RouteResult(BaseModel):
    id: str
    distance: float
    base_travel_time: float
    color: str
    final_score: float
    geometry: str
    # You can add more fields here as needed