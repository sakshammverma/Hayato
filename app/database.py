import os
from datetime import datetime
from sqlalchemy import create_engine, String, Integer, Column, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reviews.db")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine= create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base= declarative_base()

class Review(Base):
    __tablename__ = "review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_name = Column(String, nullable=False)
    pr_number= Column(Integer, nullable=False)
    verdict = Column(String, nullable=True)
    issues_found = Column(Integer, default=0)
    files_count = Column(Integer, default=0)
    reviewed_at =Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_review(repo_name: str, pr_number: int, verdict: str, issues_found: int, files_count: int):
    session = SessionLocal()
    try:
        review = Review(
            repo_name= repo_name,
            pr_number= pr_number,
            verdict = verdict,
            issues_found = issues_found,
            files_count= files_count
        )
        session.add(review)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DB] Error saving review: {e}")
    finally:
        session.close()

def get_all_reviews() -> list:
    session = SessionLocal()
    try:
        return session.query(Review).order_by(Review.reviewed_at.desc()).all()
    finally:
        session.close()
        