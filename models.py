# ==========================================================================
#
#   models.py for JalanSafe AI (Corrected & Complete Version)
#
# ==========================================================================

from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Float, 
    DateTime, 
    Enum as SQLAlchemyEnum, # Rename to avoid conflict with standard Enum
    ForeignKey, 
    Text
)
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

# Define an Enum for report types. This is good practice for fixed choices.
class ReportTypeEnum(str, enum.Enum):
    road_condition = "road_condition"
    traffic_light = "traffic_light"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reports = relationship("Report", back_populates="owner")
    comments = relationship("Comment", back_populates="owner")
    route_choices = relationship("RouteChoice", back_populates="user") # Added back-reference

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- CRITICAL FIX: Add ForeignKey to establish the relationship ---
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # --- Complete the model with all necessary fields ---
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    report_type = Column(SQLAlchemyEnum(ReportTypeEnum), nullable=False)
    description = Column(Text, nullable=True)
    photo_url = Column(String(255), nullable=False)
    quality_score = Column(Integer, default=40)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="reports")
    comments = relationship("Comment", back_populates="report", cascade="all, delete-orphan") # Cascade delete

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="comments")
    owner = relationship("User", back_populates="comments")

class RouteChoice(Base):
    __tablename__ = "route_choices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chosen_route_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="route_choices")