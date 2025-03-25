import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.youtube_tools import YouTubeTools

import google.generativeai as genai
from google.generativeai import upload_file, get_file

import time
from pathlib import Path
import tempfile
import os

from dotenv import load_dotenv
load_dotenv()

# 1. Configure your Google Gemini API key from environment
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.warning("GOOGLE_API_KEY not found. Please define it in .env or environment.")

# 2. Set up Streamlit page
st.set_page_config(
    page_title="Sage Creek Wrestling Analyzer",
    page_icon="🤼",
    layout="wide"
)

# 3. Page title and branding
st.title("Sage Creek Wrestling Analyzer")
st.header("Powered by Phidata & Gemini 2.0 Flash Exp")
st.caption("Coach Steele-Style Feedback with Cary Kolat–inspired Technique Insights")

# 4. Initialize Multi-Agent System
@st.cache_resource
def initialize_agent():
    """
    Creates two specialized agents:
     - youtube_agent: uses YouTubeTools to get captions and handle YouTube-based content
     - upload_agent: can do supplementary search with DuckDuckGo for local video
    Both are integrated into a top-level agent with 'Coach Steele' instructions.
    """
    # Agent for YouTube video-based analysis
    youtube_agent = Agent(
        name="Youtube Link Handling Agent",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[YouTubeTools()],
        instructions=[
            "You are a specialized YouTube agent. Your job is to obtain the captions or relevant data from a YouTube video and answer questions."
        ],
        show_tools_calls=True,
        markdown=True
    )

    # Agent for local video + search
    upload_agent = Agent(
        name="Local Video Handling Agent",
        model=Gemini(id="gemini-2.0-flash-exp"),
        markdown=True,
        tools=[DuckDuckGo()],
        instructions=[
            "You are a wrestling technique analysis sub-agent, referencing external info via DuckDuckGo if needed."
        ]
    )

    # Final aggregator agent: "Coach Steele" style
    # We combine the YouTube & Upload agents as a 'team'.
    return Agent(
        name="Sage Creek Wrestling Analyzer - Coach Steele",
        team=[youtube_agent, upload_agent],
        model=Gemini(id="gemini-2.0-flash-exp"),
        instructions=[
            "You are Coach David Steele, wrestling coach at Sage Creek High School.",
            "Your style is tough but encouraging, referencing Cary Kolat’s philosophy.",
            "Provide thorough wrestling technique analysis, with direct and actionable drills.",
            "Focus on stance, takedown entries, finishes, top control, bottom escapes, and the mental game."
        ],
        markdown=True
    )

Multimodal_Agent = initialize_agent()

###############################################################################
# 5. UI Inputs: YouTube Link or Local File
###############################################################################
st.subheader("Step 1: Provide a Wrestling Video")
youtube_url = st.text_input(
    "Enter a YouTube video URL for analysis",
    placeholder="https://www.youtube.com/watch?v=VIDEO_ID",
    help="Paste a YouTube link you want Coach Steele to analyze"
)

video_file = st.file_uploader(
    "Or upload a local wrestling video file (MP4, MOV, AVI)",
    type=["mp4", "mov", "avi"],
    help="Upload a short video for analysis if you have no YouTube link"
)

###############################################################################
# 6. Analysis Routines
###############################################################################
def analyze_youtube_video(url: str, query: str):
    """
    Analyze a YouTube video with 'Coach Steele' style,
    referencing any relevant external context.
    """
    try:
        with st.spinner("Processing YouTube video via Coach Steele..."):
            # The final prompt referencing the user’s query and the YouTube link
            analysis_prompt = f"""
                You're analyzing a wrestling video from YouTube at {url}.
                The user asks: {query}

                Provide a thorough wrestling technique analysis, referencing the video’s
                content (captions, if available) and additional web knowledge if needed.
                Focus on critical improvements, Kolat-inspired drills, and 'Coach Steele' style toughness.
                Conclude with a motivational message for a Sage Creek wrestler.
            """

            response = Multimodal_Agent.run(analysis_prompt)

        st.subheader("Analysis Result")
        st.markdown(response.content)

    except Exception as error:
        st.error(f"An error occurred during analysis: {error}")

def analyze_uploaded_video(file_path: str, query: str):
    """
    Analyze a local MP4/MOV/AVI video, referencing the
    video file plus external context. The file is
    uploaded to Google GenerativeAI (upload_file) for partial reference.
    """
    try:
        with st.spinner("Processing local video via Coach Steele..."):
            # 1) Upload file to Google GenerativeAI
            process_video = upload_file(file_path)
            # 2) Poll until state != PROCESSING
            while process_video.state.name == "PROCESSING":
                time.sleep(2)
                process_video = get_file(process_video.name)

            # 3) Construct the final prompt
            analysis_prompt = f"""
                You have a wrestling video uploaded for analysis. The user asks: {query}

                Provide a thorough wrestling technique analysis, referencing Kolat fundamentals
                and real wrestling knowledge. Incorporate external web search if needed.
                Summarize technique diagnoses, recommended drills, and mindset tips, all in
                'Coach Steele' style. End with an encouraging challenge for a Sage Creek wrestler.
            """

            # 4) Run the multi-agent, passing the processed video
            response = Multimodal_Agent.run(analysis_prompt, videos=[process_video])

        st.subheader("Analysis Result")
        st.markdown(response.content)

    except Exception as error:
        st.error(f"An error occurred during analysis: {error}")
    finally:
        # Clean up local temp file
        Path(file_path).unlink(missing_ok=True)


###############################################################################
# 7. UI Interaction: Asking for Queries
###############################################################################
if youtube_url:
    # If user provides a YouTube link, get their question
    user_query = st.text_area(
        "What do you want Coach Steele to focus on from this YouTube wrestling video?",
        placeholder="E.g., single leg technique, stance, top control, etc.",
        help="Enter specific points or a general request for analysis."
    )

    # Button to analyze
    if st.button("Analyze YouTube Video", key="analyze_youtube"):
        if not user_query.strip():
            st.warning("Please provide a question or topic for analysis.")
        else:
            analyze_youtube_video(youtube_url, user_query)

elif video_file:
    # If a local file is provided, store it, preview it, then ask a query
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    st.video(video_path, format='video/mp4', start_time=0)

    user_query = st.text_area(
        "What do you want Coach Steele to address from this uploaded video?",
        placeholder="E.g., 'How can I improve my shots?', 'Is my stance too high?', etc.",
        help="Enter specific points or a general request for analysis."
    )

    if st.button("Analyze Uploaded Video", key="analyze_local_video"):
        if not user_query.strip():
            st.warning("Please provide a question or topic for analysis.")
        else:
            analyze_uploaded_video(video_path, user_query)

else:
    # If no source is provided, user sees instructions
    st.info("Please enter a YouTube video URL or upload a wrestling video to begin analysis.")


###############################################################################
# 8. Small Styling Tweak for Larger Text Boxes
###############################################################################
st.markdown(
    """
    <style>
    .stTextArea textarea {
        height: 100px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Footer, if desired
st.markdown("""
<hr>
<p style="text-align:center;">
  <strong>Sage Creek High School | 3900 Bobcat Blvd. | Carlsbad, CA 92010</strong><br>
  Phone: 760-331-6600 • Email: office.schs@carlsbadusd.net<br>
  Contents © 2025 Sage Creek High School
</p>
""", unsafe_allow_html=True)
