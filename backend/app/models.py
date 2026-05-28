from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    """
    User account model. Handles credentials and password hashes.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")


class InterviewSession(Base):
    """
    Stores interview session setups, target job details, resume content,
    and parsed ATS optimization metrics.
    """
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String, nullable=False)
    job_description = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=False)
    
    # ATS Analysis fields (saved after upload/matching)
    ats_score = Column(Integer, nullable=True)
    ats_skills_matched = Column(JSON, nullable=True)
    ats_skills_missing = Column(JSON, nullable=True)
    ats_keywords_missing = Column(JSON, nullable=True)
    ats_recommendations = Column(JSON, nullable=True)
    
    max_questions = Column(Integer, default=5, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    report = relationship("InterviewReport", back_populates="session", uselist=False, cascade="all, delete-orphan")


class InterviewQuestion(Base):
    """
    Stores generated questions, expected concepts, candidate answers, 
    and detailed AI gradings for each turn.
    """
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    expected_concepts = Column(JSON, nullable=False)
    focus_area = Column(String, nullable=False)
    difficulty = Column(String, default="Medium")
    
    # Candidate responses & scoring
    candidate_answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    model_answer = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="questions")


class InterviewReport(Base):
    """
    Aggregates overall score and recommendations to finalize the interview session.
    """
    __tablename__ = "interview_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_score = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    key_strengths = Column(JSON, nullable=False)
    improvement_areas = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("InterviewSession", back_populates="report")
