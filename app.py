import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file
from elevenlabs.client import ElevenLabs

import time
import os
import tempfile
from pathlib import Path
import base64

# Set page configuration
st.set_page_config(
    page_title="Sage Creek Wrestling Analyzer",
    page_icon="🤼",
    layout="wide"
)

# ------------------------------
# Retrieve API keys from secrets
# ------------------------------
API_KEY_GOOGLE = st.secrets["google"]["api_key"]
API_KEY_ELEVENLABS = st.secrets.get("elevenlabs", {}).get("api_key", None)

# ------------------------------
# Configure Google Generative AI
# ------------------------------
if API_KEY_GOOGLE:
    os.environ["GOOGLE_API_KEY"] = API_KEY_GOOGLE
    genai.configure(api_key=API_KEY_GOOGLE)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()

# ------------------------------
# CSS styling based on Sage Creek website
# ------------------------------
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Sage Creek Colors */
    :root {
        --sc-dark-green: #2B4736;
        --sc-light-green: #3D6A4D;
        --sc-gold: #BF9D4E;
        --sc-light-gray: #f5f5f5;
        --sc-dark-gray: #333333;
    }

    /* Header Styling */
    .main-header {
        background-color: var(--sc-dark-green);
        padding: 15px;
        color: white;
        border-radius: 5px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }

    .main-header img {
        margin-right: 15px;
    }

    /* Analysis Section */
    .analysis-section {
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid var(--sc-gold);
        margin-top: 20px;
        background-color: var(--sc-light-gray);
    }

    /* Button Styling */
    .stButton button {
        background-color: var(--sc-dark-green);
        color: white;
        font-weight: bold;
    }

    .stDownloadButton button {
        background-color: var(--sc-gold);
        color: white;
        font-weight: bold;
    }

    /* Info Boxes */
    .info-box {
        background-color: var(--sc-light-gray);
        border-left: 5px solid var(--sc-gold);
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }

    /* Navigation Menu Styling */
    .nav-menu {
        background-color: var(--sc-dark-green);
        color: white;
        padding: 10px;
        margin-bottom: 20px;
        border-radius: 5px;
        display: flex;
        justify-content: space-around;
    }

    .nav-menu a {
        color: white;
        text-decoration: none;
        padding: 5px 10px;
    }

    /* Footer Styling */
    .footer {
        background-color: var(--sc-dark-green);
        color: white;
        padding: 15px;
        text-align: center;
        border-radius: 5px;
        margin-top: 30px;
    }

    /* Centralize elements for cleaner look on larger screens */
    .stFileUploader, .stTextArea, .stButton, .stDownloadButton, .stAudio, .stVideo {
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Section Headers */
    .section-header {
        background-color: var(--sc-light-green);
        color: white;
        padding: 8px 15px;
        border-radius: 5px;
        margin: 15px 0;
    }

    /* Sport Boxes */
    .sport-box {
        display: inline-block;
        background-color: var(--sc-dark-green);
        color: white;
        padding: 8px 15px;
        margin: 5px;
        border-radius: 5px;
        font-weight: bold;
    }

    .sport-box.active {
        background-color: var(--sc-gold);
    }

    h1, h2, h3, h4 {
        color: var(--sc-dark-green);
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# Header - Styled like Sage Creek website
# ------------------------------
st.markdown("""
    <div class="main-header">
        <img src="https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png" width="70">
        <div>
            <h1 style="margin: 0;">Sage Creek High School</h1>
            <h3 style="margin: 0; font-weight: normal;">Wrestling Analyzer</h3>
        </div>
    </div>
""", unsafe_allow_html=True)

# ------------------------------
# Sidebar content - Sage Creek themed
# ------------------------------
with st.sidebar:
    st.image("https://files.smartsites.parentsquare.com/3483/design_img__ljsgi1.png", width=80)
    st.header("About Wrestling Form Analysis", anchor=False)
    st.write("""
    Level up your wrestling with AI-powered technique analysis. Upload a video and get detailed feedback to refine your takedowns, top control, escapes, and scrambles.

    Dominate on the mat with precise technique and strategic insights! Go Bobcats!
    """)

    st.subheader("Wrestling Program Info", anchor=False)
    st.write("""

    **Head Coach:** David Steele, david.martin.steele@gmail.com

    """)

    st.subheader("Connect with Sage Creek Wrestling", anchor=False)
    st.write("""
    **Address:**
    3900 Bobcat Blvd.
    Carlsbad, CA 92010

    **Phone:** 760-331-6600
    **Email:** office.schs@carlsbadusd.net
    """)

# ------------------------------
# Agent initialization
# ------------------------------
@st.cache_resource
def initialize_agent():
    """Initialize and cache the Phi Agent with Gemini model."""
    return Agent(
        name="Wrestling Form Analyzer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_Agent = initialize_agent()
script_agent = initialize_agent()

# ------------------------------
# Session state initialization
# ------------------------------
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'audio_script' not in st.session_state:
    st.session_state.audio_script = None

if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False

# ------------------------------
# Main UI - Section Headers in Sage Creek style
# ------------------------------
st.markdown('<div class="section-header">Wrestling Technique Analyzer</div>', unsafe_allow_html=True)
st.write("Upload a video of your wrestling technique for analysis.")

video_file = st.file_uploader(
    "Upload Video",
    type=['mp4', 'mov', 'avi'],
)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    st.video(video_path, format="video/mp4", start_time=0)

    user_query = st.text_area(
        "What wrestling technique would you like analyzed?",
        placeholder="e.g., 'Analyze my single leg takedown', 'How's my top control?', 'Check my stand-up escape'",
        height=80
    )
    analyze_button = st.button("Get Analysis")

    if analyze_button:
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

                    analysis_prompt = f"""You are Cary Kolat, legendary wrestler and coach. You are meticulously analyzing a high school wrestler from Sage Creek's video to provide feedback in your signature, detail-oriented style. Analyze this wrestling video focusing on: {user_query}

Structure your analysis to deliver actionable insights, emphasizing core techniques and relentless improvement, in line with the Kolat Wrestling Philosophy as described in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'.

Structure your feedback rigorously, mirroring Cary Kolat's direct and demanding coaching approach:

## TECHNIQUE DIAGNOSIS: INITIAL IMPRESSION - NO BS.
Cut the fluff. Start with a brutally honest, immediate assessment of the wrestler's skill level.  Are they fundamentally sound or a project? Be direct. *Example: "Raw. Needs Major Work: Single leg attempt is weak. Stance is too high, no penetration, hands are lazy. Back to basics."*

## KEY FUNDAMENTAL FLAWS (Identify 2-3 CRITICAL ISSUES - PRIORITIZE)
*   Pinpoint the 2-3 ABSOLUTE MUST-FIX flaws killing their technique, based on your expert knowledge and the principles outlined in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'. Timestamp each for immediate video reference. No fluff - what will cost them matches?
*   Explain the *precise* technical breakdown.  Use Kolat's language and refer to core wrestling principles.  Focus on stance, motion, penetration, finish, top control, bottom escapes, scrambling. *Example: "Lazy Hands - [0:10]. Hands are down, not active.  You're telegraphing your shot. Active hands control ties, create openings. Fundamental flaw - see 'Mastering Core Techniques: Takedowns' in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'."*
*   Detail the *match-costing consequences*.  How will this get them beat, referencing common scenarios from high school wrestling and insights from 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'? *Example: "Lazy hands means you get collar tied, headlocked, and can't control your opponent.  You'll get beat by anyone with hand-fighting skills -  'Takedowns – High-Percentage Attacks and Finishes' in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual' emphasizes hand-fighting for a reason."*

## KOLAT DRILL PRESCRIPTION: FIX IT NOW (Assign 2-3 Game-Changing Drills)
*   Prescribe 2-3 MAX, high-rep Kolat drills to directly attack these flaws, drawing directly from drills recommended by Kolat and mentioned in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'. Drills must be practical and immediately implementable in training.
*   Explain the *EXACT PURPOSE* of each drill in Kolat's terms.  How does it build the needed muscle memory and fix the breakdown, based on Kolat's drilling philosophy described in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'? *Example: "Drill: 1000 Hand Fighting Drills This Week (see 'Drilling and Skill Progression' in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'). Purpose: Build active hand muscle memory.  Every day, before and after practice.  No excuses. Focus on speed and control, like Kolat says - 'High-Pace, Realistic Drilling'."*

## WRESTLING IQ & MINDSET - THE KOLAT NON-NEGOTIABLE
*   Deliver ONE non-negotiable mindset cue.  This is about toughness, work ethic, and the Kolat mentality of DOMINANCE, directly inspired by the 'Competition Mindset and Preparation Strategies' section of 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'.  No soft encouragement - demand better.
*   Make it a Kolat-style command, reflecting his emphasis on visualization, intensity, and mental preparation from 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'.  Direct, aggressive, and unforgettable.  *Example: "Mindset: 'Relentless Forward Pressure. Wrestle like you're attacking their will.  Dominate or get dominated.  Choose dominance.' Remember Kolat's 'Visualization and Self-Belief' - see yourself dominating, now go do it."*

Deliver this analysis with the uncompromising, technical authority of Cary Kolat.  Be brutally honest. Be direct. Be demanding.  But be effective.  Wrestlers need TRUTH to improve.  Keep it concise – under 300 words.  No wasted words.  Let's get to work.
""";
                    progress_bar.progress(80, text="Generating Kolat-Style Insights...")
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video], user_query = user_query)
                    progress_bar.progress(100, text="Analysis Complete. Get Back to Work!")
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

    # Analysis Section
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

        # Audio Options Section
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
                                Convert the following wrestling technique analysis into a monologue script as if spoken by Cary Kolat.
                                The tone MUST be direct, demanding, technically precise, and laser-focused on actionable improvement, just like Cary Kolat's signature coaching.

                                Remove ALL headings, bullet points, timestamps, or ANY fluff.
                                The script MUST be plain text and sound EXACTLY like a coach talking DIRECTLY to a wrestler, providing no-nonsense, tough feedback.

                                EMPHASIZE the critical corrections and DRILLS needed for IMMEDIATE improvement.
                                The script MUST be hyper-focused on core technique, iron-clad mindset, and relentless work ethic – the non-negotiable pillars of the Kolat philosophy, as detailed in 'Implementing Cary Kolat’s Wrestling Philosophy: A High School Coach’s Manual'.
                                Inject a sense of EXTREME URGENCY and DEMAND for INSTANT ACTION.  No soft encouragement.  Demand DOMINANCE.

                                **Analysis to convert:**
                                ```
                                {st.session_state.analysis_result}
                                ```
                                """;
                                script_response = script_agent.run(script_prompt)
                                st.session_state.audio_script = script_response.content

                            with st.spinner("Generating audio - Kolat Voice..."):
                                clean_text = st.session_state.audio_script
                                client = ElevenLabs(api_key=elevenlabs_api_key)
                                audio_generator = client.text_to_speech.convert(
                                    text=clean_text,
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

    st.write("""
    Upload a wrestling video to receive Cary Kolat-style technique analysis. Let's get to work!
    """)
    st.info("🤼 Upload a wrestling technique video above for expert AI analysis and personalized feedback, the Kolat way.")

    st.markdown('<div class="section-header">Tips for Best Analysis</div>', unsafe_allow_html=True)
    with st.expander("How to Get the Most from Your Wrestling Analysis"):
        st.markdown("""
        1. **Video Quality**: Good lighting and a clear, stable view of the wrestler and technique.
        2. **Technique Focus**: Focus on ONE technique per video for targeted, detailed feedback.
        3. **Specific Question**: Ask a specific question about the technique. 'Analyze my single leg' is better than 'Critique my wrestling.'
        4. **Multiple Reps**: Include several repetitions of the technique in the video so patterns can be identified.
        """)

    st.markdown('<div class="section-header">Technique Areas for Analysis</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Takedowns")
        st.write("""
        Single Legs, Double Legs, High Crotches, Ankle Picks - Takedowns win matches. Get analysis on your penetration, setups, and finishes.
        """)
    with col2:
        st.markdown("### Top Control & Pinning")
        st.write("""
        Riding, Turns, Pins - Top position is for scoring and ending matches. Improve your rides, half nelsons, and pinning combinations.
        """)
    with col3:
        st.markdown("### Bottom Escapes & Reversals")
        st.write("""
        Stand-Ups, Sit-Outs, Switches - Getting off bottom is essential. Perfect your escapes and reversals to avoid giving up points.
        """)

# ------------------------------
# Footer styled after Sage Creek website
# ------------------------------
st.markdown("""
    <div class="footer">
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
            <div>
                <p style="font-weight: bold; margin-bottom: 5px;">Sage Creek High School</p>
                <p style="margin: 0;">3900 Bobcat Blvd. | Carlsbad, CA 92010</p>
                <p style="margin: 0;">Phone: 760-331-6600 • office.schs@carlsbadusd.net</p>
            </div>
            <div>
                <p style="margin: 0;">Privacy Policy</p>
                <p style="margin: 0;">Site Map</p>
                <p style="margin: 0;">Accessibility</p>
                <p style="margin: 0;">Login</p>
            </div>
        </div>
        <hr style="border-color: #3D6A4D; margin: 10px 0;">
        <p style="margin: 0; font-size: 12px;">Contents © 2025 Sage Creek High School</p>
        <p style="margin: 0; font-size: 12px;">Notice of Non-Discrimination: In compliance with federal law, our school district administers all education programs, employment activities and admissions without discrimination against any person on the basis of gender, race, color, religion, national origin, age, or disability.</p>
    </div>
""", unsafe_allow_html=True)
