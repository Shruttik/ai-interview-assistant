import json
import time
import socket
import httpx
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
    topics_to_revise: List[str] = Field(description="Specific high-level topics the candidate should revise (e.g. ['DBMS', 'SQL', 'OOP']).")
    concepts_to_strengthen: List[str] = Field(description="Concrete concepts within those topics to strengthen (e.g. ['Index optimization', 'Inheritance vs Composition']).")
    suggested_focus: str = Field(description="Suggested focus for their next mock interview session.")

# ---------------------------------------------------------------------------
# Core LLM Service
# ---------------------------------------------------------------------------

class LLMService:
    """
    Interfaces with Google's Gemini Models using the `google-genai` SDK.
    Handles all interactions involving resume parsing, ATS scoring, adaptive
    question generation, and structured scoring.
    """

    def _is_quota_or_rate_limit(self, e: Exception) -> bool:
        """
        Detects if an exception is a Gemini rate limit or quota exceeded error.
        """
        err_str = str(e).lower()
        if isinstance(e, APIError):
            code = getattr(e, "code", None)
            if code == 429:
                return True
        indicators = ["429", "resourceexhausted", "quota exceeded", "rate limit", "busy", "limit exceeded"]
        return any(indicator in err_str for indicator in indicators)

    def _evaluate_answer_rules(
        self,
        question: str,
        expected_concepts: List[str],
        candidate_answer: str
    ) -> AnswerEvaluation:
        """
        Provides a basic rule-based concept matching evaluation when Gemini is unavailable.
        Scores the answer from 3 to 9 based on the percentage of expected concepts matched.
        """
        ans_lower = candidate_answer.lower()
        matched = []
        missing = []
        for concept in expected_concepts:
            if concept.lower() in ans_lower:
                matched.append(concept)
            else:
                missing.append(concept)
        
        num_concepts = len(expected_concepts)
        if num_concepts > 0:
            ratio = len(matched) / num_concepts
        else:
            ratio = 1.0
            
        score = int(3 + ratio * 6)
        if len(candidate_answer.strip()) < 10:
            score = 3
            
        feedback = "AI service is temporarily busy. Please try again later. (Performed a rule-based evaluation of your response.)"
        strengths = [f"Covered key concept: '{c}'" for c in matched] if matched else ["Submitted response for evaluation."]
        weaknesses = [f"Did not mention expected concept: '{c}'" for c in missing] if missing else ["Covered all expected concepts."]
        model_answer = "Model answer is temporarily unavailable as the AI service is busy."
        
        return AnswerEvaluation(
            score=score,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            model_answer=model_answer
        )

    def _generate_fallback_report(
        self,
        job_title: str,
        transcript_evaluations: List[Dict[str, Any]]
    ) -> FinalReport:
        """
        Generates a fallback FinalReport using basic metrics when Gemini is busy.
        """
        scores = []
        topics = []
        concepts = []
        for item in transcript_evaluations:
            score_val = item.get("score")
            if score_val is not None:
                scores.append(score_val)
            focus = item.get("focus_area")
            if focus:
                topics.append(focus)
            expected = item.get("expected_concepts") or []
            concepts.extend(expected)
            
        avg_score = round(sum(scores) / len(scores)) if scores else 5
        topics = list(set(topics)) if topics else ["General"]
        concepts = list(set(concepts)) if concepts else ["Core Concepts"]
        
        return FinalReport(
            overall_score=max(1, min(10, int(avg_score))),
            summary="AI service is temporarily busy. Please try again later. (Your final report has been compiled based on auto-aggregation of mock session scores.)",
            key_strengths=["Completed the mock interview session successfully."],
            improvement_areas=["Review and practice topics covered during the session."],
            recommendations=["Continue practicing under timed constraints to increase confidence."],
            topics_to_revise=topics[:3],
            concepts_to_strengthen=concepts[:5],
            suggested_focus="Focus on the weak areas identified during the session and practice offline."
        )

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
            
        except Exception as e:
            if self._is_quota_or_rate_limit(e):
                logger.error(f"Gemini API quota/rate-limit error during resume analysis: {e}")
                raise ValueError("AI service is temporarily busy. Please try again later.")
            elif isinstance(e, APIError):
                logger.error(f"Gemini API Error during resume analysis: {e}")
                raise ValueError(f"Gemini API request failed: {e.message}")
            else:
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
            
        except Exception as e:
            if self._is_quota_or_rate_limit(e):
                logger.error(f"Gemini API quota/rate-limit error during ATS analysis: {e}")
                raise ValueError("AI service is temporarily busy. Please try again later.")
            elif isinstance(e, APIError):
                logger.error(f"Gemini API Error during ATS analysis: {e}")
                raise ValueError(f"Gemini API request failed: {e.message}")
            else:
                logger.error(f"Unexpected error during ATS analysis: {e}")
                raise

    def generate_question(
        self,
        job_title: str,
        job_description: str,
        resume_skills: List[str],
        history: List[Dict[str, str]],
        previous_evaluations: List[Dict[str, Any]],
        weak_topics: Optional[List[str]] = None,
        strong_topics: Optional[List[str]] = None,
        api_key: Optional[str] = None
    ) -> InterviewQuestion:
        """
        Generates the next interview question adaptively.
        Determines difficulty based on previous score averages.
        Prioritizes weak topics (score < 6 or tracked in weak_topics) and avoids strong topics.
        Enforces strict anti-redundancy checks to ensure distinct questions.
        """
        client = self._get_client(api_key)
        
        # 1. Calculate current average score to determine adaptive difficulty
        difficulty = "Medium"
        session_weak_topics = []
        
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
            
            # Find weak areas in the current session
            for eval_item in previous_evaluations:
                if eval_item.get("score") is not None and eval_item["score"] < 6:
                    if eval_item.get("focus_area"):
                        session_weak_topics.append(eval_item["focus_area"])

        # Combine tracked weak topics with session-specific weak topics
        active_weak_topics = list(set((weak_topics or []) + session_weak_topics))
        active_strong_topics = strong_topics or []

        # 2. Formulate the adaptive instructions
        adaptive_guideline = f"ADAPTIVE DIFFICULTY LEVEL: {difficulty}\n"
        if active_weak_topics:
            topics_desc = ", ".join(active_weak_topics)
            adaptive_guideline += (
                f"ADAPTIVE TOPIC SELECTION: The candidate has demonstrated weaknesses in: [{topics_desc}]. "
                f"Generate a question at the '{difficulty}' level that tests one of these weak areas (or a related concept) "
                f"to check for improvement. Focus about 60% of your selection probability on these areas."
            )
        else:
            adaptive_guideline += (
                f"ADAPTIVE TOPIC SELECTION: The candidate is performing well. Generate a new question "
                f"at the '{difficulty}' level testing a new topic from their resume skills or the job description."
            )

        if active_strong_topics:
            strong_desc = ", ".join(active_strong_topics)
            adaptive_guideline += f"\nAvoid testing areas where the candidate is already highly proficient: [{strong_desc}]."

        # Extract previously asked questions to prevent duplication
        asked_questions = [h["text"] for h in history if h.get("role") == "interviewer"]
        anti_redundancy_block = ""
        if asked_questions:
            questions_list_str = "\n".join([f"- {q}" for q in asked_questions])
            anti_redundancy_block = (
                "CRITICAL ANTI-REDUNDANCY REQUIREMENT:\n"
                "You MUST NOT generate any question that matches, duplicates, or closely resembles the topics, "
                "structures, or technical angles of any questions already asked in this session. "
                "Here are the previously asked questions:\n"
                f"{questions_list_str}\n"
                "Please generate a fresh, distinct question testing a different technical concept or behavioral scenario."
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
            f"{anti_redundancy_block}\n\n"
            "Generate the next question as a valid JSON object matching the requested schema. "
            "Ensure the question is creative, professional, and strictly different from the previous questions."
        )

        attempts = 3
        backoff_sec = 2
        
        # Predefined fallback questions to continue session under network failure
        fallback_questions = [
            InterviewQuestion(
                question="Explain the difference between SQL and NoSQL databases, and when you would use each.",
                focus_area="DBMS",
                expected_concepts=["SQL", "NoSQL", "ACID", "Schema", "Scaling"],
                difficulty="Medium"
            ),
            InterviewQuestion(
                question="Explain the key principles of Object-Oriented Programming (OOP) and give examples of each.",
                focus_area="OOP",
                expected_concepts=["Encapsulation", "Inheritance", "Polymorphism", "Abstraction"],
                difficulty="Medium"
            ),
            InterviewQuestion(
                question="What is a RESTful API? What are the main HTTP methods and their usage?",
                focus_area="REST API Design",
                expected_concepts=["GET", "POST", "PUT", "DELETE", "Statelessness", "Resources"],
                difficulty="Medium"
            ),
            InterviewQuestion(
                question="Describe how a Hash Map works internally, including collision handling.",
                focus_area="DSA",
                expected_concepts=["Hash function", "Collision", "Chaining", "Open Addressing", "O(1) time complexity"],
                difficulty="Medium"
            )
        ]

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"Generating adaptive question (Difficulty: {difficulty}, History length: {len(history)}, attempt {attempt}/{attempts})...")
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
            except Exception as e:
                is_quota = self._is_quota_or_rate_limit(e)
                if is_quota:
                    logger.error(f"Gemini API quota/rate-limit error during question generation: {e}")
                else:
                    logger.warning(
                        f"Gemini API question generation attempt {attempt} failed with error: {e}. "
                        f"Diagnostics: Error type={type(e).__name__}, args={e.args}"
                    )
                
                # Check for network/DNS failures
                err_str = str(e)
                is_network = any(phrase in err_str for phrase in ["getaddrinfo", "unreachable", "Name or service not known", "Connection refused"])
                is_network = is_network or isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError, socket.gaierror))
                
                if is_network:
                    logger.error(f"Detected DNS/network connectivity failure during question generation: {e}")
                
                if attempt < attempts:
                    sleep_time = backoff_sec ** attempt
                    logger.info(f"Retrying question generation in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All 3 attempts to generate question via Gemini failed. Returning fallback question. Last error: {e}")
                    # Select fallback question based on length of history to avoid duplicates
                    asked_count = len([h for h in history if h.get("role") == "interviewer"])
                    fallback_base = fallback_questions[asked_count % len(fallback_questions)]
                    fallback_q = InterviewQuestion(
                        question=f"For the role of {job_title}: {fallback_base.question}",
                        focus_area=fallback_base.focus_area,
                        expected_concepts=fallback_base.expected_concepts,
                        difficulty=fallback_base.difficulty
                    )
                    return fallback_q

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

        attempts = 3
        backoff_sec = 2

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"Calling Gemini API for answer evaluation (attempt {attempt}/{attempts})...")
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
            except Exception as e:
                is_quota = self._is_quota_or_rate_limit(e)
                if is_quota:
                    logger.error(f"Gemini API quota/rate-limit error during answer evaluation: {e}")
                else:
                    logger.warning(
                        f"Gemini API answer evaluation attempt {attempt} failed with error: {e}. "
                        f"Diagnostics: Error type={type(e).__name__}, args={e.args}"
                    )
                
                # Check for network/DNS failures
                err_str = str(e)
                is_network = any(phrase in err_str for phrase in ["getaddrinfo", "unreachable", "Name or service not known", "Connection refused"])
                is_network = is_network or isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError, socket.gaierror))
                
                if is_network:
                    logger.error(f"Detected DNS/network connectivity failure during answer evaluation: {e}")
                
                if attempt < attempts:
                    sleep_time = backoff_sec ** attempt
                    logger.info(f"Retrying answer evaluation in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All 3 attempts to evaluate answer via Gemini failed. Calling rule-based fallback evaluation. Last error: {e}")
                    return self._evaluate_answer_rules(question, expected_concepts, candidate_answer)

    def generate_final_report(
        self,
        job_title: str,
        transcript_evaluations: List[Dict[str, Any]],
        api_key: Optional[str] = None
    ) -> FinalReport:
        """
        Aggregates all individual question evaluations to write a comprehensive performance review.
        Suggests key revision topics, concepts to strengthen, and next focus areas.
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
            "and direct, actionable advice or next steps to prepare for actual interviews. "
            "Additionally, you must output:\n"
            "1. topics_to_revise: A list of 2-4 core subject areas (like 'OOP', 'SQL', 'DBMS', 'Operating Systems', 'Computer Networks', 'DSA', 'Python', 'Java') where performance was weak or incomplete.\n"
            "2. concepts_to_strengthen: A list of 3-5 specific, concrete concepts within those topics they should review (e.g. ['Index structures', 'Garbage collection', 'Polymorphism']).\n"
            "3. suggested_focus: A single sentence recommending the focus of their next interview session based on their weakest topics."
        )

        attempts = 3
        backoff_sec = 2

        for attempt in range(1, attempts + 1):
            try:
                logger.info(f"Calling Gemini API for final report generation (attempt {attempt}/{attempts})...")
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
            except Exception as e:
                is_quota = self._is_quota_or_rate_limit(e)
                if is_quota:
                    logger.error(f"Gemini API quota/rate-limit error during final report generation: {e}")
                else:
                    logger.warning(
                        f"Gemini API final report generation attempt {attempt} failed with error: {e}. "
                        f"Diagnostics: Error type={type(e).__name__}, args={e.args}"
                    )
                
                # Check for network/DNS failures
                err_str = str(e)
                is_network = any(phrase in err_str for phrase in ["getaddrinfo", "unreachable", "Name or service not known", "Connection refused"])
                is_network = is_network or isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError, socket.gaierror))
                
                if is_network:
                    logger.error(f"Detected DNS/network connectivity failure during final report generation: {e}")
                
                if attempt < attempts:
                    sleep_time = backoff_sec ** attempt
                    logger.info(f"Retrying final report generation in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All 3 attempts to generate final report via Gemini failed. Returning fallback report. Last error: {e}")
                    return self._generate_fallback_report(job_title, transcript_evaluations)

# Single instance of LLMService to be imported
llm_service = LLMService()
