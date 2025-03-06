import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file
from elevenlabs.client import ElevenLabs
import time, os, tempfile
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="Sage Creek Wrestling Analyzer",
    page_icon="🤼",
    layout="wide"
)

# Retrieve API keys from secrets
API_KEY_GOOGLE = st.secrets["google"]["api_key"]
API_KEY_ELEVENLABS = st.secrets.get("elevenlabs", {}).get("api_key", None)

# Configure Google Generative AI
if API_KEY_GOOGLE:
    os.environ["GOOGLE_API_KEY"] = API_KEY_GOOGLE
    genai.configure(api_key=API_KEY_GOOGLE)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# Modern and educational CSS styling
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
        background-color: var(--sc-light-gray);
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
    /* Video Upload Button */
    .video-upload-button {
        background-color: var(--sc-gold);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        padding: 15px 25px;
        font-size: 1.2rem;
        cursor: pointer;
        display: inline-block;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <img src="https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png" alt="Sage Creek Logo">
        <div>
            <h1 style="margin: 0;">Sage Creek High School</h1>
            <h3 style="margin: 0; font-weight: normal;">Wrestling Analyzer</h3>
        </div>
    </div>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.image("https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png", width=150)
    st.header("Wrestling Form Analysis")
    st.write("Level up your wrestling with AI-powered technique analysis. Upload a video and get detailed feedback in the voice of Coach Steele.")
    st.info("Go Bobcats!")

# Agent initialization
@st.cache_resource
def initialize_agent():
    return Agent(
        name="Wrestling Form Analyzer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_Agent = initialize_agent()
script_agent = initialize_agent()

# Session state initialization
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'audio_script' not in st.session_state:
    st.session_state.audio_script = None
if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False
if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False

# Main UI Header
st.markdown('<div class="section-header">Wrestling Technique Analyzer</div>', unsafe_allow_html=True)
st.write("Upload a video of your wrestling technique for analysis.")

# Video upload button
video_file = st.file_uploader("Upload Video", type=['mp4', 'mov', 'avi'])

# Make the upload button more prominent
st.markdown('<button class="video-upload-button">Upload Your Wrestling Video</button>', unsafe_allow_html=True)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    # Display video preview with an option to remove the preview
    preview_placeholder = st.empty()
    with preview_placeholder.container():
        st.video(video_path, format="video/mp4", start_time=0)
        if st.button("Close Video Preview"):
            preview_placeholder.empty()

    user_query = st.text_area(
        "What wrestling technique would you like analyzed?",
        placeholder="e.g., 'Analyze my single leg takedown', 'How's my top control?', 'Check my stand-up escape'",
        height=80
    )
    if st.button("Get Analysis"):
        if not user_query:
            st.warning("Please enter a wrestling technique you want analyzed.")
        else:
            try:
                with st.spinner("Analyzing video and generating feedback..."):
                    progress_bar = st.progress(0)
                    progress_bar.progress(10, text="Uploading...")
                    processed_video = upload_file(video_path)

                    progress_bar.progress(30, text="Processing...")
                    processing_start = time.time()
                    while processed_video.state.name == "PROCESSING":
                        if time.time() - processing_start > 60:
                            st.warning("Video processing is taking longer than expected. Please be patient.")
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)

                    progress_bar.progress(60, text="Analyzing Technique...")

                    analysis_prompt = f"""You are Coach David Steele, the wrestling coach at Sage Creek High School. You are analyzing a video to provide feedback to a high school wrestler, drawing inspiration from the intense and detail-oriented coaching methods of legends like Cary Kolat. Analyze this wrestling video focusing on: {user_query}

Structure your analysis to deliver actionable insights, emphasizing core techniques and relentless improvement, in line with wrestling principles inspired by the Kolat Wrestling Philosophy as described in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'.

Structure your feedback rigorously, mirroring a direct and demanding coaching approach, while maintaining a constructive tone appropriate for high school athletes:

## TECHNIQUE DIAGNOSIS: INITIAL IMPRESSION - BE DIRECT.
Provide a clear and honest initial assessment of the wrestler's technique. Be direct but constructive.  Example: "Needs Sharpening: Single leg entry shows potential, but finish is weak. Stance needs to be lower and more consistent."

## KEY FUNDAMENTAL AREAS FOR IMPROVEMENT (Identify 2-3 CRITICAL ISSUES - PRIORITIZE)
*   Pinpoint 2-3 key areas that need the most immediate attention for improvement. Timestamp each for video reference. Focus on fundamentals.
*   Explain the *precise* technical issue. Use clear wrestling terminology, referencing core principles. Focus on stance, motion, penetration, finish, top control, bottom escapes, scrambling as relevant. Example: "Stance Too High - [0:15]. Wrestler's stance is too upright, compromising power and speed. A lower stance is crucial for effective shots and defense."
*   Detail the *impact* of these issues on wrestling performance and match outcomes. Explain how these weaknesses can be exploited by opponents at the high school level, drawing upon general wrestling knowledge and principles inspired by 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'. Example: "High stance makes you vulnerable to faster opponents and deeper shots. You'll struggle against anyone with a strong low attack.  Remember the emphasis on 'Stance and Movement' in Kolat-inspired training."

## ACTIONABLE DRILL PRESCRIPTION:  TARGETED DRILLS FOR FIXES (Assign 2-3 Focused Drills)
*   Prescribe 2-3 specific, actionable drills to directly address the identified weaknesses. Prioritize drills that can be realistically implemented in a high school practice setting.  Reference drills that align with Kolat-inspired training methods whenever possible.
*   Explain the *specific purpose* of each drill and *how* it will lead to technical correction and skill development. Example: "Drill: Partner Penetration Step Drill (3 sets of 20 reps). Purpose: To build muscle memory for a lower, more explosive penetration step, improving shot entries. Focus on driving through with the hips, maintaining a strong base -  as emphasized in Kolat-inspired 'Penetration' drills."

## WRESTLING IQ & MINDSET - COACH STEELE'S KEY TAKEAWAY
*   Deliver ONE key takeaway focused on mindset or wrestling IQ.  This should be encouraging but also emphasize the importance of hard work, smart training, and continuous improvement, reflecting a Coach Steele inspired by Kolat's dedication.
*   Frame it as a memorable coaching cue or key principle. Example: "Key Takeaway: 'Be Relentless in Improvement.'  Focus on getting 1% better every practice.  Drill these corrections, visualize success, and bring intensity to every workout. That's how we build champions at Sage Creek."
""", unsafe_allow_html=True)
                    progress_bar.progress(80, text="Generating Insights...")
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video], user_query=user_query)
                    progress_bar.progress(100, text="Analysis Complete. Keep Working Hard!")
                    time.sleep(0.5)
                    progress_bar.empty()

                    st.session_state.analysis_result = response.content
                    st.session_state.audio_generated = False
                    st.session_state.show_audio_options = False
                    st.session_state.audio_script = None

            except Exception as error:
                st.error(f"Analysis error: {error}")
                st.info("Try uploading a shorter video or check your internet connection.")
            finally:
                Path(video_path).unlink(missing_ok=True)

    if st.session_state.analysis_result:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.subheader("Wrestling Technique Analysis")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="Download Analysis",
            data=st.session_state.analysis_result,
            file_name="wrestling_technique_analysis.md",
            mime="text/markdown"
        )

        if st.button("Listen to Analysis (Audio Options)"):
            st.session_state.show_audio_options = True

        if st.session_state.show_audio_options:
            with st.expander("Audio Voice Settings", expanded=True):
                st.subheader("Voice Options")
                elevenlabs_api_key = API_KEY_ELEVENLABS
                selected_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
                if elevenlabs_api_key:
                    try:
                        client = ElevenLabs(api_key=elevenlabs_api_key)
                        voice_data = client.voices.get_all()
                        voices_list = [v.name for v in voice_data.voices]
                        selected_voice_name = st.selectbox("Choose Voice", options=voices_list, index=0)
                        selected_voice_id = next((v.voice_id for v in voice_data.voices if v.name == selected_voice_name), None)
                        if not selected_voice_id:
                            st.warning("Voice selection issue. Using default voice.")
                            selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                    except Exception as e:
                        st.warning(f"Could not retrieve voices: {e}. Using default voice.")
                        selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                else:
                    st.error("ElevenLabs API key missing.")

                if st.button("Generate Audio Analysis"):
                    if elevenlabs_api_key:
                        try:
                            with st.spinner("Preparing audio script - Kolat Style..."):
                                script_prompt = f"""
Convert the following wrestling technique analysis into a monologue script as if spoken by Coach David Steele.
The tone MUST be direct, demanding, and hyper-focused on actionable corrections and drills. Remove all headings, bullet points, timestamps, and fluff. The final script should sound like a coach talking directly to a wrestler – no-nonsense, tough, and urgent.

Analysis to convert:

{st.session_state.analysis_result}

                                """
                                script_response = script_agent.run(script_prompt)
                                st.session_state.audio_script = script_response.content

                            with st.spinner("Generating audio - Coach Steele Voice..."):
                                client = ElevenLabs(api_key=elevenlabs_api_key)
                                audio_generator = client.text_to_speech.convert(
                                    text=st.session_state.audio_script,
                                    voice_id=selected_voice_id,
                                    model_id="eleven_multilingual_v2"
                                )
                                audio_bytes = b""
                                for chunk in audio_generator:
                                    audio_bytes += chunk
                                st.session_state.audio = audio_bytes
                                st.session_state.audio_generated = True

                                st.audio(st.session_state.audio, format="audio/mp3")
                                st.download_button(
                                    label="Download Audio Analysis",
                                    data=st.session_state.audio,
                                    file_name="wrestling_analysis_audio.mp3",
                                    mime="audio/mp3"
                                )
                        except Exception as e:
                            st.error(f"Audio generation error: {str(e)}")
                    else:
                        st.error("ElevenLabs API key needed for audio.")
else:
    st.write("Upload a wrestling video to receive Coach Steele-style technique analysis. Let's get to work!")
    st.info("🤼 Upload a wrestling technique video above for expert AI analysis and personalized feedback!")

# Footer
st.markdown("""
    <div class="footer">
        <p>Sage Creek High School | 3900 Bobcat Blvd. | Carlsbad, CA 92010</p>
        <p>Phone: 760-331-6600 • Email: office.schs@carlsbadusd.net</p>
        <p>Contents © 2025 Sage Creek High School</p>
    </div>
""", unsafe_allow_html=True)
