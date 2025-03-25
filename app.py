import streamlit as st
import tempfile
import time
import os
from pathlib import Path

import google.generativeai as genai
from google.generativeai import types

# 1. Load API key from Streamlit secrets
API_KEY_GOOGLE = st.secrets["google"].get("api_key", None)
if not API_KEY_GOOGLE:
    st.error("Google API Key not found in secrets. Please set [google] api_key in secrets.toml.")
    st.stop()

# 2. Configure Generative AI
genai.configure(api_key=API_KEY_GOOGLE)

# 3. Streamlit Page Configuration
st.set_page_config(
    page_title="Sage Creek Wrestling Analyzer",
    page_icon="🤼",
    layout="wide"
)

# 4. Page Title / Branding
st.markdown("""
    <style>
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* Sage Creek Colors */
    :root {
        --sc-dark-green: #2B4736;
        --sc-light-green: #3D6A4D;
        --sc-gold: #BF9D4E;
    }
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
        width: 120px;
    }
    .analysis-section {
        background-color: #f8f8f8;
        border-left: 5px solid var(--sc-gold);
        padding: 15px;
        margin-top: 20px;
        border-radius: 0 8px 8px 0;
    }
    .processing-status {
        font-size: 1.1rem;
        font-weight: bold;
        color: var(--sc-dark-green);
        margin: 10px 0;
    }
    .footer {
        background-color: var(--sc-dark-green);
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 8px;
        margin-top: 40px;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <img src="https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png" alt="Sage Creek Logo">
    <div>
        <h1 style="margin: 0;">Sage Creek High School</h1>
        <h3 style="margin: 0; font-weight: normal;">Coach Steele Wrestling Analyzer</h3>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. Main UI
st.subheader("Upload a Wrestling Video")
video_file = st.file_uploader(
    "Video File (MP4, MOV, etc.):",
    type=["mp4", "mov", "avi"],
    help="Wrestling technique video for Coach Steele to analyze."
)

# Query / Extra context
user_prompt = st.text_area(
    "Additional Context or Focus Points (Optional)",
    placeholder="E.g. 'Focus on my stance and single-leg takedown' or 'Please emphasize defensive scrambling.'",
    height=100
)

def analyze_wrestling_video(video_path: str, user_notes: str):
    """
    Uploads the local video file to Google Generative AI,
    waits for processing, and then passes a prompt for 'Coach Steele' style analysis.
    """
    try:
        # 1. Upload the video to Google's generative AI
        uploaded_file = genai.files.upload(path=video_path)
        # 2. Poll until the file is 'ACTIVE' or 'FAILED'
        while uploaded_file.state == "PROCESSING":
            st.write("Waiting for video to be processed...")
            time.sleep(3)
            uploaded_file = genai.files.get(name=uploaded_file.name)

        if uploaded_file.state == "FAILED":
            st.error("File upload failed. Please try a different video or check your file size limits.")
            return

        # 3. Construct a "Coach Steele" prompt
        # This prompt encourages the LLM to reference fundamental wrestling technique.
        system_instruction = """You are Coach David Steele, wrestling coach at Sage Creek High School.
You deliver intense, but constructive wrestling feedback based on Cary Kolat’s philosophy.
Your analysis is direct yet encouraging. Focus on stance, shots, finishes, top control, bottom escapes,
and overall mindset.
"""

        # We'll have the LLM produce a single detailed analysis. 
        user_instruction = f"""
A wrestling video has been uploaded for your analysis. 
User notes: {user_notes}

Please identify the main technical strengths and weaknesses in the athlete's performance, referencing fundamental
wrestling skills. Provide 2-3 key focal points to improve, plus recommended drills or practice ideas.
Close with a motivating, "Coach Steele–style" message.
"""

        # 4. Generate content using the video + user prompt
        response = genai.models.generate_content(
            model="gemini-2.0-flash",  # or whichever 2.0 model you have access to
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type=uploaded_file.mime_type
                        )
                    ]
                ),
                user_instruction
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=8192
            ),
        )

        # 5. Return the final text
        return response.text

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None
    finally:
        # Cleanup local file
        Path(video_path).unlink(missing_ok=True)

# Action: If user clicks "Analyze"
if video_file:
    st.video(video_file, format="video/mp4")

    if st.button("Analyze Video"):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(video_file.read())
            video_path = temp_video.name

        st.write("Analyzing your wrestling video...")

        output = analyze_wrestling_video(video_path, user_prompt)
        if output:
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.subheader("Coach Steele's Analysis")
            st.write(output)
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload a video to get started.")

# 6. Footer
st.markdown("""
<div class="footer">
    <p>Sage Creek High School | 3900 Bobcat Blvd. | Carlsbad, CA 92010<br>
    Phone: 760-331-6600 • Email: office.schs@carlsbadusd.net<br>
    Contents © 2025 Sage Creek High School</p>
</div>
""", unsafe_allow_html=True)
