import streamlit as st
from interview_bot import InterviewBot  # Assuming your bot class is in interview_bot.py
import os
import tempfile

# Set page config
st.set_page_config(
    page_title="AI Technical Interviewer",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .stTextInput input {
            border-radius: 20px;
            padding: 10px 15px;
        }
        .stButton button {
            width: 100%;
            border-radius: 20px;
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .stChatMessage {
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
        }
        .user-message {
            background-color: #f0f2f6;
        }
        .bot-message {
            background-color: #e3f2fd;
        }
    </style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    if 'bot' not in st.session_state:
        st.session_state.bot = None
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'resume_processed' not in st.session_state:
        st.session_state.resume_processed = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = False

def display_chat():
    """Display the chat messages"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show difficulty level for bot messages
            if message["role"] == "assistant" and "difficulty" in message:
                st.caption(f"Difficulty: {message['difficulty'].upper()}")

def start_interview(resume_file=None):
    """Start the interview process"""
    api_key = os.getenv("GROQ_API_KEY")  # Get from environment variables
    
    if not api_key:
        st.error("GROQ_API_KEY not found in environment variables!")
        return
    
    st.session_state.bot = InterviewBot(api_key=api_key)
    
    if resume_file:
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resume_file.getvalue())
            resume_path = tmp.name
        
        if st.session_state.bot.load_resume(resume_path):
            st.session_state.resume_processed = True
            os.unlink(resume_path)  # Delete temp file
        else:
            st.error("Failed to process resume. Starting without resume analysis.")
    
    # Add initial greeting
    domain = st.session_state.bot.interview_state["domain"] if st.session_state.bot.interview_state["domain"] != "general" else "technical"
    greeting = f"Hi there! I'll be conducting your {domain} interview today. Let's start with a brief introduction. Could you tell me about yourself and your {domain} experience?"
    
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.current_question = greeting
    st.session_state.interview_started = True

def handle_user_response(user_input):
    """Process user response and get next question"""
    if not st.session_state.interview_started or not st.session_state.bot:
        return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process the response and get next question
    if not st.session_state.feedback_given:
        # Evaluate response if we're in a topic
        if st.session_state.bot.interview_state["current_topic"]:
            score = st.session_state.bot.evaluate_response(
                st.session_state.bot.interview_state["current_topic"],
                user_input
            )
        
        # Get next question
        topic, question = st.session_state.bot.determine_next_topic()
        st.session_state.bot.interview_state["current_topic"] = topic
        
        # Add bot response to chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": question,
            "difficulty": st.session_state.bot.interview_state["technical_difficulty"],
            "topic": topic
        })
        st.session_state.current_question = question
    else:
        # Interview completed
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Thank you for participating in the interview! You can start a new session if you'd like."
        })

def show_feedback():
    """Display interview feedback"""
    if not st.session_state.bot or st.session_state.feedback_given:
        return
    
    # Calculate overall score
    total_questions = sum(st.session_state.bot.interview_state["questions_per_difficulty"].values())
    if total_questions > 0:
        for key in st.session_state.bot.interview_state["hiring_scores"]:
            st.session_state.bot.interview_state["hiring_scores"][key] /= total_questions
    
    overall_score = (
        st.session_state.bot.interview_state["hiring_scores"]["technical_knowledge"] * 0.4 +
        st.session_state.bot.interview_state["hiring_scores"]["problem_solving"] * 0.3 +
        st.session_state.bot.interview_state["hiring_scores"]["communication"] * 0.15 +
        st.session_state.bot.interview_state["hiring_scores"]["experience_relevance"] * 0.15
    )
    
    # Generate feedback
    feedback = f"""
    ### Interview Feedback
    
    *Overall Score*: {overall_score:.2f}/1.0
    
    *Breakdown*:
    - Technical Knowledge: {st.session_state.bot.interview_state["hiring_scores"]["technical_knowledge"]:.2f}/1.0
    - Problem Solving: {st.session_state.bot.interview_state["hiring_scores"]["problem_solving"]:.2f}/1.0
    - Communication: {st.session_state.bot.interview_state["hiring_scores"]["communication"]:.2f}/1.0
    - Experience Relevance: {st.session_state.bot.interview_state["hiring_scores"]["experience_relevance"]:.2f}/1.0
    
    *Recommendation*: {"Strong Hire" if overall_score > 0.8 else "Hire" if overall_score > 0.6 else "Consider" if overall_score > 0.4 else "Reject"}
    """
    
    st.session_state.messages.append({"role": "assistant", "content": feedback})
    st.session_state.feedback_given = True

def main():
    initialize_session_state()
    
    st.title("🤖 AI Technical Interviewer")
    st.markdown("Practice your technical interview skills with our AI-powered interviewer")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        max_questions = st.slider("Maximum number of questions", 5, 20, 12)
        api_key = st.text_input("GROQ API Key", type="password", help="Get your API key from Groq's website")
        
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
        
        if st.button("Reset Interview"):
            st.session_state.clear()
            initialize_session_state()
            st.rerun()
    
    # Upload resume section (only before interview starts)
    if not st.session_state.interview_started:
        with st.form("start_interview"):
            st.subheader("Start Your Interview")
            resume_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
            
            if st.form_submit_button("Start Interview"):
                start_interview(resume_file)
    
    # Display chat
    display_chat()
    
    # User input (only when interview is active and not completed)
    if st.session_state.interview_started and not st.session_state.feedback_given:
        # Check if we've reached max questions
        total_questions = sum(st.session_state.bot.interview_state["questions_per_difficulty"].values())
        if total_questions >= max_questions:
            show_feedback()
        else:
            with st.form("user_response"):
                user_input = st.text_input(
                    "Your response", 
                    placeholder="Type your answer here...",
                    key="user_input"
                )
                
                if st.form_submit_button("Send"):
                    if user_input.strip():
                        handle_user_response(user_input.strip())
                        st.rerun()

if __name__ == "__main__":
    main()