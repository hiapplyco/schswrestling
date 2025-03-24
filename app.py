import streamlit as st
import tempfile
import time
import os
from pathlib import Path
import base64
import google.generativeai as genai 
from elevenlabs.client import ElevenLabs

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
    os.environ["GEMINI_API_KEY"] = API_KEY_GOOGLE
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
    /* Detailed Analysis Styling */
    .detailed-analysis {
        background-color: var(--sc-light-gray);
        border-left: 5px solid var(--sc-gold);
        padding: 15px;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
    }
    .analysis-progress {
        height: 25px;
        border-radius: 5px;
    }
    .processing-status {
        font-size: 1.1rem;
        font-weight: bold;
        color: var(--sc-dark-green);
        margin: 10px 0;
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
    
    # Analysis detail level slider
    analysis_detail = st.slider(
        "Analysis Detail Level", 
        min_value=1, 
        max_value=5, 
        value=3, 
        help="Higher values will produce more detailed analysis but may take longer to process."
    )
    
    # Model selection
    model_options = {
        "Quick Analysis": "gemini-2.0-flash",
        "Standard Analysis": "gemini-2.0-pro",
        "Detailed Analysis": "gemini-2.0-ultra",
    }
    selected_model = st.selectbox(
        "Analysis Model",
        options=list(model_options.keys()),
        index=0,
        help="Select the model to use for analysis. More advanced models provide more detailed feedback but may take longer."
    )
    
    st.info("Go Bobcats!")

# Session state initialization
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'audio_script' not in st.session_state:
    st.session_state.audio_script = None
if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False
if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = ""

# Function to generate analysis using Google Generative AI
def generate_analysis(video_path, user_query, analysis_detail, selected_model):
    # Create a Google Generative AI client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Upload the video file
    with open(video_path, "rb") as file:
        uploaded_file = client.files.upload(file=file)
    
    # Get the model name from the selected option
    model = model_options[selected_model]
    
    # Generate detail level text based on the slider value
    detail_level_text = {
        1: "Keep the analysis brief and focused on the most critical issues.",
        2: "Provide a standard analysis with key points and suggestions.",
        3: "Offer a comprehensive analysis with detailed feedback and specific drills.",
        4: "Create an in-depth analysis with extensive technical breakdowns and multiple drill options.",
        5: "Develop an exceptionally detailed analysis with frame-by-frame technical assessment and comprehensive improvement plan."
    }
    
    # Create the Coach Steele prompt
    coach_steele_prompt = f"""You are Coach David Steele, the wrestling coach at Sage Creek High School. You are analyzing a video to provide feedback to a high school wrestler, drawing inspiration from the intense and detail-oriented coaching methods of legends like Cary Kolat. Analyze this wrestling video focusing on: {user_query}

{detail_level_text[analysis_detail]}

Structure your analysis to deliver actionable insights, emphasizing core techniques and relentless improvement, in line with wrestling principles inspired by the Kolat Wrestling Philosophy as described in 'Implementing Cary Kolat's Wrestling Philosophy: A High School Coach's Manual'.

Structure your feedback rigorously, mirroring a direct and demanding coaching approach, while maintaining a constructive tone appropriate for high school athletes:

## TECHNIQUE DIAGNOSIS: INITIAL IMPRESSION - BE DIRECT.
Provide a clear and honest initial assessment of the wrestler's technique. Be direct but constructive.  Example: "Needs Sharpening: Single leg entry shows potential, but finish is weak. Stance needs to be lower and more consistent."

## KEY FUNDAMENTAL AREAS FOR IMPROVEMENT (Identify {"2-3" if analysis_detail <= 3 else "3-5"} CRITICAL ISSUES - PRIORITIZE)
*   Pinpoint {"2-3" if analysis_detail <= 3 else "3-5"} key areas that need the most immediate attention for improvement. Timestamp each for video reference. Focus on fundamentals.
*   Explain the *precise* technical issue. Use clear wrestling terminology, referencing core principles. Focus on stance, motion, penetration, finish, top control, bottom escapes, scrambling as relevant. Example: "Stance Too High - [0:15]. Wrestler's stance is too upright, compromising power and speed. A lower stance is crucial for effective shots and defense."
*   Detail the *impact* of these issues on wrestling performance and match outcomes. Explain how these weaknesses can be exploited by opponents at the high school level, drawing upon general wrestling knowledge and principles inspired by 'Implementing Cary Kolat's Wrestling Philosophy: A High School Coach's Manual'. Example: "High stance makes you vulnerable to faster opponents and deeper shots. You'll struggle against anyone with a strong low attack.  Remember the emphasis on 'Stance and Movement' in Kolat-inspired training."

## ACTIONABLE DRILL PRESCRIPTION:  TARGETED DRILLS FOR FIXES (Assign {"2-3" if analysis_detail <= 3 else "4-6"} Focused Drills)
*   Prescribe {"2-3" if analysis_detail <= 3 else "4-6"} specific, actionable drills to directly address the identified weaknesses. Prioritize drills that can be realistically implemented in a high school practice setting.  Reference drills that align with Kolat-inspired training methods whenever possible.
*   Explain the *specific purpose* of each drill and *how* it will lead to technical correction and skill development. Example: "Drill: Partner Penetration Step Drill (3 sets of 20 reps). Purpose: To build muscle memory for a lower, more explosive penetration step, improving shot entries. Focus on driving through with the hips, maintaining a strong base -  as emphasized in Kolat-inspired 'Penetration' drills."

## STRENGTHS TO BUILD UPON
*   Identify {"1-2" if analysis_detail <= 2 else "2-3"} specific strengths in the wrestler's technique that can be leveraged for further improvement.
*   Explain how these strengths can be used as a foundation for addressing weaknesses.

## WRESTLING IQ & MINDSET - COACH STEELE'S KEY TAKEAWAY
*   Deliver {"ONE" if analysis_detail <= 3 else "TWO"} key takeaway{"s" if analysis_detail > 3 else ""} focused on mindset or wrestling IQ.  This should be encouraging but also emphasize the importance of hard work, smart training, and continuous improvement, reflecting a Coach Steele inspired by Kolat's dedication.
*   Frame it as a memorable coaching cue or key principle. Example: "Key Takeaway: 'Be Relentless in Improvement.'  Focus on getting 1% better every practice.  Drill these corrections, visualize success, and bring intensity to every workout. That's how we build champions at Sage Creek."

{"## COMPETITION STRATEGY\n* Provide specific strategic advice for using the techniques shown in competitive matches.\n* Discuss setups, timing, and situational awareness related to the techniques analyzed." if analysis_detail >= 4 else ""}

{"## ADVANCED TECHNICAL CONSIDERATIONS\n* For a wrestler seeking to master this technique, provide advanced technical details that would elevate their performance to a higher competitive level.\n* Reference high-level wrestling concepts that align with the Kolat philosophy." if analysis_detail >= 5 else ""}

Make your analysis {"concise but informative" if analysis_detail <= 2 else "detailed and comprehensive"}. Focus on {"the most critical issues" if analysis_detail <= 3 else "both fundamental and nuanced aspects of the technique"}.
"""
    
    # Create the content structure for the API call
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=uploaded_file.uri,
                    mime_type=uploaded_file.mime_type,
                ),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=coach_steele_prompt),
            ],
        ),
    ]
    
    # Set the generation config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,  # Lower temperature for more focused analysis
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,  # Increased for more detailed responses
        response_mime_type="text/plain",
    )
    
    # Stream the response and collect it
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            response_text += chunk.text
            yield chunk.text  # Yield each chunk for streaming display
    
    return response_text

# Function to generate audio script
def generate_audio_script(analysis_text, voice_style="Balanced"):
    # Create a Google Generative AI client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Adjust script prompt based on voice style
    intensity_level = {
        "Calm": "encouraging but firm",
        "Balanced": "direct and focused",
        "Intense": "intense and demanding"
    }
    
    script_prompt = f"""
Convert the following wrestling technique analysis into a monologue script as if spoken by Coach David Steele.
The tone MUST be {intensity_level[voice_style]}, and hyper-focused on actionable corrections and drills. Remove all headings, bullet points, timestamps, and fluff. The final script should sound like a coach talking directly to a wrestler – no-nonsense, tough, and urgent.

Analysis to convert:

{analysis_text}
    """
    
    # Set the generation config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,  # Higher temperature for more natural speech
        top_p=0.95,
        top_k=40,
        max_output_tokens=4096,
        response_mime_type="text/plain",
    )
    
    # Generate the audio script
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": [{"text": script_prompt}]}],
        generation_config=generate_content_config,
    )
    
    return response.text

# Main UI Header
st.write("Upload a video of your wrestling technique for analysis.")

# Video upload button
video_file = st.file_uploader("Upload Video", type=['mp4', 'mov', 'avi'])

if video_file:
    # Display file info for longer videos
    file_details = {"FileName": video_file.name, "FileType": video_file.type, "FileSize": f"{video_file.size / (1024 * 1024):.2f} MB"}
    st.write(f"**File Details:** {file_details['FileName']} ({file_details['FileSize']} MB)")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    # Display video preview with an option to remove the preview
    preview_placeholder = st.empty()
    with preview_placeholder.container():
        st.video(video_path, format="video/mp4", start_time=0)
        if st.button("Close Video Preview"):
            preview_placeholder.empty()

    # Analysis options
    user_query = st.text_area(
        "What wrestling technique would you like analyzed?",
        placeholder="e.g., 'Analyze my single leg takedown', 'How's my top control?', 'Check my stand-up escape'",
        height=80
    )
    
    # Additional context input for more detailed analysis
    if analysis_detail >= 3:
        additional_context = st.text_area(
            "Additional Context (Optional)",
            placeholder="e.g., 'I've been working on this for 2 weeks', 'This is for an upcoming tournament', 'I struggle with the finish'",
            height=60
        )
    else:
        additional_context = ""
    
    if st.button("Get Analysis"):
        if not user_query:
            st.warning("Please enter a wrestling technique you want analyzed.")
        else:
            try:
                with st.spinner("Analyzing video and generating feedback..."):
                    progress_bar = st.progress(0)
                    st.session_state.processing_status = "Uploading video..."
                    status_placeholder = st.empty()
                    status_placeholder.markdown(f'<p class="processing-status">{st.session_state.processing_status}</p>', unsafe_allow_html=True)
                    progress_bar.progress(10, text="Uploading...")
                    
                    # Update progress and status
                    progress_bar.progress(30, text="Processing...")
                    st.session_state.processing_status = "Processing video... This may take a few moments for longer videos."
                    status_placeholder.markdown(f'<p class="processing-status">{st.session_state.processing_status}</p>', unsafe_allow_html=True)
                    
                    # Update status
                    progress_bar.progress(60, text="Analyzing Technique...")
                    st.session_state.processing_status = "Analyzing wrestling technique..."
                    status_placeholder.markdown(f'<p class="processing-status">{st.session_state.processing_status}</p>', unsafe_allow_html=True)
                    
                    # Analysis result placeholder for streaming
                    analysis_placeholder = st.empty()
                    
                    # Create a full query combining the user query and additional context
                    full_query = user_query
                    if additional_context:
                        full_query += f"\n\nAdditional context: {additional_context}"
                    
                    # Stream the analysis results
                    result_text = ""
                    for text_chunk in generate_analysis(video_path, full_query, analysis_detail, selected_model):
                        result_text += text_chunk
                        analysis_placeholder.markdown(result_text)
                        
                        # Update progress as we receive chunks
                        progress_percent = min(60 + len(result_text) / 100, 95)
                        progress_bar.progress(int(progress_percent), text="Generating Analysis...")
                    
                    # Store the full result
                    st.session_state.analysis_result = result_text
                    
                    # Complete the progress
                    progress_bar.progress(100, text="Analysis Complete. Keep Working Hard!")
                    st.session_state.processing_status = "Analysis complete! Review your feedback below."
                    status_placeholder.markdown(f'<p class="processing-status">{st.session_state.processing_status}</p>', unsafe_allow_html=True)
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_placeholder.empty()
                    
                    # Reset the audio state
                    st.session_state.audio_generated = False
                    st.session_state.show_audio_options = False
                    st.session_state.audio_script = None

            except Exception as error:
                st.error(f"Analysis error: {error}")
                st.info("Try uploading a shorter video or check your internet connection.")
            finally:
                # Clean up the temporary file
                Path(video_path).unlink(missing_ok=True)

    # Display analysis results if available
    if st.session_state.analysis_result:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.subheader("Wrestling Technique Analysis")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Analysis",
                data=st.session_state.analysis_result,
                file_name="wrestling_technique_analysis.md",
                mime="text/markdown"
            )
        
        with col2:
            if st.button("Listen to Analysis (Audio Options)"):
                st.session_state.show_audio_options = True

        if st.session_state.show_audio_options:
            with st.expander("Audio Voice Settings", expanded=True):
                st.subheader("Voice Options")
                elevenlabs_api_key = API_KEY_ELEVENLABS
                selected_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
                
                # ElevenLabs voice options
                if elevenlabs_api_key:
                    try:
                        client = ElevenLabs(api_key=elevenlabs_api_key)
                        voice_data = client.voices.get_all()
                        voices_list = [v.name for v in voice_data.voices]
                        
                        # Voice settings
                        col1, col2 = st.columns(2)
                        with col1:
                            selected_voice_name = st.selectbox("Choose Voice", options=voices_list, index=0)
                        with col2:
                            voice_style = st.select_slider(
                                "Voice Style",
                                options=["Calm", "Balanced", "Intense"],
                                value="Balanced",
                                help="Adjust the coaching intensity of the voice"
                            )
                        
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
                                # Generate the audio script
                                st.session_state.audio_script = generate_audio_script(
                                    st.session_state.analysis_result, 
                                    voice_style
                                )

                            with st.spinner(f"Generating audio - Coach Steele Voice ({voice_style} Intensity)..."):
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
