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
    page_title="Sage Creek Wrestling Analyzer - Powered by Kolat Method",
    page_icon="🤼",
    layout="wide"
)

# ------------------------------
# Utility Functions for Background (REMOVED)
# ------------------------------
# Background and custom CSS are being significantly simplified for clarity.

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
# Basic CSS styling - now much simpler
# ------------------------------
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .analysis-section {
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0474b5; /* Sage Creek Blue accent - Example */
        margin-top: 20px;
        background-color: #f9f9f9; /* Light background for analysis */
    }
    .stButton button {
        background-color: #0474b5; /* Sage Creek Blue button - Example */
        color: white;
    }
    .stDownloadButton button {
        background-color: #4CAF50; /* Example: Green for download */
        color: white;
    }

    /* Centralize elements for cleaner look on larger screens */
    .stFileUploader, .stTextArea, .stButton, .stDownloadButton, .stAudio, .stVideo {
        max-width: 800px; /* Adjust as needed */
        margin-left: auto;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# Header - Simplified - Wrestling Focused
# ------------------------------
st.image("https://sagecreekhs.net/wp-content/uploads/2023/07/cropped-SageCreek_favicon-32x32.png", width=100) # Sage Creek Logo - Replace with actual wrestling logo if available
st.title("Sage Creek High School Wrestling Analyzer")
st.markdown("Get Cary Kolat-style feedback on your wrestling technique.") # Clear subtitle as CTA

# ------------------------------
# Sidebar content - Kept, but now Wrestling themed
# ------------------------------
with st.sidebar:
    st.image("https://sagecreekhs.net/wp-content/uploads/2023/07/cropped-SageCreek_favicon-32x32.png", width=80) # Smaller sidebar logo - Replace with actual wrestling logo if available
    st.header("About Wrestling Form Analysis", anchor=False) # anchor=False to remove streamlit warning
    st.write("""
    Level up your wrestling with AI-powered technique analysis, inspired by Cary Kolat's legendary coaching. Upload a video and get detailed feedback to refine your takedowns, top control, escapes, and scrambles.

    Dominate on the mat with precise technique and strategic insights! Go Coyotes!
    """)

    st.subheader("Connect with Sage Creek Wrestling", anchor=False) # Example Contact info - adapt as needed
    st.write("""
    **Visit the Sage Creek High School Athletics Website**: [Sage Creek Athletics](https://sagecreekhs.net/athletics/)  (Example Link)

    **Find a Wrestling Club**: [USA Wrestling Club Finder](https://www.usawmembership.com/club_search) (Example Link)
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
script_agent = initialize_agent() # Initialize a second agent for script generation

# ------------------------------
# Session state initialization
# ------------------------------
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'audio_script' not in st.session_state: # New session state for audio script
    st.session_state.audio_script = None

if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False

# ------------------------------
# Main UI - Streamlined Landing and Video Analysis - Wrestling focused
# ------------------------------
st.write(" ") # Adding some whitespace
st.write("Upload a video of your wrestling technique for analysis.") # More direct instruction

video_file = st.file_uploader(
    "Upload Wrestling Technique Video", # Clearer label - Wrestling specific
    type=['mp4', 'mov', 'avi'],
    help="Upload a video of your wrestling technique to receive Cary Kolat-style feedback." # Help text updated
)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    st.video(video_path, format="video/mp4", start_time=0)

    user_query = st.text_area(
        "What wrestling technique would you like analyzed?", # More user-focused question - Wrestling specific
        placeholder="e.g., 'Analyze my single leg takedown', 'How's my top control?', 'Check my stand-up escape'", # Placeholders updated
        height=80 # Reduced height for text area
    )
    analyze_button = st.button("Get Kolat-Style Analysis") # Stronger CTA button text - Wrestling specific

    if analyze_button:
        if not user_query:
            st.warning("Please enter a wrestling technique you want analyzed.") # Warning updated
        else:
            try:
                with st.spinner("Analyzing video and generating Cary Kolat-style feedback..."): # Spinner text updated
                    progress_bar = st.progress(0)
                    progress_bar.progress(10, text="Uploading...")
                    processed_video = upload_file(video_path)

                    progress_bar.progress(30, text="Processing...")
                    processing_start = time.time()
                    while processed_video.state.name == "PROCESSING":
                        if time.time() - processing_start > 60:
                            st.warning("Video processing is taking longer than expected. Please be patient, champion.") # Cary Kolat style patience encouragement
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)

                    progress_bar.progress(60, text="Analyzing Technique...") # Progress text updated

                    analysis_prompt = f"""You are Cary Kolat, legendary wrestler and coach. You are meticulously analyzing a high school wrestler's video to provide feedback in your signature, detail-oriented style.  Analyze this wrestling video focusing on: {user_query}

Structure your analysis to deliver actionable insights, emphasizing core techniques and relentless improvement. Focus on fundamentals across neutral, top, bottom, and scramble positions, reflecting Kolat's coaching pillars.

Structure your feedback rigorously, mirroring Cary Kolat's coaching approach:

## TECHNIQUE DIAGNOSIS & INITIAL IMPRESSION
Start with an immediate, direct assessment of the wrestler's skill level and overall technique in the video. Be as precise as if you were cornering them at a major tournament. *Example: "Needs Improvement: Shows some understanding of the single leg, but lacks crucial details in penetration and finish. Stance is too high, needs more motion."*

## KEY STRENGTHS (Identify 1-2 Foundational Elements - Be Selective)
*   Pinpoint 1-2 elements where the wrestler shows solid fundamentals or potential. Include timestamps for focused review.  Don't overpraise, keep it technical.
*   Briefly explain *why* these are strengths based on wrestling biomechanics and Kolat's core principles. *Example: "Good hand fighting - timestamp [0:15]. Wrestler uses active hands to clear ties and create space, fundamental for setting up shots."*

## CRITICAL CORRECTIONS (Prioritize 2-3 - High-Impact, Actionable)
*   Zero in on the 2-3 MOST critical technical flaws hindering their immediate progress. Provide timestamps for precise correction.
*   Explain the *exact* biomechanical principle being violated in Kolat's terms. *Example: "High Stance - timestamp [0:25]. Stance is too upright. Needs to lower center of gravity to improve shot penetration and defense. 'Low stance, fast hands, always moving' - that's wrestling."*
*   Detail the *direct consequences* of these errors in wrestling matches. *Example: "High stance makes you vulnerable to leg attacks and slower to react defensively. You'll get shot on by anyone with a good low single."*

## KOLAT DRILL PRESCRIPTION (Assign 1-2 Focused Drills - High Repetition)
*   Prescribe 1-2 specific, high-repetition drills directly from the Kolat system to fix the identified weaknesses. Drills should be practical and immediately implementable in training.
*   Explain the *purpose* of each drill and *how* it corrects the flaw. *Example: "Drill: 500 Penetration Steps Daily. Purpose: Builds muscle memory for low stance and explosive penetration. Do this until it's automatic - every day."*

## MINDSET & WRESTLING IQ CUE (The 'Kolat Mindset' Takeaway)
*   Provide ONE key mindset cue or piece of wrestling IQ advice that embodies Kolat's mental approach. This should be direct, demanding, and focused on relentless improvement.
*   This should be a 'Kolat-ism' – concise, memorable, and impactful. *Example: "Mindset: 'Dominate Every Position.'  Wrestling isn't about just scoring - it's about control. Ride tougher, shoot faster, scramble harder. Dominate."*

Deliver your analysis with the directness, technical expertise, and demanding yet motivational tone of Cary Kolat. Use precise wrestling terminology. Be brutally honest but always with the goal of improvement. Keep it concise, actionable, and under 350 words – Kolat is efficient and to the point.
"""
                    progress_bar.progress(80, text="Generating Kolat-Style Insights...") # Progress text updated
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
                    progress_bar.progress(100, text="Analysis Complete. Let's get to work!") # Progress text updated - Kolat style
                    time.sleep(0.5)
                    progress_bar.empty()

                    st.session_state.analysis_result = response.content
                    st.session_state.audio_generated = False
                    st.session_state.show_audio_options = False
                    st.session_state.audio_script = None # Reset audio script when new analysis is generated

            except Exception as error:
                st.error(f"Analysis error: {error}") # Error message kept general
                st.info("Try uploading a shorter video or check your internet connection. Get back to work.") # Info message kept general - Kolat style
            finally:
                Path(video_path).unlink(missing_ok=True)

    # Analysis Section - Displayed regardless of audio options
    if st.session_state.analysis_result:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.subheader("Cary Kolat Technique Analysis") # Subheader updated
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="Download Analysis", # Clearer label
            data=st.session_state.analysis_result,
            file_name="wrestling_technique_analysis.md", # Filename updated
            mime="text/markdown"
        )

        # Audio Options Section - Now consistently below analysis
        if st.button("Listen to Analysis (Audio Options)"): # More informative button
            st.session_state.show_audio_options = True

        if st.session_state.show_audio_options:
            with st.expander("Audio Voice Settings", expanded=True): # Clearer expander title
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
                        st.warning(f"Could not retrieve voices: {e}. Using default voice.") # Include error in warning
                        selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                else:
                    st.error("ElevenLabs API key missing.")

                if st.button("Generate Audio Analysis"): # Clear CTA for audio generation
                    if elevenlabs_api_key:
                        try:
                            with st.spinner("Preparing audio script - Kolat Style..."): # New spinner for script generation - Kolat style
                                script_prompt = f"""
                                Convert the following wrestling technique analysis into a monologue script as if spoken by Cary Kolat.  The tone should be direct, demanding, technically precise, and focused on actionable improvement, just like Cary Kolat's coaching style.

                                Remove all headings, bullet points, timestamps or any special characters.  The script should be plain text and sound like a coach talking directly to a wrestler, providing no-nonsense feedback.

                                Emphasize the critical corrections and drills needed for improvement. The script should be highly focused on technique, mindset, and relentless work ethic - key elements of the Kolat philosophy. Inject a sense of urgency and demand for immediate action.

                                **Analysis to convert:**
                                ```
                                {st.session_state.analysis_result}
                                ```
                                """
                                script_response = script_agent.run(script_prompt) # Use script_agent
                                st.session_state.audio_script = script_response.content # Store the script

                            with st.spinner("Generating audio - Kolat Voice..."): # New spinner for audio generation - Kolat style
                                clean_text = st.session_state.audio_script # Use audio_script for TTS
                                client = ElevenLabs(api_key=elevenlabs_api_key)
                                # **Modified Audio Generation Code:**
                                audio_generator = client.text_to_speech.convert(
                                    text=clean_text,
                                    voice_id=selected_voice_id,
                                    model_id="eleven_multilingual_v2"
                                )
                                audio_bytes = b"" # Initialize empty bytes
                                for chunk in audio_generator:
                                    audio_bytes += chunk # Accumulate audio chunks
                                st.session_state.audio = audio_bytes # Store audio bytes in session state
                                st.session_state.audio_generated = True

                                st.audio(st.session_state.audio, format="audio/mp3") # Play audio from bytes
                                st.download_button(
                                    label="Download Audio Analysis", # Clearer label
                                    data=st.session_state.audio, # Download audio from bytes
                                    file_name="wrestling_analysis_audio.mp3", # Filename updated
                                    mime="audio/mp3"
                                )
                        except Exception as e:
                            st.error(f"Audio generation error: {str(e)}") # Error message kept general
                    else:
                        st.error("ElevenLabs API key needed for audio.")

else:
    st.write("""
    Upload a wrestling video to receive Cary Kolat-style technique analysis. Let's get to work!
    """) # Welcome message updated - Kolat style
    st.info("🤼 Upload a wrestling technique video above for expert AI analysis and personalized feedback, the Kolat way.") # Info message as CTA - Wrestling specific and Kolat style
    st.subheader("Tips for Best Analysis - Focus Like Kolat") # Tips section - updated - Kolat style
    with st.expander("How to Get the Most from Your Wrestling Analysis"): # Expander label updated - Kolat style
        st.markdown("""
        1. **Video Quality - Clear View**: Good lighting and a clear, stable view of the wrestler and technique. No excuses.
        2. **Technique Focus - One Thing at a Time**: Focus on ONE technique per video for targeted, detailed feedback. Don't show me everything at once.
        3. **Specific Question - Be Precise**: Ask a specific question about the technique.  'Analyze my single leg' is better than 'Critique my wrestling.' Be specific.
        4. **Multiple Reps - Show the Movement**: Include several repetitions of the technique in the video so I can see the pattern. Show me you've drilled it.
        """)

    st.subheader("Technique Areas for Analysis - Master the Fundamentals") # Section header - updated - Kolat style
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Takedowns - Neutral Domination") # Sub-subheader for better visual hierarchy - updated - Kolat style
        st.write("""
        Single Legs, Double Legs, High Crotches, Ankle Picks - Takedowns win matches. Let's analyze your penetration, setups, and finishes. Dominate neutral.
        """)
    with col2:
        st.markdown("### Top Control & Pinning - Ride Tough") # Sub-subheader for better visual hierarchy - updated - Kolat style
        st.write("""
        Riding, Turns, Pins - Top position is for scoring and ending matches. Show me your rides, half nelsons, and pinning combinations.  Ride tougher.
        """)
    with col3:
        st.markdown("### Bottom Escapes & Reversals - Get Off Bottom") # Sub-subheader for better visual hierarchy - updated - Kolat style
        st.write("""
        Stand-Ups, Sit-Outs, Switches - Getting off bottom is non-negotiable.  Let's see your escapes and reversals. Don't give up points on bottom.
        """)

    st.markdown("---") # Divider for visual separation

    st.subheader("Sage Creek Wrestling - Built on Technique and Hard Work") # Testimonials section -  Sage Creek Specific if possible, otherwise general wrestling mindset
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        "The Wrestling Analyzer helped me dial in my single leg finish - Coach Kolat's feedback was like having him matside!" - [Wrestler Name], Sage Creek High School Wrestling
        """) # Example testimonial - needs to be updated - Sage Creek Specific if possible
    with col2:
        st.info("""
        "I used to get stuck on bottom. The analysis pinpointed my base issues, and the drills are already making a difference. Thanks Coach Kolat AI!" - [Wrestler Name 2], Sage Creek Coyote Wrestler
        """) # Example testimonial - needs to be updated - Sage Creek Specific if possible

    st.write("**Technique Wins. Dominate the Details. Let's Go!**") # Motivational quote - Wrestling/Kolat themed
content_copy
download
Use code with caution.
Python
