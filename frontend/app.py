import os
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Interview Coach & ATS Optimizer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Visual Themes & CSS Injector (Aesthetics & Premium Polish) - Force Dark Theme
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

/* Force Dark Theme globally */
.stApp {
    background-color: #0b130e !important;
    color: #f1f5f3 !important;
}

html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #0f1c15 !important;
    border-right: 1px solid #1a2f24 !important;
}
[data-testid="stSidebar"] .stMarkdown, 
[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] label, 
[data-testid="stSidebar"] span {
    color: #cbd5e1 !important;
}

/* Titles and Headers */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f3 !important;
    font-weight: 700 !important;
}

/* Gradient Header Title */
.gradient-text {
    background: linear-gradient(90deg, #10b981, #34d399, #059669);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.8rem;
    margin-bottom: 0.2rem;
    text-align: center;
}

.gradient-subtext {
    font-size: 1.15rem;
    color: #94a3b8;
    text-align: center;
    margin-bottom: 1.8rem;
}

/* Custom styled Card containers (and Streamlit border blocks) */
.premium-card, div[data-testid="stVerticalBlockBorder"] {
    background: #0f1c15 !important;
    border: 1px solid #1a2f24 !important;
    border-radius: 16px !important;
    padding: 24px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.premium-card:hover, div[data-testid="stVerticalBlockBorder"]:hover {
    border-color: rgba(16, 185, 129, 0.4) !important;
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.15) !important;
    transform: translateY(-2px);
}

/* Badge highlights */
.concept-tag {
    display: inline-block;
    background-color: rgba(16, 185, 129, 0.15) !important;
    color: #34d399 !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.82rem;
    margin-right: 6px;
    margin-bottom: 6px;
    font-weight: 500;
}

.difficulty-easy {
    background-color: rgba(52, 211, 153, 0.15) !important;
    color: #34d399 !important;
    border: 1px solid rgba(52, 211, 153, 0.3) !important;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.8rem;
    font-weight: 600;
}

.difficulty-medium {
    background-color: rgba(245, 158, 11, 0.15) !important;
    color: #fbbf24 !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.8rem;
    font-weight: 600;
}

.difficulty-hard {
    background-color: rgba(239, 68, 68, 0.15) !important;
    color: #f87171 !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Large Score display circle */
.score-circle-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 20px 0;
}

.score-circle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 130px;
    height: 130px;
    border-radius: 50%;
    background: linear-gradient(135deg, #059669, #10b981);
    color: white !important;
    font-size: 3.2rem;
    font-weight: 800;
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
    position: relative;
    transition: transform 0.3s ease;
}

.score-circle:hover {
    transform: scale(1.05) rotate(3deg);
}

.score-label {
    margin-top: 12px;
    font-size: 1rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Success/Strength items list */
.strength-item {
    border-left: 4px solid #10b981;
    background: rgba(16, 185, 129, 0.08) !important;
    color: #a7f3d0 !important;
    padding: 10px 16px;
    margin-bottom: 8px;
    border-radius: 0 8px 8px 0;
    font-size: 0.95rem;
    font-weight: 500;
}

.weakness-item {
    border-left: 4px solid #f59e0b;
    background: rgba(245, 158, 11, 0.08) !important;
    color: #fde68a !important;
    padding: 10px 16px;
    margin-bottom: 8px;
    border-radius: 0 8px 8px 0;
    font-size: 0.95rem;
    font-weight: 500;
}

/* Form inputs overrides */
.stTextInput>div>div>input, 
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input,
.stSelectbox>div>div>div {
    background-color: #0f1c15 !important;
    border: 1px solid #1a2f24 !important;
    color: #f1f5f3 !important;
    border-radius: 8px !important;
}

.stTextInput>div>div>input:focus, 
.stTextArea>div>div>textarea:focus,
.stNumberInput>div>div>input:focus {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.4) !important;
}

/* Button UI styling updates */
div.stButton > button {
    background: linear-gradient(90deg, #059669, #10b981) !important;
    color: white !important;
    border: none !important;
    padding: 10px 20px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #047857, #059669) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3) !important;
    transform: translateY(-1.5px) !important;
}

/* Tabs override */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    background-color: #0f1c15 !important;
    border: 1px solid #1a2f24 !important;
    border-radius: 8px 8px 0px 0px !important;
    padding: 8px 20px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #10b981 !important;
    border-color: #1a2f24 !important;
}

.stTabs [aria-selected="true"] {
    background-color: #1a2f24 !important;
    color: #34d399 !important;
    border-color: #10b981 #10b981 transparent #10b981 !important;
    border-bottom: 3px solid #10b981 !important;
}

/* File uploader styling */
[data-testid="stFileUploader"] {
    background-color: #0f1c15 !important;
    border: 1px dashed #1a2f24 !important;
    border-radius: 12px !important;
    padding: 15px !important;
}

/* Progress bar override */
div[data-testid="stProgress"] > div > div > div {
    background-color: #10b981 !important;
}

/* Ensure all main markdown text has clear visibility and high contrast */
.stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
    color: #cbd5e1 !important;
}

/* Enforce light green on widget labels */
label[data-testid="stWidgetLabel"], .stWidgetLabel p {
    color: #e2ece9 !important;
    font-weight: 600 !important;
}

/* Enforce high-contrast text on expanders */
.streamlit-expanderHeader p {
    color: #f1f5f3 !important;
    font-weight: 600 !important;
}

/* Enforce visibility on alert descriptions */
div[data-testid="stAlert"] {
    background-color: #0f1c15 !important;
    border-radius: 8px !important;
    border: 1px solid #1a2f24 !important;
}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] span {
    color: #f1f5f3 !important;
}

/* Force dropdown options text colors */
div[data-baseweb="select"] div {
    color: #f1f5f3 !important;
}

/* Fix tabs text inside p tags inheriting parent colors */
.stTabs [data-baseweb="tab"] p {
    color: inherit !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Config & API Parameters
# ---------------------------------------------------------------------------
# Try to get BACKEND_URL from Streamlit secrets first, then environment variables, falling back to the Render URL
BACKEND_URL = None
try:
    if "BACKEND_URL" in st.secrets:
        BACKEND_URL = st.secrets["BACKEND_URL"]
except Exception:
    pass

if not BACKEND_URL:
    BACKEND_URL = os.getenv("BACKEND_URL")

if not BACKEND_URL:
    BACKEND_URL = "https://ai-interview-assistant-6nr6.onrender.com"

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
# Auth State
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

# Mock Interview State
if "interview_session_id" not in st.session_state:
    st.session_state.interview_session_id = None
if "interview_state" not in st.session_state:
    st.session_state.interview_state = "setup"  # setup, active, completed
if "resume_skills" not in st.session_state:
    st.session_state.resume_skills = []
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "question_number" not in st.session_state:
    st.session_state.question_number = 0
if "max_questions" not in st.session_state:
    st.session_state.max_questions = 5
if "session_evaluations" not in st.session_state:
    st.session_state.session_evaluations = []
if "final_report" not in st.session_state:
    st.session_state.final_report = None

# Active selected job fields
if "job_title" not in st.session_state:
    st.session_state.job_title = ""
if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""

# ---------------------------------------------------------------------------
# Helper Methods
# ---------------------------------------------------------------------------
def get_auth_headers():
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    if st.session_state.api_key:
        headers["X-Gemini-API-Key"] = st.session_state.api_key
    return headers

def perform_logout():
    st.session_state.token = None
    st.session_state.user_email = ""
    reset_interview_variables()

def reset_interview_variables():
    st.session_state.interview_session_id = None
    st.session_state.interview_state = "setup"
    st.session_state.resume_skills = []
    st.session_state.current_question = None
    st.session_state.question_number = 0
    st.session_state.session_evaluations = []
    st.session_state.final_report = None

# ---------------------------------------------------------------------------
# Sidebar UI (Key settings & Logout)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ System Settings")
    
    # Custom Gemini Key override
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Provide your Gemini API key. Defaults to system .env value if left blank."
    )
    if api_key_input:
        st.session_state.api_key = api_key_input
        
    st.markdown("---")
    
    if st.session_state.token:
        st.markdown(f"👤 **Logged in as:**\n`{st.session_state.user_email}`")
        if st.button("🚪 Logout Session", use_container_width=True):
            perform_logout()
            st.rerun()
    else:
        st.markdown("🔒 **Account Locked**\nSign in to synchronize sessions and save scorecard histories.")
        
    st.markdown("---")
    st.markdown(
        """
        <div style='font-size: 0.85rem; color: #64748b; text-align: center;'>
        <b>AI Interview Coach v2.0</b><br>
        SQLite | JWT | Adaptive Q&A
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------------
# Auth Flow View (Sign In / Register)
# ---------------------------------------------------------------------------
if not st.session_state.token:
    st.markdown("<div class='gradient-text'>AI Interview Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='gradient-subtext'>Sign up or sign in to start practicing customized interviews</div>", unsafe_allow_html=True)
    
    col_auth, _ = st.columns([1, 1], gap="large")
    with col_auth:
        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])
        
        with tab_login:
            login_email = st.text_input("Email Address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_pw")
            if st.button("Access Dashboard", use_container_width=True):
                if not login_email or not login_password:
                    st.error("Please enter email and password.")
                else:
                    with st.spinner("Authenticating credentials..."):
                        try:
                            resp = requests.post(
                                f"{BACKEND_URL}/api/auth/token",
                                data={"username": login_email, "password": login_password}
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                st.session_state.token = data["access_token"]
                                st.session_state.user_email = login_email
                                st.success("Access Granted! Loading workspace...")
                                st.rerun()
                            else:
                                err = resp.json().get("detail", "Authentication failed.")
                                st.error(err)
                        except Exception as e:
                            st.error(f"Cannot connect to API server: {e}")
                            
        with tab_register:
            reg_email = st.text_input("Email Address", key="reg_email")
            reg_password = st.text_input("Password (min 6 chars)", type="password", key="reg_pw")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.button("Register Account", use_container_width=True):
                if not reg_email or not reg_password:
                    st.error("Please provide email and password details.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif len(reg_password) > 128:
                    st.error("Password must be 128 characters or fewer.")
                else:
                    with st.spinner("Creating account details..."):
                        try:
                            resp = requests.post(
                                f"{BACKEND_URL}/api/auth/register",
                                json={"email": reg_email, "password": reg_password}
                            )
                            if resp.status_code == 201:
                                st.success("Registration complete! Please Sign In in the left tab.")
                            else:
                                err = resp.json().get("detail", "Registration failed.")
                                st.error(err)
                        except Exception as e:
                            st.error(f"Cannot connect to server: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Authenticated Main Workspace Layout
# ---------------------------------------------------------------------------
st.markdown("<div class='gradient-text'>AI Interview Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='gradient-subtext'>Interactive mock interviews, ATS resume profiling, and dashboard scoring insights</div>", unsafe_allow_html=True)

tab_coach, tab_ats, tab_history = st.tabs([
    "🎯 Interview Coach", 
    "📈 ATS Resume Optimizer", 
    "📜 History & Performance Insights"
])

# ---------------------------------------------------------------------------
# TAB 1: INTERVIEW COACH (MOCK SIMULATOR)
# ---------------------------------------------------------------------------
with tab_coach:
    
    # CASE A: SETUP PHASE
    if st.session_state.interview_state == "setup":
        st.markdown("### 📝 Configure Mock Interview Session")
        
        col1, col2 = st.columns(2, gap="large")
        with col1:
            with st.container(border=True):
                st.markdown("##### 💼 Job Specifics")
                job_title = st.text_input(
                    "Target Job Title",
                    placeholder="e.g. Senior Backend Developer, Data Scientist",
                    value=st.session_state.job_title
                )
                job_desc = st.text_area(
                    "Job Description",
                    placeholder="Paste key role requirements to customize generated questions...",
                    height=180,
                    value=st.session_state.job_desc
                )
            
        with col2:
            with st.container(border=True):
                st.markdown("##### 📄 Resume Upload")
                uploaded_resume = st.file_uploader(
                    "Upload Resume (PDF or TXT formats)",
                    type=["pdf", "txt"],
                    key="coach_resume_upload"
                )
                
                st.markdown("##### ⏱️ Interview Length")
                max_q = st.number_input(
                    "Number of Interview Questions",
                    min_value=3,
                    max_value=25,
                    value=st.session_state.max_questions
                )
            
        if st.button("🚀 Begin Interview Simulation", use_container_width=True):
            if not job_title:
                st.error("Please supply a Target Job Title.")
            elif not uploaded_resume:
                st.error("Please upload your resume file.")
            elif not st.session_state.api_key:
                st.error("Gemini API key is not configured. Please supply it in the sidebar.")
            else:
                with st.spinner("Uploading resume and analyzing skills..."):
                    try:
                        # Call start endpoint (Multipart form-data)
                        files = {"file": (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
                        data = {
                            "job_title": job_title,
                            "job_description": job_desc,
                            "max_questions": max_q
                        }
                        
                        resp = requests.post(
                            f"{BACKEND_URL}/api/interview/session/start",
                            files=files,
                            data=data,
                            headers=get_auth_headers()
                        )
                        
                        if resp.status_code == 200:
                            session_data = resp.json()
                            
                            st.session_state.interview_session_id = session_data["session_id"]
                            st.session_state.resume_skills = session_data["resume_analysis"]["skills"]
                            st.session_state.current_question = session_data["first_question"]
                            st.session_state.question_number = 1
                            st.session_state.max_questions = max_q
                            st.session_state.job_title = job_title
                            st.session_state.job_desc = job_desc
                            
                            st.session_state.interview_state = "active"
                            st.success("Session configured successfully! Let's start.")
                            st.rerun()
                        else:
                            err = resp.json().get("detail", "Error starting session.")
                            st.error(f"Error: {err}")
                    except Exception as e:
                        st.error(f"Connection failure: {e}")
                        
    # CASE B: ACTIVE INTERVIEWING PHASE
    elif st.session_state.interview_state == "active":
        q_num = st.session_state.question_number
        max_q = st.session_state.max_questions
        current_q = st.session_state.current_question
        
        st.markdown(f"### 💬 Question {q_num} of {max_q}")
        st.progress(q_num / max_q)
        
        # Display Question Card
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown(f"#### **Q: {current_q['question']}**")
        
        st.markdown("##### Core Concepts to target:")
        for tag in current_q['expected_concepts']:
            st.markdown(f"<span class='concept-tag'>{tag}</span>", unsafe_allow_html=True)
            
        # Display Difficulty Badge
        diff = current_q.get("difficulty", "Medium")
        diff_class = f"difficulty-{diff.lower()}"
        st.markdown(
            f"<span style='float: right; margin-top: -30px;'>Difficulty: <span class='{diff_class}'>{diff}</span></span>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='clear: both;'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Text Area Answer
        ans_text = st.text_area(
            "Type your answer response here:",
            placeholder="Focus on technical clarity, structure, and direct experience references...",
            height=200,
            key=f"active_ans_field_{q_num}"
        )
        
        col_s1, col_s2 = st.columns([1, 6])
        with col_s1:
            submit_ans = st.button("Submit Answer", use_container_width=True)
        with col_s2:
            skip_ans = st.button("Skip Question")
            
        if submit_ans or skip_ans:
            final_ans = "Candidate skipped this question." if skip_ans else ans_text.strip()
            if not final_ans and not skip_ans:
                st.warning("Please type an answer before submitting.")
            else:
                with st.spinner("Scoring response and updating history..."):
                    try:
                        session_id = st.session_state.interview_session_id
                        resp = requests.post(
                            f"{BACKEND_URL}/api/interview/session/{session_id}/answer",
                            json={"candidate_answer": final_ans},
                            headers=get_auth_headers()
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            evaluation = data["evaluation"]
                            
                            # Log answer evaluation
                            st.session_state.session_evaluations.append({
                                "question": current_q['question'],
                                "answer": final_ans,
                                "score": evaluation["score"],
                                "feedback": evaluation["feedback"],
                                "strengths": evaluation["strengths"],
                                "weaknesses": evaluation["weaknesses"],
                                "model_answer": evaluation["model_answer"]
                            })
                            
                            # Shift to next question or complete
                            next_q = data["next_question"]
                            if next_q:
                                st.session_state.current_question = next_q
                                st.session_state.question_number += 1
                                st.rerun()
                            else:
                                st.session_state.interview_state = "completed"
                                st.rerun()
                        else:
                            err = resp.json().get("detail", "Error submitting answer.")
                            st.error(f"Error: {err}")
                    except Exception as e:
                        st.error(f"API Error: {e}")

    # CASE C: COMPLETED / SUMMARY REPORT PHASE
    elif st.session_state.interview_state == "completed":
        session_id = st.session_state.interview_session_id
        
        # Pull or compile final report
        if st.session_state.final_report is None:
            with st.spinner("Compiling evaluations and generating your comprehensive scorecard..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/api/interview/session/{session_id}/finalize",
                        headers=get_auth_headers()
                    )
                    if resp.status_code == 200:
                        st.session_state.final_report = resp.json()
                        st.rerun()
                    else:
                        st.error("Failed to compile final report scorecard.")
                        st.stop()
                except Exception as e:
                    st.error(f"Connection error: {e}")
                    st.stop()
                    
        report = st.session_state.final_report
        
        # Display Final Scorecard Report
        col_c1, col_c2 = st.columns([1, 2], gap="large")
        with col_c1:
            st.markdown("<div class='premium-card' style='text-align: center;'>", unsafe_allow_html=True)
            st.markdown("#### Performance Rating")
            st.markdown(
                f"""
                <div class='score-circle-container'>
                    <div class='score-circle'>{report['overall_score']}<span style='font-size:1.5rem; vertical-align:super;'>/10</span></div>
                    <div class='score-label'>Overall Score</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            avg_score = sum([q["score"] for q in st.session_state.session_evaluations]) / len(st.session_state.session_evaluations)
            st.markdown(f"**Average Question Score:** {avg_score:.1f} / 10.0")
            st.markdown(f"**Completed Questions:** {len(st.session_state.session_evaluations)}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_c2:
            st.markdown("<div class='premium-card' style='height: 100%;'>", unsafe_allow_html=True)
            st.markdown("#### Executive Summary")
            st.write(report['summary'])
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Performance trend chart
        st.markdown("### 📊 Question Score Trend")
        q_scores = [q["score"] for q in st.session_state.session_evaluations]
        chart_data = pd.DataFrame({
            "Question": [f"Q{i}" for i in range(1, len(q_scores) + 1)],
            "Score": q_scores
        }).set_index("Question")
        st.bar_chart(chart_data)
        
        st.markdown("---")
        
        # Strengths & Weaknesses
        col_str, col_imp = st.columns(2, gap="medium")
        with col_str:
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown("#### ✅ Top Key Strengths")
            for strength in report['key_strengths']:
                st.markdown(f"<div class='strength-item'>💡 {strength}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_imp:
            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Areas for Improvement")
            for area in report['improvement_areas']:
                st.markdown(f"<div class='weakness-item'>⚠️ {area}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Recommendations
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("#### 🚀 Actionable Coach Recommendations")
        for rec in report['recommendations']:
            st.write(f"- {rec}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # AI Adaptive Recommendations
        col_rec1, col_rec2 = st.columns(2, gap="medium")
        with col_rec1:
            st.markdown("<div class='premium-card' style='height: 100%;'>", unsafe_allow_html=True)
            st.markdown("#### 📚 Recommended Topics to Revise")
            if report.get('topics_to_revise'):
                for topic in report.get('topics_to_revise', []):
                    st.markdown(f"<span class='concept-tag' style='background-color: rgba(239, 68, 68, 0.12); color: #f87171; border-color: rgba(239, 68, 68, 0.25);'>{topic}</span>", unsafe_allow_html=True)
            else:
                st.write("*No revision topics specified.*")
            
            st.markdown("##### Concepts to Strengthen:")
            if report.get('concepts_to_strengthen'):
                for concept in report.get('concepts_to_strengthen', []):
                    st.markdown(f"<div class='weakness-item' style='border-left-color: #ef4444; background: rgba(239, 68, 68, 0.04);'>🔍 {concept}</div>", unsafe_allow_html=True)
            else:
                st.write("*No concepts specified.*")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_rec2:
            st.markdown("<div class='premium-card' style='height: 100%;'>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Focus for Next Mock Session")
            st.write(report.get('suggested_focus', 'Practice more to get tailor-made revision advice.'))
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📝 Detailed Question Log")
        
        for idx, qa in enumerate(st.session_state.session_evaluations, 1):
            with st.expander(f"Question {idx} Summary (Score: {qa['score']}/10)"):
                st.markdown(f"##### **Q: {qa['question']}**")
                st.info(f"**Your Answer:** {qa['answer']}")
                
                col_qa_str, col_qa_weak = st.columns(2)
                with col_qa_str:
                    st.markdown("**Strengths Identified:**")
                    for s in qa['strengths']:
                        st.markdown(f"- {s}")
                with col_qa_weak:
                    st.markdown("**Weaknesses / Missed Details:**")
                    for w in qa['weaknesses']:
                        st.markdown(f"- {w}")
                        
                st.markdown(f"**Coaching Feedback:** {qa['feedback']}")
                st.markdown("---")
                st.success(f"**Model Answer Reference:**\n{qa['model_answer']}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Try Another Interview Setup", use_container_width=True):
            reset_interview_variables()
            st.rerun()

# ---------------------------------------------------------------------------
# TAB 2: ATS RESUME OPTIMIZER
# ---------------------------------------------------------------------------
with tab_ats:
    st.markdown("### 🔍 ATS Resume Audit & Skill Gap Analysis")
    
    col_ats1, col_ats2 = st.columns([1, 1], gap="large")
    with col_ats1:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("##### 💼 Role Specifics")
        ats_title = st.text_input("Job Title", placeholder="e.g. Lead Frontend Developer", key="ats_title_input")
        ats_desc = st.text_area("Full Job Description text", placeholder="Paste job descriptions here...", height=200, key="ats_desc_input")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_ats2:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("##### 📄 Resume File")
        ats_file = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"], key="ats_resume_uploader")
        st.markdown("</div>", unsafe_allow_html=True)
        
    if st.button("Analyze ATS Compatibility Score", use_container_width=True):
        if not ats_title or not ats_desc:
            st.error("Please provide both Job Title and Job Description.")
        elif not ats_file:
            st.error("Please upload your resume file.")
        else:
            with st.spinner("Analyzing resume against Job Description guidelines..."):
                try:
                    files = {"file": (ats_file.name, ats_file.getvalue(), ats_file.type)}
                    data = {"job_title": ats_title, "job_description": ats_desc}
                    
                    resp = requests.post(
                        f"{BACKEND_URL}/api/interview/resume/ats-analyze",
                        files=files,
                        data=data,
                        headers=get_auth_headers()
                    )
                    
                    if resp.status_code == 200:
                        ats_report = resp.json()
                        
                        st.markdown("---")
                        col_score, col_details = st.columns([1, 2], gap="large")
                        
                        with col_score:
                            st.markdown("<div class='premium-card' style='text-align: center;'>", unsafe_allow_html=True)
                            st.markdown("##### ATS Compatibility Rating")
                            st.markdown(
                                f"""
                                <div class='score-circle-container'>
                                    <div class='score-circle'>{ats_report['score']}<span style='font-size:1.5rem; vertical-align:super;'>%</span></div>
                                    <div class='score-label'>Match Rate</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        with col_details:
                            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                            st.markdown("##### 🚀 Key Recommendations")
                            for rec in ats_report['recommendations']:
                                st.write(f"- {rec}")
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        st.markdown("---")
                        
                        # Match & Missing Skills grid
                        col_matched, col_missing = st.columns(2)
                        with col_matched:
                            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                            st.markdown("##### ✅ Skills Found in Resume")
                            for skill in ats_report['skills_matched']:
                                st.markdown(f"<div class='strength-item'>🔹 {skill}</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        with col_missing:
                            st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                            st.markdown("##### ⚠️ Missing Core Skills")
                            for skill in ats_report['skills_missing']:
                                st.markdown(f"<div class='weakness-item'>🔸 {skill}</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        # Keywords missing tag cloud
                        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                        st.markdown("##### 🏷️ Recommended Keywords to Add (Bypass ATS Filters)")
                        for keyword in ats_report['keywords_missing']:
                            st.markdown(f"<span class='concept-tag'>{keyword}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    else:
                        err = resp.json().get("detail", "Error compiling ATS report.")
                        st.error(f"Error: {err}")
                except Exception as e:
                    st.error(f"Connection failure: {e}")

# ---------------------------------------------------------------------------
# TAB 3: HISTORY & INSIGHTS PORTAL
# ---------------------------------------------------------------------------
with tab_history:
    st.markdown("<div class='gradient-text' style='font-size: 2rem;'>Performance & History Insights</div>", unsafe_allow_html=True)
    
    # Reload button
    if st.button("🔄 Sync History", key="sync_history_btn"):
        st.rerun()
        
    # 1. FETCH AND RENDER PERFORMANCE PROFILE
    try:
        profile_resp = requests.get(
            f"{BACKEND_URL}/api/performance/profile",
            headers=get_auth_headers()
        )
        if profile_resp.status_code == 200:
            profile_data = profile_resp.json()
            st.markdown("### 📈 Your Performance Profile")
            
            p_col1, p_col2, p_col3 = st.columns(3, gap="medium")
            with p_col1:
                with st.container(border=True):
                    diff_lvl = profile_data.get("difficulty_level", "Beginner")
                    if diff_lvl == "Advanced":
                        diff_style = "color: #f87171; font-weight: bold; font-size: 1.8rem;"
                    elif diff_lvl == "Intermediate":
                        diff_style = "color: #fbbf24; font-weight: bold; font-size: 1.8rem;"
                    else:
                        diff_style = "color: #34d399; font-weight: bold; font-size: 1.8rem;"
                    st.markdown(
                        f"""
                        <div style='text-align: center;'>
                            <h5 style='margin:0;'>Adaptive Difficulty</h5>
                            <div style='margin-top: 15px; {diff_style}'>{diff_lvl}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
            with p_col2:
                with st.container(border=True):
                    st.markdown("##### 💪 Strongest Topics")
                    strongs = profile_data.get("strong_topics", [])
                    if strongs:
                        tags_html = "".join([f"<span class='concept-tag' style='background-color: rgba(16, 185, 129, 0.12); color: #34d399; border-color: rgba(16, 185, 129, 0.25);'>{s}</span>" for s in strongs])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.write("*No strong areas established yet.*")
                
            with p_col3:
                with st.container(border=True):
                    st.markdown("##### ⚠️ Weakest Topics")
                    weaks = profile_data.get("weak_topics", [])
                    if weaks:
                        tags_html = "".join([f"<span class='concept-tag' style='background-color: rgba(239, 68, 68, 0.12); color: #f87171; border-color: rgba(239, 68, 68, 0.25);'>{w}</span>" for w in weaks])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.write("*No weak areas detected yet! Keep practicing.*")
                
            topic_scores = profile_data.get("topic_scores", [])
            if topic_scores:
                st.markdown("##### 📊 Topic-wise Score Breakdown")
                t_names = [ts["topic"] for ts in topic_scores]
                t_avgs = [ts["avg_score"] for ts in topic_scores]
                
                chart_df = pd.DataFrame({
                    "Topic": t_names,
                    "Average Score": t_avgs
                }).set_index("Topic")
                st.bar_chart(chart_df)
            else:
                st.info("Complete an interview session to see your topic-wise score breakdown.")

            with st.container(border=True):
                st.markdown("##### 🚀 Personalized Practice & Revision Plan")
                suggestions = profile_data.get("practice_suggestions", [])
                for sug in suggestions:
                    st.markdown(f"- {sug}")
            
            st.markdown("---")
            
        else:
            st.error("Failed to load your performance profile.")
    except Exception as e:
        st.error(f"Cannot load performance profile: {e}")

    # 2. RENDER PAST SESSIONS HISTORY LOG
    st.markdown("### 📜 Past Sessions History Log")
    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/history/sessions",
            headers=get_auth_headers()
        )
        if resp.status_code == 200:
            sessions = resp.json()
            if not sessions:
                st.info("No past sessions found. Start a mock interview or run an ATS audit to see logs.")
            else:
                # Build option maps
                session_options = {}
                for s in sessions:
                    date_parsed = datetime_val = s["created_at"].split("T")[0]
                    label = f"Session #{s['id']} - {s['job_title']} ({date_parsed}) [Score: {s['ats_score'] or 'In Progress'}]"
                    session_options[label] = s["id"]
                    
                selected_label = st.selectbox("Select a past session to reload:", options=list(session_options.keys()))
                selected_session_id = session_options[selected_label]
                
                # Fetch detailed session logs
                with st.spinner("Fetching transcripts from database..."):
                    detail_resp = requests.get(
                        f"{BACKEND_URL}/api/history/session/{selected_session_id}",
                        headers=get_auth_headers()
                    )
                    
                    if detail_resp.status_code == 200:
                        session_detail = detail_resp.json()
                        
                        st.markdown("---")
                        st.markdown(f"#### 📁 Session #{session_detail['id']} Logs - {session_detail['job_title']}")
                        
                        # Case A: It was a mock interview
                        if session_detail.get("report") or session_detail.get("questions"):
                            report_db = session_detail.get("report")
                            questions_db = session_detail.get("questions", [])
                            
                            col_h1, col_h2 = st.columns([1, 2], gap="large")
                            with col_h1:
                                score_val = report_db["overall_score"] if report_db else "N/A"
                                st.markdown("<div class='premium-card' style='text-align: center;'>", unsafe_allow_html=True)
                                st.markdown("##### Overall Performance")
                                st.markdown(
                                    f"""
                                    <div class='score-circle-container'>
                                        <div class='score-circle'>{score_val}<span style='font-size:1.5rem; vertical-align:super;'>/10</span></div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                            with col_h2:
                                summary_val = report_db["summary"] if report_db else "This interview session was started but not finalized with a summary report."
                                st.markdown("<div class='premium-card' style='height: 100%;'>", unsafe_allow_html=True)
                                st.markdown("##### Session Summary")
                                st.write(summary_val)
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                            st.markdown("---")
                            
                            if report_db:
                                col_hr1, col_hr2 = st.columns(2, gap="medium")
                                with col_hr1:
                                    st.markdown("<div class='premium-card' style='height: 100%;'>", unsafe_allow_html=True)
                                    st.markdown("##### 📚 Recommended Topics to Revise")
                                    if report_db.get('topics_to_revise'):
                                        for topic in report_db.get('topics_to_revise', []):
                                            st.markdown(f"<span class='concept-tag' style='background-color: rgba(239, 68, 68, 0.12); color: #f87171; border-color: rgba(239, 68, 68, 0.25);'>{topic}</span>", unsafe_allow_html=True)
                                    else:
                                        st.write("*No revision topics specified.*")
                                    st.markdown("##### Concepts to Strengthen:")
                                    if report_db.get('concepts_to_strengthen'):
                                        for concept in report_db.get('concepts_to_strengthen', []):
                                            st.markdown(f"<div class='weakness-item' style='border-left-color: #ef4444; background: rgba(239, 68, 68, 0.04);'>🔍 {concept}</div>", unsafe_allow_html=True)
                                    else:
                                        st.write("*No concepts specified.*")
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    
                                with col_hr2:
                                    st.markdown("<div class='premium-card' style='height: 100%;'>", unsafe_allow_html=True)
                                    st.markdown("##### 🎯 Focus for Next Mock Session")
                                    st.write(report_db.get('suggested_focus', ''))
                                    st.markdown("</div>", unsafe_allow_html=True)
                                st.markdown("---")
                            
                            # Trend graph
                            scores_db = [q["score"] for q in questions_db if q.get("score") is not None]
                            if scores_db:
                                st.markdown("##### 📈 Question Score Progression")
                                chart_data_db = pd.DataFrame({
                                    "Question": [f"Q{i}" for i in range(1, len(scores_db) + 1)],
                                    "Score": scores_db
                                }).set_index("Question")
                                st.bar_chart(chart_data_db)
                                
                            # QA expansion listing
                            st.markdown("##### 📝 Interview Q&A Transcript")
                            for idx, q in enumerate(questions_db, 1):
                                score_badge = f"(Score: {q['score']}/10)" if q.get('score') is not None else "(Not Answered)"
                                with st.expander(f"Q{idx}: {q['question_text'][:80]}... {score_badge}"):
                                    st.markdown(f"**Full Question:** {q['question_text']}")
                                    st.info(f"**Answer:** {q['candidate_answer'] or 'Skipped/No response'}")
                                    if q.get('score') is not None:
                                        col_sh_str, col_sh_wk = st.columns(2)
                                        with col_sh_str:
                                            st.markdown("**Strengths:**")
                                            for st_val in (q['strengths'] or []):
                                                st.markdown(f"- {st_val}")
                                        with col_sh_wk:
                                            st.markdown("**Weaknesses:**")
                                            for wk_val in (q['weaknesses'] or []):
                                                st.markdown(f"- {wk_val}")
                                        st.markdown(f"**Feedback:** {q['feedback']}")
                                        st.markdown("---")
                                        st.success(f"**Model Answer:**\n{q['model_answer']}")
                                        
                        # Case B: It was an ATS scan session
                        elif session_detail.get("ats_score") is not None:
                            st.markdown("##### 🔍 ATS Scorecard Summary")
                            col_as1, col_as2 = st.columns([1, 2])
                            with col_as1:
                                st.markdown("<div class='premium-card' style='text-align: center;'>", unsafe_allow_html=True)
                                st.markdown(
                                    f"""
                                    <div class='score-circle-container'>
                                        <div class='score-circle'>{session_detail['ats_score']}<span style='font-size:1.5rem; vertical-align:super;'>%</span></div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.markdown("</div>", unsafe_allow_html=True)
                            with col_as2:
                                st.markdown("<div class='premium-card' style='height:100%;'>", unsafe_allow_html=True)
                                st.markdown("##### 💡 Optimize Recommendations")
                                for rec in (session_detail['ats_recommendations'] or []):
                                    st.write(f"- {rec}")
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                            st.markdown("---")
                            col_mt, col_ms = st.columns(2)
                            with col_mt:
                                st.markdown("##### Matched Skills")
                                for val in (session_detail['ats_skills_matched'] or []):
                                    st.markdown(f"<div class='strength-item'>🔹 {val}</div>", unsafe_allow_html=True)
                            with col_ms:
                                st.markdown("##### Missing Skills")
                                for val in (session_detail['ats_skills_missing'] or []):
                                    st.markdown(f"<div class='weakness-item'>🔸 {val}</div>", unsafe_allow_html=True)
                                    
                    else:
                        st.error("Failed to load details for this session.")
        else:
            st.error("Failed to fetch sessions from server.")
    except Exception as e:
        st.error(f"Cannot connect to database API: {e}")
