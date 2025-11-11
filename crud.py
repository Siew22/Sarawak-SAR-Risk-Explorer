# --------------------------------------------------------------------------
# --- crud.py for JalanSafe AI (Final Version) ---
# --------------------------------------------------------------------------
# This file contains all functions that directly interact with the database
# using the SQLAlchemy ORM.
# --------------------------------------------------------------------------

from sqlalchemy.orm import Session, joinedload
from typing import List

# Import our SQLAlchemy models and Pydantic schemas
import models
import schemas
import services

# --- User CRUD ---

def get_user(db: Session, user_id: int) -> models.User | None:
    """Reads a single user from the database by their ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Reads a single user from the database by their email."""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Creates a new user in the database."""
    # In a real app, you MUST hash the password here before saving.
    # e.g., using passlib: hashed_password = pwd_context.hash(user.password)
    fake_hashed_password = user.password + "_hashed" # Placeholder for hashing
    db_user = models.User(
        email=user.email,
        username=user.username,
        password_hash=fake_hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def add_points_to_user(db: Session, user_id: int, points_to_add: int) -> models.User | None:
    """Adds points to a user's score after a successful contribution."""
    db_user = get_user(db, user_id=user_id)
    if db_user:
        db_user.points += points_to_add
        db.commit()
        db.refresh(db_user)
    return db_user

# --- Report CRUD ---

def create_report(db: Session, report: schemas.ReportCreate) -> models.Report:
    """
    Creates a new report in the database, automatically fetches the address,
    and awards points to the user.
    """
    # 1. Automatically perform reverse geocoding to get the human-readable address
    point_for_geocoding = schemas.Point(lat=report.latitude, lon=report.longitude)
    address_text = services.reverse_geocode_location(point_for_geocoding)

    # 2. Create the SQLAlchemy model instance with the fetched address.
    #    The quality_score will use the default value (e.g., 40) set in models.py.
    db_report = models.Report(
        user_id=report.user_id,
        latitude=report.latitude,
        longitude=report.longitude,
        report_type=report.report_type,
        description=report.description,
        photo_url=report.photo_url,
        address=address_text
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # 3. Award points to the user for their contribution.
    POINTS_PER_REPORT = 10
    add_points_to_user(db, user_id=report.user_id, points_to_add=POINTS_PER_REPORT)
    
    return db_report

def get_report(db: Session, report_id: int) -> models.Report | None:
    """Reads a single report from the database by its ID."""
    return db.query(models.Report).filter(models.Report.id == report_id).first()

def update_report_score_based_on_comment(db: Session, report_id: int, vote: str):
    """
    Updates a report's quality_score based on community feedback (agree/disagree).
    """
    db_report = get_report(db, report_id=report_id)
    if not db_report:
        return None

    # Define how votes affect the score
    AGREE_PENALTY = 5
    DISAGREE_BONUS = 10
    
    if vote == "agree":
        db_report.quality_score = max(0, db_report.quality_score - AGREE_PENALTY)
    elif vote == "disagree":
        db_report.quality_score = min(100, db_report.quality_score + DISAGREE_BONUS)
    
    db.commit()
    return db_report

# --- Comment CRUD ---

def get_comments_for_report(db: Session, report_id: int) -> List[models.Comment]:
    """Reads all comments associated with a single report, with user info preloaded."""
    return db.query(models.Comment).options(joinedload(models.Comment.owner)).filter(models.Comment.report_id == report_id).all()

def get_comment_count(db: Session, report_id: int) -> int:
    """Counts how many comments a report has."""
    return db.query(models.Comment).filter(models.Comment.report_id == report_id).count()

def create_comment(db: Session, comment: schemas.CommentCreate, report_id: int) -> models.Comment:
    """Creates a new comment for a report."""
    db_user = get_user(db, user_id=comment.user_id)
    if not db_user:
        # This case should ideally not happen if user_id is validated properly
        raise ValueError("User not found")
        
    db_comment = models.Comment(
        comment_text=comment.comment_text,
        user_id=comment.user_id,
        report_id=report_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

# --- Route Choice CRUD ---

def create_route_choice(db: Session, choice: schemas.RouteChoiceCreate):
    """Logs a user's choice of route."""
    db_choice = models.RouteChoice(
        user_id=choice.user_id,
        chosen_route_hash=choice.chosen_route_hash
    )
    db.add(db_choice)
    db.commit()
    db.refresh(db_choice)
    return db_choice

# --- Ranking ---

def get_user_rankings(db: Session, limit: int = 100) -> List[models.User]:
    """Gets the top N users based on their points."""
    return db.query(models.User).order_by(models.User.points.desc()).limit(limit).all()