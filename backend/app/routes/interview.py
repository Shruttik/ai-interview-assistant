import os
import shutil
from typing import List, Dict, Optional, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import User, InterviewSession, InterviewQuestion, InterviewReport, UserTopicScore, PerformanceTracking
from backend.app.schemas import (
    SessionResponse, 
    QuestionResponse, 
    AnswerSubmit, 
    AnswerResponse, 
    FinalReportResponse,
    ATSAnalysisResponse
)
from backend.app.utils.auth import get_current_user
from backend.app.utils.logger import logger
from backend.app.utils.helpers import ensure_directory_exists
from backend.app.services.resume_service import resume_service
from backend.app.services.llm_service import llm_service

router = APIRouter(prefix="/interview", tags=["interview"])

# ---------------------------------------------------------------------------
# Sessions & ATS Endpoints
# ---------------------------------------------------------------------------

@router.post("/session/start", response_model=Dict[str, Any])
async def start_interview_session(
    job_title: str = Form(...),
    job_description: str = Form(""),
    max_questions: int = Form(5),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Initializes a new database-backed interview session.
    Parses resume, runs resume analysis, creates a session, and yields the first question.
    """
    logger.info(f"User {current_user.email} initiating interview for job: {job_title}")
    
    # Save uploaded file temporarily
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in [".pdf", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume format. Please upload PDF or TXT."
        )
        
    ensure_directory_exists(settings.upload_dir)
    temp_file_path = os.path.join(settings.upload_dir, f"session_start_{current_user.id}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        resume_text = resume_service.extract_text(temp_file_path)
        if not resume_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uploaded resume text is empty or could not be parsed."
            )
            
        # Call LLM to parse resume skills and summary
        resume_analysis = llm_service.analyze_resume(resume_text, api_key=x_gemini_api_key)
        
        # Save session to DB
        session = InterviewSession(
            user_id=current_user.id,
            job_title=job_title,
            job_description=job_description,
            resume_text=resume_text,
            max_questions=max_questions
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Fetch performance profile for adaptive context
        profile = db.query(PerformanceTracking).filter(
            PerformanceTracking.user_id == current_user.id
        ).first()
        weak_topics = profile.weak_topics if profile else []
        strong_topics = profile.strong_topics if profile else []

        # Generate first question
        first_q = llm_service.generate_question(
            job_title=job_title,
            job_description=job_description,
            resume_skills=resume_analysis.skills,
            history=[],
            previous_evaluations=[],
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            api_key=x_gemini_api_key
        )
        
        # Save first question to DB
        db_question = InterviewQuestion(
            session_id=session.id,
            question_text=first_q.question,
            expected_concepts=first_q.expected_concepts,
            focus_area=first_q.focus_area,
            difficulty=first_q.difficulty
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        
        return {
            "session_id": session.id,
            "resume_analysis": {
                "skills": resume_analysis.skills,
                "experience_summary": resume_analysis.experience_summary,
                "recommended_topics": resume_analysis.recommended_topics
            },
            "first_question": {
                "id": db_question.id,
                "question": db_question.question_text,
                "focus_area": db_question.focus_area,
                "expected_concepts": db_question.expected_concepts,
                "difficulty": db_question.difficulty
            }
        }
        
    except ValueError as ve:
        logger.error(f"Validation error starting session: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error starting interview session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/resume/ats-analyze", response_model=ATSAnalysisResponse)
async def ats_analyze_resume(
    job_title: str = Form(...),
    job_description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Performs ATS keyword match, skill gap analysis, and formatting suggestions.
    Saves the report and session in the database so it can be reloaded in history.
    """
    logger.info(f"ATS Resume Profiling requested by {current_user.email} for job: {job_title}")
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in [".pdf", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Upload a PDF or TXT file."
        )
        
    ensure_directory_exists(settings.upload_dir)
    temp_file_path = os.path.join(settings.upload_dir, f"ats_{current_user.id}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        resume_text = resume_service.extract_text(temp_file_path)
        if not resume_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resume could not be read."
            )
            
        # Get ATS scorecard from LLM
        ats_report = llm_service.analyze_resume_ats(
            resume_text=resume_text, 
            job_description=job_description,
            api_key=x_gemini_api_key
        )
        
        # Save session with ATS report details
        session = InterviewSession(
            user_id=current_user.id,
            job_title=job_title,
            job_description=job_description,
            resume_text=resume_text,
            ats_score=ats_report.score,
            ats_skills_matched=ats_report.skills_matched,
            ats_skills_missing=ats_report.skills_missing,
            ats_keywords_missing=ats_report.keywords_missing,
            ats_recommendations=ats_report.recommendations,
            max_questions=0 # ATS session, no questions simulated
        )
        db.add(session)
        db.commit()
        
        return ats_report
        
    except ValueError as ve:
        logger.error(f"Validation error during ATS: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"ATS service failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS Analysis failed: {str(e)}"
        )
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# ---------------------------------------------------------------------------
# Q&A Loop Endpoints
# ---------------------------------------------------------------------------

@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
async def submit_session_answer(
    session_id: int,
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Submits candidate's answer for evaluation.
    Updates the active question in the DB, queries history, and generates the next
    adaptive question if within constraints.
    """
    # 1. Fetch Session and verify ownership
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )
        
    # 2. Get latest unanswered question
    unanswered_q = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id,
        InterviewQuestion.candidate_answer == None
    ).order_by(InterviewQuestion.id.asc()).first()
    
    if not unanswered_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active question waiting for response."
        )
        
    try:
        # 3. Evaluate the answer
        eval_result = llm_service.evaluate_answer(
            question=unanswered_q.question_text,
            expected_concepts=unanswered_q.expected_concepts,
            candidate_answer=payload.candidate_answer,
            api_key=x_gemini_api_key
        )
        
        # 4. Save evaluation to DB
        unanswered_q.candidate_answer = payload.candidate_answer
        unanswered_q.score = eval_result.score
        unanswered_q.feedback = eval_result.feedback
        unanswered_q.strengths = eval_result.strengths
        unanswered_q.weaknesses = eval_result.weaknesses
        unanswered_q.model_answer = eval_result.model_answer
        
        db.commit()
        db.refresh(unanswered_q)
        
        # 5. Fetch all completed questions in this session for adaptive context
        completed_questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.candidate_answer != None
        ).all()
        
        completed_turns = len(completed_questions)
        
        next_question_response = None
        
        # 6. Generate next question if max count is not met
        if completed_turns < session.max_questions:
            # Build conversation history text format
            history = []
            previous_evals = []
            for q in completed_questions:
                history.append({"role": "interviewer", "text": q.question_text})
                history.append({"role": "candidate", "text": q.candidate_answer})
                previous_evals.append({
                    "question": q.question_text,
                    "score": q.score,
                    "focus_area": q.focus_area,
                    "strengths": q.strengths,
                    "weaknesses": q.weaknesses
                })
                
            # Build resume skills list (rough fallback split)
            resume_skills = [s.strip() for s in session.resume_text.split("\n") if len(s.strip()) < 50][:15]
            
            # Fetch performance profile for adaptive context
            profile = db.query(PerformanceTracking).filter(
                PerformanceTracking.user_id == current_user.id
            ).first()
            weak_topics = profile.weak_topics if profile else []
            strong_topics = profile.strong_topics if profile else []

            # Generate next question with adaptive difficulty/weak topics
            next_q = llm_service.generate_question(
                job_title=session.job_title,
                job_description=session.job_description or "",
                resume_skills=resume_skills,
                history=history,
                previous_evaluations=previous_evals,
                weak_topics=weak_topics,
                strong_topics=strong_topics,
                api_key=x_gemini_api_key
            )
            
            # Save next question to DB
            db_next_q = InterviewQuestion(
                session_id=session_id,
                question_text=next_q.question,
                expected_concepts=next_q.expected_concepts,
                focus_area=next_q.focus_area,
                difficulty=next_q.difficulty
            )
            db.add(db_next_q)
            db.commit()
            db.refresh(db_next_q)
            
            # Map database model to schemas.QuestionResponse
            next_question_response = QuestionResponse(
                id=db_next_q.id,
                question=db_next_q.question_text,
                focus_area=db_next_q.focus_area,
                expected_concepts=db_next_q.expected_concepts,
                difficulty=db_next_q.difficulty
            )
            
        return AnswerResponse(
            evaluation={
                "score": unanswered_q.score,
                "feedback": unanswered_q.feedback,
                "strengths": unanswered_q.strengths,
                "weaknesses": unanswered_q.weaknesses,
                "model_answer": unanswered_q.model_answer
            },
            next_question=next_question_response
        )
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while scoring response: {str(e)}"
        )


@router.post("/session/{session_id}/finalize", response_model=FinalReportResponse)
def finalize_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Grades the entire interview session, compiles summary analytics, 
    and saves the FinalReport in the database.
    """
    # Stage 1: Session retrieval
    logger.info(f"[Finalize Session] Stage 1 - Session retrieval. session_id: {session_id}, user: {current_user.email}")
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        logger.error(f"[Finalize Session] Session {session_id} not found for user {current_user.email}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )
        
    # Check if report already exists
    if session.report:
        logger.info(f"[Finalize Session] Existing report found for session {session_id}. Sanitizing nulls and returning.")
        # Ensure older null records are handled safely to satisfy FinalReportResponse schema
        if session.report.key_strengths is None:
            session.report.key_strengths = []
        if session.report.improvement_areas is None:
            session.report.improvement_areas = []
        if session.report.recommendations is None:
            session.report.recommendations = []
        if session.report.topics_to_revise is None:
            session.report.topics_to_revise = []
        if session.report.concepts_to_strengthen is None:
            session.report.concepts_to_strengthen = []
        if session.report.suggested_focus is None:
            session.report.suggested_focus = "Focus on weak subject areas in future practice."
        return session.report
        
    # Fetch all answered questions
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id,
        InterviewQuestion.candidate_answer != None
    ).all()
    
    if not questions:
        logger.warning(f"[Finalize Session] Cannot finalize session {session_id} because the transcript is empty.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compile final scorecard for an empty transcript."
        )
        
    # Stage 2: Answer aggregation
    logger.info(f"[Finalize Session] Stage 2 - Answer aggregation. Found {len(questions)} answered questions.")
    transcript_evaluations = []
    scores = []
    
    for q in questions:
        # Default any missing scores to 5
        score_val = q.score
        if score_val is None:
            logger.warning(f"[Finalize Session] Question ID {q.id} has missing score. Defaulting to 5.")
            score_val = 5
        scores.append(score_val)
        
        transcript_evaluations.append({
            "question": q.question_text,
            "answer": q.candidate_answer,
            "score": score_val,
            "feedback": q.feedback or "No feedback provided.",
            "strengths": q.strengths or [],
            "weaknesses": q.weaknesses or []
        })
        
    # Stage 3: AI evaluation / Fallback Report Creation
    logger.info(f"[Finalize Session] Stage 3 - AI evaluation. Generating report for session {session_id}.")
    try:
        final_report = llm_service.generate_final_report(
            job_title=session.job_title,
            transcript_evaluations=transcript_evaluations,
            api_key=x_gemini_api_key
        )
        logger.info(f"[Finalize Session] AI scorecard generated successfully for session {session_id}.")
    except Exception as e:
        logger.error(f"[Finalize Session] Gemini final report generation failed: {e}. Generating fallback scorecard.")
        from backend.app.services.llm_service import FinalReport
        
        # Calculate overall score from aggregation
        avg_score = round(sum(scores) / len(scores)) if scores else 5
        
        # Gather focus areas and expected concepts for fallback lists
        topics = list(set([q.focus_area for q in questions if q.focus_area]))
        concepts = []
        for q in questions:
            if q.expected_concepts:
                concepts.extend(q.expected_concepts)
        concepts = list(set(concepts))
        
        # Construct fallback scorecard matching the schema
        final_report = FinalReport(
            overall_score=max(1, min(10, int(avg_score))),
            summary=f"Fallback Report: Performance summary for role {session.job_title} compiled based on auto-aggregation of scores. The AI evaluation service is temporarily offline.",
            key_strengths=["Successfully attempted the technical questions asked in the session."],
            improvement_areas=["Review and practice topics covered during the session to improve scores."],
            recommendations=["Practice mock interviews under timed constraints to increase confidence."],
            topics_to_revise=topics if topics else ["General"],
            concepts_to_strengthen=concepts if concepts else ["Core Concepts"],
            suggested_focus="Practice mock interview sessions in technical focus areas where performance was lower."
        )
        logger.info(f"[Finalize Session] Fallback scorecard created successfully for session {session_id}.")
        
    try:
        # Stage 4: Score calculation & Performance profile updates
        logger.info(f"[Finalize Session] Stage 4 - Score calculation and user metrics update.")
        topic_aggregations = {}
        for q in questions:
            focus_area = q.focus_area or "General"
            q_score = q.score if q.score is not None else 5
            
            # Clean topic name and map to standard categories
            topic = focus_area.strip()
            t_upper = topic.upper()
            mapped_topic = topic # default
            for standard_topic in ["OOP", "DBMS", "SQL", "Operating Systems", "Computer Networks", "DSA", "Python", "Java"]:
                if standard_topic.upper() in t_upper or (standard_topic == "Operating Systems" and "OS" in t_upper):
                    mapped_topic = standard_topic
                    break
            
            if mapped_topic not in topic_aggregations:
                topic_aggregations[mapped_topic] = {"total_score": 0, "count": 0}
            topic_aggregations[mapped_topic]["total_score"] += q_score
            topic_aggregations[mapped_topic]["count"] += 1

        # Save/update UserTopicScore in database
        for topic_name, data in topic_aggregations.items():
            db_score = db.query(UserTopicScore).filter(
                UserTopicScore.user_id == current_user.id,
                UserTopicScore.topic == topic_name
            ).first()
            if db_score:
                db_score.total_score += data["total_score"]
                db_score.question_count += data["count"]
                db_score.avg_score = db_score.total_score / db_score.question_count
                db_score.last_updated = datetime.utcnow()
            else:
                db_score = UserTopicScore(
                    user_id=current_user.id,
                    topic=topic_name,
                    total_score=data["total_score"],
                    question_count=data["count"],
                    avg_score=data["total_score"] / data["count"],
                    last_updated=datetime.utcnow()
                )
                db.add(db_score)

        # Recalculate PerformanceTracking weak/strong areas and difficulty level
        all_scores = db.query(UserTopicScore).filter(
            UserTopicScore.user_id == current_user.id
        ).all()
        
        weak_topics_list = []
        strong_topics_list = []
        overall_avg_sum = 0.0
        
        if all_scores:
            for s in all_scores:
                overall_avg_sum += s.avg_score
                if s.avg_score < 6.0:
                    weak_topics_list.append(s.topic)
                elif s.avg_score >= 8.0:
                    strong_topics_list.append(s.topic)
            
            overall_avg = overall_avg_sum / len(all_scores)
            if overall_avg >= 8.0:
                difficulty_level = "Advanced"
            elif overall_avg >= 6.0:
                difficulty_level = "Intermediate"
            else:
                difficulty_level = "Beginner"
        else:
            difficulty_level = "Beginner"

        profile_record = db.query(PerformanceTracking).filter(
            PerformanceTracking.user_id == current_user.id
        ).first()
        if profile_record:
            profile_record.weak_topics = weak_topics_list
            profile_record.strong_topics = strong_topics_list
            profile_record.difficulty_level = difficulty_level
            profile_record.last_updated = datetime.utcnow()
        else:
            profile_record = PerformanceTracking(
                user_id=current_user.id,
                weak_topics=weak_topics_list,
                strong_topics=strong_topics_list,
                difficulty_level=difficulty_level,
                last_updated=datetime.utcnow()
            )
            db.add(profile_record)

        # Stage 5: Report creation
        logger.info(f"[Finalize Session] Stage 5 - Saving report for session {session_id} to database.")
        db_report = InterviewReport(
            session_id=session_id,
            overall_score=final_report.overall_score,
            summary=final_report.summary,
            key_strengths=final_report.key_strengths or [],
            improvement_areas=final_report.improvement_areas or [],
            recommendations=final_report.recommendations or [],
            topics_to_revise=final_report.topics_to_revise or [],
            concepts_to_strengthen=final_report.concepts_to_strengthen or [],
            suggested_focus=final_report.suggested_focus or "Focus on weak subject areas in future practice."
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"[Finalize Session] Session {session_id} finalized and report saved successfully.")
        return db_report
        
    except Exception as e:
        logger.error(f"[Finalize Session] Error saving scorecard metadata for session {session_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save final scorecard: {str(e)}"
        )
