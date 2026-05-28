import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.app.config import settings
from backend.app.utils.logger import logger

# ---------------------------------------------------------------------------
# Pydantic Schemas for Structured JSON Output
# ---------------------------------------------------------------------------

class ResumeAnalysis(BaseModel):
    skills: List[str] = Field(description="List of primary technical and soft skills extracted from the resume.")
    experience_summary: str = Field(description="A concise summary of the candidate's professional experience.")
    recommended_topics: List[str] = Field(description="3-5 recommended topics or areas of focus to interview the candidate on.")

class ATSAnalysisResponse(BaseModel):
    score: int = Field(description="ATS match score from 0 to 100 based on resume compatibility with job description.")
    skills_matched: List[str] = Field(description="List of skills in the resume matching the job description.")
    skills_missing: List[str] = Field(description="List of skills in the job description missing from the resume.")
    keywords_missing: List[str] = Field(description="List of key technological buzzwords or industry terms missing from the resume.")
    recommendations: List[str] = Field(description="Actionable recommendations to improve resume match rate for the job description.")

class InterviewQuestion(BaseModel):
    question: str = Field(description="The interview question for the candidate.")
    focus_area: str = Field(description="The primary focus (e.g., 'React Hooks', 'System Design', 'Behavioral').")
    expected_concepts: List[str] = Field(description="List of key concepts or terms that the candidate should cover in their answer.")
    difficulty: str = Field(description="The difficulty level of this question ('Easy', 'Medium', 'Hard').")

class AnswerEvaluation(BaseModel):
    score: int = Field(description="Score from 1 (poor) to 10 (excellent) for the candidate's response.")
    feedback: str = Field(description="Constructive critique of the answer provided by the candidate.")
    strengths: List[str] = Field(description="What parts of the answer were good.")
    weaknesses: List[str] = Field(description="What key details or concepts were missing or incorrect.")
    model_answer: str = Field(description="An exemplar response showing how a top-tier candidate would answer this question.")

class FinalReport(BaseModel):
    overall_score: int = Field(description="Overall performance score from 1 to 10.")
    summary: str = Field(description="A high-level synthesis of how the candidate performed across the whole interview.")
    key_strengths: List[str] = Field(description="Top 3 key strengths demonstrated during the interview.")
    improvement_areas: List[str] = Field(description="Top 3 areas where the candidate needs to improve.")
    recommendations: List[str] = Field(description="Actionable next steps or learning suggestions for the candidate.")

# ---------------------------------------------------------------------------
# Core LLM Service
# ---------------------------------------------------------------------------

class LLMService:
    """
    Interfaces with Google's Gemini Models using the `google-genai` SDK.
    Handles all interactions involving resume parsing, ATS scoring, adaptive
    question generation, and structured scoring.
    """

    def _get_client(self, api_key: Optional[str] = None) -> genai.Client:
        """
        Helper method to retrieve a Gemini Client.
        Prioritizes the request-specific API key, falling back to application config.
        """
        active_key = api_key or settings.gemini_api_key
        if not active_key:
            logger.error("Gemini API key is not configured.")
            raise ValueError(
                "Gemini API key is missing. Please set it in your .env file "
                "or pass it via headers from the frontend."
            )
        try:
            return genai.Client(api_key=active_key)
        except Exception as e:
            logger.error(f"Error initializing GenAI Client: {e}")
            raise RuntimeError(f"Failed to initialize Gemini API Client: {e}")

    def analyze_resume(self, resume_text: str, api_key: Optional[str] = None) -> ResumeAnalysis:
        """
        Analyzes raw resume text to extract skills, a brief experience summary,
        and recommended topics for an interview.
        """
        client = self._get_client(api_key)
        prompt = (
            "Analyze the following resume text. Extract a list of primary skills, "
            "provide a concise summary of the candidate's professional experience, "
            "and suggest 3-5 focus areas/topics to base the interview questions on.\n\n"
            f"Resume Text:\n{resume_text}"
        )

        try:
            logger.info("Calling Gemini API for resume analysis...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResumeAnalysis,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            return ResumeAnalysis(**data)
            
        except APIError as api_err:
            logger.error(f"Gemini API Error during resume analysis: {api_err}")
            raise ValueError(f"Gemini API request failed: {api_err.message}")
        except Exception as e:
            logger.error(f"Unexpected error during resume analysis: {e}")
            raise

    def analyze_resume_ats(
        self, 
        resume_text: str, 
        job_description: str, 
        api_key: Optional[str] = None
    ) -> ATSAnalysisResponse:
        """
        Performs an ATS resume optimization review against a job description.
        Matches skills, lists missing skills/keywords, and yields an ATS compatibility score.
        """
        client = self._get_client(api_key)
        prompt = (
            "You are an expert technical recruiter and ATS system analyst. "
            "Analyze the following resume text and compare it with the job description. "
            "1. Calculate an ATS match score (0-100) based on alignment of qualifications, experience, and skills.\n"
            "2. Identify skills in the resume that match the job description.\n"
            "3. List critical skills mentioned in the job description that are missing from the resume.\n"
            "4. Identify technical keywords/buzzwords from the job description that should be added to bypass filters.\n"
            "5. Provide actionable formatting, phrasing, and content suggestions to optimize the resume.\n\n"
            f"Resume Text:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}"
        )

        try:
            logger.info("Calling Gemini API for ATS Resume Profiling...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ATSAnalysisResponse,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            return ATSAnalysisResponse(**data)
            
        except APIError as api_err:
            logger.error(f"Gemini API Error during ATS analysis: {api_err}")
            raise ValueError(f"Gemini API request failed: {api_err.message}")
        except Exception as e:
            logger.error(f"Unexpected error during ATS analysis: {e}")
            raise

    def generate_question(
        self,
        job_title: str,
        job_description: str,
        resume_skills: List[str],
        history: List[Dict[str, str]],
        previous_evaluations: List[Dict[str, Any]],
        api_key: Optional[str] = None
    ) -> InterviewQuestion:
        """
        Generates the next interview question adaptively.
        Determines difficulty based on previous score averages.
        Drills down into weak topics (score < 6) if found, otherwise broadens coverage.
        """
        client = self._get_client(api_key)
        
        # 1. Calculate current average score to determine adaptive difficulty
        difficulty = "Medium"
        weak_topics = []
        
        if previous_evaluations:
            scores = [e["score"] for e in previous_evaluations if e.get("score") is not None]
            if scores:
                avg_score = sum(scores) / len(scores)
                # Adaptive difficulty thresholding
                if avg_score >= 8.0:
                    difficulty = "Hard"
                elif avg_score < 6.0:
                    difficulty = "Easy"
                else:
                    difficulty = "Medium"
            
            # Find weak areas (where score was less than 6/10)
            for eval_item in previous_evaluations:
                if eval_item.get("score") is not None and eval_item["score"] < 6:
                    weak_topics.append({
                        "question": eval_item.get("question"),
                        "focus_area": eval_item.get("focus_area"),
                        "weaknesses": eval_item.get("weaknesses", [])
                    })

        # 2. Formulate the adaptive instructions
        adaptive_guideline = ""
        if weak_topics:
            topics_desc = ", ".join([w["focus_area"] for w in weak_topics if w.get("focus_area")])
            adaptive_guideline = (
                f"ADAPTIVE LOGIC: The candidate struggled in previous questions on the following focus areas: [{topics_desc}]. "
                f"Please generate a follow-up question at the '{difficulty}' difficulty level that targets these weak technical areas "
                f"or related fundamental principles to see if they can clarify their understanding."
            )
        else:
            adaptive_guideline = (
                f"ADAPTIVE LOGIC: The candidate is performing well. Please generate a new technical or behavioral question "
                f"at the '{difficulty}' difficulty level covering a different skill listed in their resume, matching the job description."
            )

        # Build transcript context
        conversation_context = ""
        if history:
            conversation_context = "\n".join(
                [f"- {msg['role'].capitalize()}: {msg['text']}" for msg in history]
            )
        else:
            conversation_context = "No questions have been asked yet. This is the start of the interview."

        prompt = (
            f"You are a professional, polite, and technical interviewer conducting a mock interview.\n\n"
            f"Target Job Title: {job_title}\n"
            f"Target Job Description:\n{job_description}\n\n"
            f"Candidate Skills: {', '.join(resume_skills)}\n\n"
            f"Previous Interview Transcript:\n"
            f"{conversation_context}\n\n"
            f"{adaptive_guideline}\n\n"
            "Generate the next question as a valid JSON object matching the requested schema. "
            "Ensure the question aligns with the selected difficulty and focus area."
        )

        try:
            logger.info(f"Generating adaptive question (Difficulty: {difficulty}, History length: {len(history)})...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=InterviewQuestion,
                    temperature=0.7,
                )
            )
            data = json.loads(response.text)
            return InterviewQuestion(**data)
            
        except APIError as api_err:
            logger.error(f"Gemini API Error during question generation: {api_err}")
            raise ValueError(f"Gemini API request failed: {api_err.message}")
        except Exception as e:
            logger.error(f"Unexpected error during question generation: {e}")
            raise

    def evaluate_answer(
        self,
        question: str,
        expected_concepts: List[str],
        candidate_answer: str,
        api_key: Optional[str] = None
    ) -> AnswerEvaluation:
        """
        Grades a single answer provided by the candidate, showing strengths,
        weaknesses, a target grade, and a model answer.
        """
        client = self._get_client(api_key)
        prompt = (
            f"You are a mock interviewer evaluating a candidate's answer to a question.\n\n"
            f"Question: {question}\n"
            f"Expected Concepts/Keywords: {', '.join(expected_concepts)}\n"
            f"Candidate's Answer:\n{candidate_answer}\n\n"
            "Please evaluate the candidate's answer. Provide an objective score from 1 to 10, "
            "a constructive feedback summary, a list of strengths, a list of weaknesses (or missing "
            "concepts), and a clear 'model answer' demonstrating how a senior-level candidate would "
            "respond to the same question."
        )

        try:
            logger.info("Calling Gemini API for answer evaluation...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnswerEvaluation,
                    temperature=0.3,
                )
            )
            data = json.loads(response.text)
            return AnswerEvaluation(**data)
            
        except APIError as api_err:
            logger.error(f"Gemini API Error during answer evaluation: {api_err}")
            raise ValueError(f"Gemini API request failed: {api_err.message}")
        except Exception as e:
            logger.error(f"Unexpected error during answer evaluation: {e}")
            raise

    def generate_final_report(
        self,
        job_title: str,
        transcript_evaluations: List[Dict[str, Any]],
        api_key: Optional[str] = None
    ) -> FinalReport:
        """
        Aggregates all individual question evaluations to write a comprehensive performance review.
        """
        client = self._get_client(api_key)
        
        transcript_formatted = ""
        for i, item in enumerate(transcript_evaluations, 1):
            # Safe parsing
            question = item.get("question") or item.get("question_text", "")
            answer = item.get("answer") or item.get("candidate_answer", "")
            score = item.get("score", 0)
            feedback = item.get("feedback", "")
            strengths = item.get("strengths") or []
            weaknesses = item.get("weaknesses") or []
            
            transcript_formatted += (
                f"Question {i}: {question}\n"
                f"Candidate's Answer: {answer}\n"
                f"Score Given: {score}/10\n"
                f"Feedback: {feedback}\n"
                f"Strengths: {', '.join(strengths)}\n"
                f"Weaknesses: {', '.join(weaknesses)}\n"
                "--------------------\n"
            )

        prompt = (
            f"You are a senior recruitment manager summarizing a mock interview.\n\n"
            f"Target Job Role: {job_title}\n\n"
            f"Detailed Interview Logs and Grades:\n"
            f"{transcript_formatted}\n"
            "Please read the log. Aggregate the scores to form a balanced final overview. "
            "Deliver an overall score out of 10, a professional summary of the candidate's suitability "
            "for the role, their top 3 overall strengths, top 3 target areas for improvement, "
            "and direct, actionable advice or next steps to prepare for actual interviews."
        )

        try:
            logger.info("Calling Gemini API for final report generation...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FinalReport,
                    temperature=0.3,
                )
            )
            data = json.loads(response.text)
            return FinalReport(**data)
            
        except APIError as api_err:
            logger.error(f"Gemini API Error during final report generation: {api_err}")
            raise ValueError(f"Gemini API request failed: {api_err.message}")
        except Exception as e:
            logger.error(f"Unexpected error during final report generation: {e}")
            raise

# Single instance of LLMService to be imported
llm_service = LLMService()
