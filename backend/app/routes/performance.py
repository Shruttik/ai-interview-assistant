from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import User, UserTopicScore, PerformanceTracking
from backend.app.schemas import UserPerformanceProfile
from backend.app.utils.auth import get_current_user
from backend.app.utils.logger import logger

router = APIRouter(prefix="/performance", tags=["performance"])

# Standard predefined topic lists
DEFAULT_TOPICS = ["OOP", "DBMS", "SQL", "Operating Systems", "Computer Networks", "DSA", "Python", "Java"]

@router.get("/profile", response_model=UserPerformanceProfile)
def get_user_performance_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the user's aggregated topic-wise scores, detected strong/weak areas,
    difficulty level, and personalized practice recommendations.
    """
    logger.info(f"User {current_user.email} requesting performance profile analytics.")
    try:
        # 1. Fetch or create overall PerformanceTracking profile
        profile = db.query(PerformanceTracking).filter(
            PerformanceTracking.user_id == current_user.id
        ).first()
        
        if not profile:
            profile = PerformanceTracking(
                user_id=current_user.id,
                weak_topics=[],
                strong_topics=[],
                difficulty_level="Beginner"
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
        # 2. Fetch all topic scores
        topic_scores = db.query(UserTopicScore).filter(
            UserTopicScore.user_id == current_user.id
        ).order_by(UserTopicScore.avg_score.desc()).all()
        
        # 3. Generate dynamic practice recommendations
        practice_suggestions = []
        recommended_topics = []
        
        weak_list = profile.weak_topics or []
        strong_list = profile.strong_topics or []
        
        if not weak_list:
            # Default recommendations for beginners/untracked profiles
            recommended_topics = ["DSA", "SQL", "OOP", "DBMS"]
            practice_suggestions = [
                "Initialize your first mock interview to compile your performance baseline.",
                "Review core object-oriented programming (OOP) principles and basic data structures.",
                "Practice writing simple SQL queries (SELECT, JOINs, Group By) to prepare for DBMS topics."
            ]
        else:
            recommended_topics = list(weak_list)
            # Custom recommendations mapped to identified weak areas
            for topic in weak_list:
                t_upper = topic.upper()
                if "SQL" in t_upper:
                    practice_suggestions.append("SQL: Practice aggregate query operations, indexing, and window functions on platforms like LeetCode.")
                elif "DBMS" in t_upper or "DATABASE" in t_upper:
                    practice_suggestions.append("DBMS: Study database normalizations, indexing structures (B-Trees), and ACID transaction properties.")
                elif "DSA" in t_upper or "ALGORITHM" in t_upper:
                    practice_suggestions.append("DSA: Focus on time/space complexity analysis (Big O) and common algorithms (recursion, sorting, trees).")
                elif "OOP" in t_upper or "OBJECT" in t_upper:
                    practice_suggestions.append("OOP: Review polymorphism, abstract classes, SOLID principles, and design patterns (like Singleton or Factory).")
                elif "OPERATING" in t_upper or "OS" in t_upper:
                    practice_suggestions.append("OS: Review CPU scheduling algorithms, virtual memory paging, multithreading, and deadlock conditions.")
                elif "NETWORK" in t_upper:
                    practice_suggestions.append("Networks: Study the TCP/IP stack layers, DNS operations, HTTP/HTTPS handshake protocol, and status codes.")
                elif "PYTHON" in t_upper:
                    practice_suggestions.append("Python: Review generators, decorators, memory management (GIL), and asynchronous frameworks (asyncio).")
                elif "JAVA" in t_upper:
                    practice_suggestions.append("Java: Study JVM memory structures (Heap vs Stack), garbage collection, interfaces, and multithreading basics.")
                else:
                    practice_suggestions.append(f"{topic}: Study core theoretical principles and standard interview Q&As associated with this focus area.")
            
            practice_suggestions.append("Suggested Action: Start a new mock interview session targeting these specific weak topics to strengthen your scores.")
            
        return {
            "difficulty_level": profile.difficulty_level,
            "weak_topics": weak_list,
            "strong_topics": strong_list,
            "topic_scores": topic_scores,
            "practice_suggestions": practice_suggestions,
            "recommended_topics": recommended_topics
        }
        
    except Exception as e:
        logger.error(f"Error loading performance profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compile performance profile analytics."
        )
