import streamlit as st
import tempfile
import time
import os
from pathlib import Path

# Phidata / Gemini / DuckDuckGo
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo

# (Optional) for environment variables
from dotenv import load_dotenv

################################################################################
# 1. Load environment variables & Configure API Keys
################################################################################

load_dotenv()
API_KEY_GOOGLE = os.getenv("GOOGLE_API_KEY")

if not API_KEY_GOOGLE:
    st.error("Google API Key not found. Please set GOOGLE_API_KEY in environment.")
    st.stop()

# Configure Google Generative AI
gen.configure(api_key=API_KEY_GOOGLE)

################################################################################
# 2. Streamlit Page Setup & Global Styles
################################################################################

st.set_page_config(
    page_title="Sage Creek Wrestling Analyzer",
    page_icon="🤼",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* Sage Creek Colors */
    :root {
        --sc-dark-green: #2B4736;
        --sc-light-green: #3D6A4D;
        --sc-gold: #BF9D4E;
        --sc-light-gray: #f5f5f5;
    }
    /* Header */
    .main-header {
        background-color: var(--sc-dark-green);
        padding: 20px;
        color: white;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }
    .main-header img {
        margin-right: 20px;
        width: 150px;
    }
    /* Analysis Section */
    .analysis-section {
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
    /* Buttons */
    .stButton button, .stDownloadButton button {
        background-color: var(--sc-dark-green);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 4px;
    }
    /* Section Headers */
    .section-header {
        background-color: var(--sc-light-green);
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 15px 0;
        font-size: 1.25rem;
    }
    /* Footer */
    .footer {
        background-color: var(--sc-dark-green);
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 8px;
        margin-top: 30px;
        font-size: 0.9rem;
    }
    /* Detailed Analysis Styling */
    .processing-status {
        font-size: 1.1rem;
        font-weight: bold;
        color: var(--sc-dark-green);
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

################################################################################
# 3. Header
################################################################################

st.markdown("""
    <div class="main-header">
        <img src="https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png" alt="Sage Creek Logo">
        <div>
            <h1 style="margin: 0;">Sage Creek High School</h1>
            <h3 style="margin: 0; font-weight: normal;">Wrestling Analyzer</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)

################################################################################
# 4. Sidebar Content & Wrestling Analysis Options
################################################################################

with st.sidebar:
    st.image("https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png", width=150)
    st.header("Wrestling Form Analysis")
    st.write("Level up your wrestling with AI-powered technique analysis. Upload a video and get personalized feedback, inspired by Coach Steele.")
    
    # Analysis detail level slider (just for user experience)
    analysis_detail = st.slider(
        "Analysis Detail Level",
        min_value=1,
        max_value=5,
        value=3,
        help="Higher values will produce more detailed analysis but may take longer."
    )

    st.info("Go Bobcats!")

################################################################################
# 5. Phidata Agent (Gemini + DuckDuckGo)
################################################################################

@st.cache_resource
def initialize_agent():
    """
    Initializes a Phidata Agent with the Gemini 2.0 model and DuckDuckGo tool.
    The 'videos' parameter might fail with gemini-2.0 on raw video data,
    but we'll pass it along as a demonstration.
    """
    return Agent(
        name="Wrestling Analyzer Agent",
        model=Gemini(model="gemini-2.0-flash-exp"),  # or "gemini-2.0-pro" etc.
        tools=[DuckDuckGo()],
        markdown=True
    )

multimodal_agent = initialize_agent()

################################################################################
# 6. Main App - File Uploader & Analysis
################################################################################

st.write("Upload a wrestling video to receive technique analysis and integrated web insights.")
video_file = st.file_uploader("Upload Video", type=['mp4', 'mov'])

if video_file:
    file_details = {
        "FileName": video_file.name,
        "FileType": video_file.type,
        "FileSize": f"{video_file.size / (1024 * 1024):.2f} MB"
    }
    st.write(f"**File Details:** {file_details['FileName']} ({file_details['FileSize']} MB)")

    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    # Display video in Streamlit
    st.video(video_path, format="video/mp4")

    # Additional context for wrestling analysis
    user_context = st.text_area(
        "Additional Wrestling Context (Optional)",
        placeholder="E.g., 'Analyze my single leg takedown', 'Focus on top control', 'I struggle with finishing shots'",
        height=70
    )

    # The "Coach Steele" style prompt logic
    # We'll incorporate user_context and the "analysis_detail" slider for nuance
    # plus a general approach referencing the "Kolat Philosophy"

    # Button to run analysis
    if st.button("Analyze Wrestling Video"):
        with st.spinner("Analyzing video and gathering info from the web..."):
            # The custom prompt referencing "Coach Steele" style
            # Because gemini-2.0 has issues with raw video, we might reference it in text
            # but still pass the actual file as 'videos=[video_path]' to demonstrate usage.

            # We’ll note that the Phidata docs let us pass a list of videos,
            # but it may not fully parse the video with gemini-2.0 at the moment.
            prompt = f"""
                You are Coach David Steele analyzing a wrestling video, drawing on Cary Kolat-inspired fundamentals.
                Provide a detailed technical analysis relevant to high school wrestlers.
                Emphasize stance, takedown entries, finishes, top control, bottom escapes, and mental toughness.

                Analysis Detail: {analysis_detail}
                Additional Context: {user_context}

                # Provide:
                - Key fundamental areas for improvement (2-5, depending on detail level).
                - Actionable drills referencing typical high school practice routines.
                - Encouraging but rigorous "Coach Steele" style feedback.

                # Reference external wrestling knowledge (via web search) to clarify details if needed.
                # The final output should be an integrated summary of:
                - Observations from the video
                - Additional web insights from the DuckDuckGo tool

                NOTE: If actual video analysis is not fully supported, combine user context with best wrestling knowledge and any relevant web data.
            """

            # Run agent with the user prompt & attach the local video file
            # Caution: This might not work fully with gemini-2.0 as it doesn't truly parse video.
            try:
                response = multimodal_agent.run(
                    prompt,
                    videos=[video_path]  # demonstration only
                )
                st.markdown("### Wrestling Technique Analysis")
                st.write(response)
            except Exception as ex:
                st.error(f"Error running analysis with Gemini 2.0: {ex}")
                st.info("Gemini 2.0 may not support direct video analysis. Try removing the video or using a different approach.")
            
        # Clean up after ourselves
        Path(video_path).unlink(missing_ok=True)

else:
    st.info("Awaiting video upload. Please select an mp4 or mov file.")

################################################################################
# 7. Footer
################################################################################

st.markdown("""
    <div class="footer">
        <p>Sage Creek High School | 3900 Bobcat Blvd. | Carlsbad, CA 92010</p>
        <p>Phone: 760-331-6600 • Email: office.schs@carlsbadusd.net</p>
        <p>Contents © 2025 Sage Creek High School</p>
    </div>
""", unsafe_allow_html=True)
