from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, InterviewSession, InterviewQuestion
from backend.app.schemas import SessionResponse, SessionDetailResponse
from backend.app.utils.auth import get_current_user
from backend.app.utils.logger import logger

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/sessions", response_model=List[SessionResponse])
def get_user_sessions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all past interview sessions for the currently logged-in user.
    """
    logger.info(f"User {current_user.email} fetching past sessions history.")
    try:
        # Fetch sessions ordered by newest first
        sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == current_user.id
        ).order_by(InterviewSession.created_at.desc()).all()
        
        # Format session objects
        response_sessions = []
        for s in sessions:
            # Map score: if a report exists, use its overall_score; otherwise use ats_score or None
            ats_score = s.ats_score
            if s.report:
                ats_score = s.report.overall_score
                
            response_sessions.append(
                SessionResponse(
                    id=s.id,
                    job_title=s.job_title,
                    job_description=s.job_description,
                    ats_score=ats_score,
                    created_at=s.created_at
                )
            )
            
        return response_sessions
    except Exception as e:
        logger.error(f"Error fetching sessions for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history sessions."
        )


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_session_details(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves complete transcripts, grades, and scorecards for a specific past session.
    """
    logger.info(f"User {current_user.email} loading details for session ID {session_id}.")
    
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        logger.warning(f"Session {session_id} not found or unauthorized for {current_user.email}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session history not found."
        )
        
    try:
        # Load associated questions and reports directly (SQLAlchemy handles relationship)
        return session
    except Exception as e:
        logger.error(f"Error loading session detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load interview session details."
        )
