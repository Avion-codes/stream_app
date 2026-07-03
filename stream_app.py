import streamlit as st 
import os 
import glob 
# handling Moviepy version difference (v1.x vs v2.x)
try:
  from moviepy.editor import ImportClip, cocatenate_videoclips, AudioFlieClip
except ImportError:
  from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
import yt-dlp
 # --- 1.Initialize state --
if 'audio_path' not in st.session_state:
  st.session_state['audio_path'] = None
if 'yt_error' in st.session_state:
  pass 

#--2.Define all fumctions --
def cleanup_temp_files():
  """Removes temporary files and resets memory."""
  files = glob.glob("temp_")+["output_video.mp4"]
  for  f in files:
    try:
      os.remove(f)
    except:
      pass
  st.session_state['audio-path'] = None
  if 'yt_error' in st.session_state:
    del st.session_state['yt_error']

def download_youtube_audio(url):
  """Downloads only audio from Youtube using reliable browser impresonation."""
  audio_opts = {
    'format' : 'bestaudio/best',
    'outtmpl' : 'temp_audio.%(ext)s',
    'http_headers' : {
      'User-Agent' : "Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/12
      'Accept' : '*/*',
      'Referer' : 'https://www.google.com/',

    },
    'postprocessors':[{
      'key' : 'FFmpegExtractAudio',
       preferredcod
