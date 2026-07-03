import os
import glob
import streamlit as st

# Handling moviepy version differences safely
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    from moviepy import ImageClip, AudioFileClip

import yt_dlp

# --- 1. CONFIGURATION & STATE INITIALIZATION ---
st.set_page_config(page_title="YouTube Audio Video Creator", page_icon="🎬", layout="centered")

if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None
if 'video_path' not in st.session_state:
    st.session_state['video_path'] = None
if 'yt_error' not in st.session_state:
    st.session_state['yt_error'] = None

# --- 2. CORE UTILITY FUNCTIONS ---
def cleanup_temp_files():
    """Removes all generated temporary files and resets the app state."""
    files = glob.glob("temp_*") + ["output_video.mp4"]
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass
    st.session_state['audio_path'] = None
    st.session_state['video_path'] = None
    st.session_state['yt_error'] = None
    st.rerun()

def download_youtube_audio(url):
    """Downloads audio from a YouTube link using yt_dlp and outputs an MP3."""
    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://google.com',
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])
    return "temp_audio.mp3"

# --- 3. CALLBACK HANDLERS ---
def handle_youtube_download():
    """Triggered when the user clicks 'Download Audio'."""
    url = st.session_state.get('yt_url_input', '').strip()
    if not url:
        st.session_state['yt_error'] = "Please provide a valid YouTube URL."
        return

    st.session_state['yt_error'] = None
    st.session_state['audio_path'] = None

    try:
        res_path = download_youtube_audio(url)
        if res_path and os.path.exists(res_path):
            st.session_state['audio_path'] = res_path
    except Exception as e:
        st.session_state['yt_error'] = f"Failed to download audio: {str(e)}"

# --- 4. STREAMLIT USER INTERFACE ---
st.title("🎬 YouTube Audio Video Creator")
st.write("Extract audio from a YouTube link, attach it to a static image, and export an MP4 video.")

# Sidebar Reset Controls
with st.sidebar:
    st.header("App Controls")
    if st.button("🔄 Reset & Clear Cache", use_container_width=True):
        cleanup_temp_files()

# STEP 1: YouTube Downloader UI
st.subheader("Step 1: Get YouTube Audio")
st.text_input(
    "Enter YouTube URL:", 
    key="yt_url_input", 
    placeholder="https://youtube.com..."
)

st.button(
    "📥 Extract Audio", 
    on_click=handle_youtube_download, 
    type="primary", 
    disabled=not st.session_state.get('yt_url_input')
)

# Display Step 1 Status
if st.session_state['yt_error']:
    st.error(st.session_state['yt_error'])
elif st.session_state['audio_path']:
    st.success("✅ Audio downloaded successfully!")
    st.audio(st.session_state['audio_path'])

# STEP 2: Image Upload & Rendering UI
if st.session_state['audio_path']:
    st.divider()
    st.subheader("Step 2: Upload Background Image & Generate Video")
    
    uploaded_image = st.file_uploader(
        "Choose a background image (JPG/PNG)", 
        type=["jpg", "jpeg", "png"]
    )
    
    if uploaded_image:
        st.image(uploaded_image, caption="Selected Background", width=300)
        
        if st.button("🚀 Render Video", use_container_width=True):
            with st.spinner("Processing video layers... This may take a moment."):
                try:
                    # Save uploaded file temporarily
                    img_ext = uploaded_image.name.split(".")[-1]
                    temp_img_path = f"temp_bg.{img_ext}"
                    with open(temp_img_path, "wb") as f:
                        f.write(uploaded_image.getbuffer())
                    
                    # Process with MoviePy
                    audio_clip = AudioFileClip(st.session_state['audio_path'])
                    
                    # Create image clip matched to audio length
                    video_clip = ImageClip(temp_img_path).with_duration(audio_clip.duration)
                    video_clip = video_clip.with_audio(audio_clip)
                    
                    # Render target file
                    output_file = "output_video.mp4"
                    video_clip.write_videofile(
                        output_file, 
                        fps=24, 
                        codec="libx264", 
                        audio_codec="aac"
                    )
                    
                    # Close clips to free memory system handles
                    audio_clip.close()
                    video_clip.close()
                    
                    st.session_state['video_path'] = output_file
                    
                except Exception as video_err:
                    st.error(f"Video processing failed: {str(video_err)}")

# STEP 3: Final Output Delivery
if st.session_state['video_path'] and os.path.exists(st.session_state['video_path']):
    st.divider()
    st.subheader("🎉 Your Video is Ready!")
    st.video(st.session_state['video_path'])
    
    with open(st.session_state['video_path'], "rb") as file:
        st.download_button(
            label="💾 Download MP4 Video File",
            data=file,
            file_name="created_movie.mp4",
            mime="video/mp4",
            use_container_width=True
        )
