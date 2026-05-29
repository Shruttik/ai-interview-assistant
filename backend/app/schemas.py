from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ===========================================================================
# User / Auth Schemas
# ===========================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Password must be between 6 and 128 characters.")

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ===========================================================================
# ATS Analysis Schemas
# ===========================================================================

class ATSAnalysisResponse(BaseModel):
    score: int = Field(description="ATS match score from 0 to 100.")
    skills_matched: List[str] = Field(description="List of skills in the resume matching the job description.")
    skills_missing: List[str] = Field(description="List of skills in the job description missing from the resume.")
    keywords_missing: List[str] = Field(description="List of key technological buzzwords or industry terms missing.")
    recommendations: List[str] = Field(description="Actionable recommendations to improve resume match rate.")

# ===========================================================================
# Interview Question Schemas
# ===========================================================================

class QuestionResponse(BaseModel):
    id: int
    question_text: str = Field(..., alias="question")
    focus_area: str
    expected_concepts: List[str]
    difficulty: str

    class Config:
        from_attributes = True
        populate_by_name = True

class AnswerSubmit(BaseModel):
    candidate_answer: str

class AnswerEvaluationResponse(BaseModel):
    score: int
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    model_answer: str

    class Config:
        from_attributes = True

class AnswerResponse(BaseModel):
    evaluation: AnswerEvaluationResponse
    next_question: Optional[QuestionResponse] = None

# ===========================================================================
# Interview Final Report Schemas
# ===========================================================================

class FinalReportResponse(BaseModel):
    overall_score: int
    summary: str
    key_strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    topics_to_revise: List[str]
    concepts_to_strengthen: List[str]
    suggested_focus: str

    class Config:
        from_attributes = True

# ===========================================================================
# Session Detail / History Schemas
# ===========================================================================

class SessionResponse(BaseModel):
    id: int
    job_title: str
    job_description: Optional[str] = None
    ats_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionDetailResponse(BaseModel):
    id: int
    question_text: str
    focus_area: str
    expected_concepts: List[str]
    difficulty: str
    candidate_answer: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    model_answer: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SessionDetailResponse(SessionResponse):
    ats_skills_matched: Optional[List[str]] = None
    ats_skills_missing: Optional[List[str]] = None
    ats_keywords_missing: Optional[List[str]] = None
    ats_recommendations: Optional[List[str]] = None
    questions: List[QuestionDetailResponse] = []
    report: Optional[FinalReportResponse] = None

    class Config:
        from_attributes = True


class UserTopicScoreResponse(BaseModel):
    topic: str
    total_score: int
    question_count: int
    avg_score: float
    last_updated: datetime

    class Config:
        from_attributes = True


class PerformanceTrackingResponse(BaseModel):
    weak_topics: List[str]
    strong_topics: List[str]
    difficulty_level: str
    last_updated: datetime

    class Config:
        from_attributes = True


class UserPerformanceProfile(BaseModel):
    difficulty_level: str
    weak_topics: List[str]
    strong_topics: List[str]
    topic_scores: List[UserTopicScoreResponse]
    practice_suggestions: List[str]
    recommended_topics: List[str]
