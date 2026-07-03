import streamlit as st
import os
import glob

# Handling MoviePy version differences (v1.x vs v2.x)
try:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
except ImportError:
    from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
import yt_dlp

# --- 1. INITIALIZE STATE ---
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None

# --- 2. DEFINE ALL FUNCTIONS ---

def cleanup_temp_files():
    """Removes temporary files and resets memory."""
    # Pattern to catch temp_audio, temp_img_*, etc.
    files = glob.glob("temp_*") + ["output_video.mp4"]
    for f in files:
        try:
            os.remove(f)
        except:
            pass
    st.session_state['audio_path'] = None
    if 'yt_error' in st.session_state:
        del st.session_state['yt_error']

def download_youtube_audio(url):
    """Downloads only audio from YouTube using reliable browser impersonation."""
    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.google.com/',
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])
    return "temp_audio.mp3"

def handle_youtube_download(url):
    """Callback function to ensure session state persists after button click."""
    try:
        if 'yt_error' in st.session_state:
            del st.session_state['yt_error']
            
        res_path = download_youtube_audio(url)
        if res_path:
            st.session_state['audio_path'] = res_path
    except Exception as e:
        st.session_state['yt_error'] = str(e)
        st.session_state['audio_path'] = None

def create_video(image_files, duplicate_count, fps, audio_path):
    """Processes images and merges with audio using MoviePy 2.0+ syntax."""
    clips = []
    duration_per_image = duplicate_count / fps
    target_resolution = (1280, 720) 
    temp_images = []

    try:
        for idx, img_file in enumerate(image_files):
            temp_img_path = f"temp_img_{idx}.png"
            temp_images.append(temp_img_path)
            with open(temp_img_path, "wb") as f:
                f.write(img_file.getbuffer())
            
            # MoviePy 2.0+ syntax safely structured
            clip = ImageClip(temp_img_path).with_duration(duration_per_image)
            clip = clip.resized(target_resolution) 
            clips.append(clip)
        
        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.with_fps(fps)
        
        audio_clip = AudioFileClip(audio_path)
        if audio_clip.duration > final_video.duration:
            audio_clip = audio_clip.with_duration(final_video.duration)

        final_clip = final_video.with_audio(audio_clip)
        
        output_filename = "output_video.mp4"
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")
        
        # Explicitly close clips to release file locks
        final_clip.close()
        audio_clip.close()
        
        return output_filename

    finally:
        # Clean up frames immediately to prevent disk bloating
        for img in temp_images:
            try:
                os.remove(img)
            except:
                pass

# --- 3. STREAMLIT UI LOGIC ---

st.set_page_config(page_title="PragyanAI Video Creator", layout="wide")

if os.path.exists("PragyanAI_Transperent.png"):
    st.image("PragyanAI_Transperent.png")

st.title("PragyanAI - Multimedia Merger")
st.markdown("Upload multiple images, specify timing, and add audio from a file or YouTube.")

with st.sidebar:
    st.header("Video Settings")
    fps = st.slider("Frames Per Second (FPS)", 1, 60, 24)
    duplicates = st.number_input("Frames per Image", min_value=1, value=48)
    
    if st.button("Clear Cache & Temp Files", use_container_width=True):
        cleanup_temp_files()
        st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Images")
    uploaded_images = st.file_uploader("Upload Image Sequence", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if uploaded_images:
        st.write(f"✅ {len(uploaded_images)} images uploaded.")
        st.info(f"Total Video Duration: {(len(uploaded_images) * duplicates) / fps:.2f} seconds")

with col2:
    st.subheader("2. Audio")
    # Reset audio path logic if source changes to prevent cross-contamination
    audio_source = st.radio("Source", ["Upload File", "YouTube Link"], key="audio_src_toggle")
    
    if audio_source == "Upload File":
        uploaded_audio = st.file_uploader("Upload Audio", type=["mp3", "wav"])
        if uploaded_audio:
            manual_path = "temp_audio_manual.mp3"
            with open(manual_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())
            st.session_state['audio_path'] = manual_path
            if 'yt_error' in st.session_state:
                del st.session_state['yt_error']
    else:
        yt_url = st.text_input("Enter YouTube URL")
        if yt_url:
            st.button("Fetch YouTube Audio", 
                      on_click=handle_youtube_download, 
                      args=(yt_url,))
            
            if 'yt_error' in st.session_state:
                st.error(f"Download Error: {st.session_state['yt_error']}")
                st.info("💡 YouTube often blocks cloud servers. Use 'Upload File' as a fallback.")

# Persistent Status Check
st.write("---")
current_audio = st.session_state.get('audio_path')
if current_audio and os.path.exists(current_audio):
    st.success(f"🎵 **Audio Status:** Loaded and Ready ({current_audio})")
else:
    st.warning("🎵 **Audio Status:** Not Loaded or File Missing")

# --- 4. FINAL GENERATION ---
st.divider()
if st.button("🚀 Create & Play Video", use_container_width=True):
    if uploaded_images and st.session_state.get('audio_path') and os.path.exists(st.session_state['audio_path']):
        try:
            with st.spinner("Rendering video... This may take a minute."):
                video_file = create_video(uploaded_images, duplicates, fps, st.session_state['audio_path'])
                st.video(video_file)
                
                with open(video_file, "rb") as f:
                    st.download_button("📥 Download Result", f, file_name="my_video.mp4")
        except Exception as e:
            st.error(f"An error occurred during video creation: {e}")
    else:
        st.warning("Please ensure images are uploaded and audio is fully 'Loaded and Ready'.")
