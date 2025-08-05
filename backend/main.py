from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv
import uuid
import requests
import yt_dlp
import json
import google.generativeai as genai
import assemblyai as aai

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define request model for JSON data
class VideoRequest(BaseModel):
    url: str

app = FastAPI()

# Configure CORS - in production, restrict this to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Kubernetes deployment
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Set your API keys here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # For enhanced transcript formatting
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "fd4536c52e784a27904d197e965906cf")  # For actual transcription

# Configure the APIs
genai.configure(api_key=GEMINI_API_KEY)
aai.settings.api_key = ASSEMBLYAI_API_KEY

# Basic test endpoint
@app.get("/")
async def root():
    return {"message": "YouTube to Text API is running"}

# Test endpoint for debugging
@app.get("/test/")
async def test_endpoint():
    return {"message": "Test endpoint is working"}

# Echo endpoint for testing
@app.post("/echo/")
async def echo_endpoint(request: VideoRequest):
    return {"received_url": request.url}

def download_audio(url, output_folder="audio"):
    """Download audio from YouTube URL without requiring FFmpeg"""
    try:
        logger.info(f"Starting YouTube download for URL: {url}")
        
        # Fix for YouTube URL formats
        if 'youtu.be' in url:
            # Convert youtu.be format to full youtube.com format
            video_id = url.split('/')[-1].split('?')[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
        elif '&' in url:
            # Remove everything after &
            url = url.split('&')[0]
            
        logger.info(f"Processed URL: {url}")
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Ensure output folder is absolute path
        output_folder = os.path.abspath(output_folder)
            
        # Generate unique filename
        filename = f"{uuid.uuid4()}.webm"  # Use webm format which works well without FFmpeg
        file_path = os.path.join(output_folder, filename)
        
        # Use yt-dlp to download the audio without FFmpeg
        try:
            # Simple download configuration without FFmpeg dependency
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': file_path,
                'noplaylist': True,
                'no_warnings': False,
                'ignoreerrors': True,
                'quiet': False,
                'postprocessors': [],  # No FFmpeg post-processors
            }
            
            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Downloading audio...")
                ydl.download([url])
                
            # Verify the file exists and has content
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                logger.warning(f"Downloaded file missing or empty: {file_path}")
                # Try with specific audio format
                ydl_opts_alternate = {
                    'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',
                    'outtmpl': file_path,
                    'noplaylist': True,
                    'ignoreerrors': True,
                    'quiet': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_alternate) as ydl:
                    logger.info("Trying alternate download method...")
                    ydl.download([url])
                
            # Final check if we have a valid file
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise HTTPException(status_code=500, detail="Failed to download audio file")
                
            logger.info(f"Successfully downloaded audio to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            # Check for specific error patterns to provide better feedback
            error_str = str(e).lower()
            if 'age' in error_str or 'restrict' in error_str:
                raise HTTPException(status_code=403, detail="The video is age-restricted and requires authentication")
            elif 'private' in error_str:
                raise HTTPException(status_code=403, detail="The video is private and cannot be accessed")
            elif 'available' in error_str or 'exist' in error_str:
                raise HTTPException(status_code=404, detail="The video is unavailable or does not exist")
            else:
                raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")
                
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions as is
        raise http_ex
    except Exception as e:
        logger.error(f"Unhandled error in download_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")

def download_audio_and_get_info(url, output_folder="audio"):
    """Download audio from YouTube URL and extract video information"""
    try:
        logger.info(f"Starting YouTube download and info extraction for URL: {url}")
        
        # Fix for YouTube URL formats
        if 'youtu.be' in url:
            # Convert youtu.be format to full youtube.com format
            video_id = url.split('/')[-1].split('?')[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
        elif '&' in url:
            # Remove everything after &
            url = url.split('&')[0]
            
        logger.info(f"Processed URL: {url}")
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Ensure output folder is absolute path
        output_folder = os.path.abspath(output_folder)
            
        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"  # Use mp3 format
        file_path = os.path.join(output_folder, filename)
        
        # Extract video information first
        video_info = {}
        try:
            with yt_dlp.YoutubeDL({'quiet': False}) as ydl:
                logger.info("Extracting video information...")
                info = ydl.extract_info(url, download=False)
                
                # Extract useful metadata
                video_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'description': info.get('description', 'No description available'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown Uploader'),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown Date'),
                    'categories': info.get('categories', []),
                    'tags': info.get('tags', []),
                    'channel_url': info.get('channel_url', ''),
                }
                logger.info(f"Video info extracted: {video_info['title']}")
        except Exception as e:
            logger.error(f"Error extracting video information: {str(e)}")
            video_info = {'title': 'Unknown', 'description': 'Failed to extract video information'}
        
        # Use yt-dlp to download the audio
        try:
            # Simple download configuration without FFmpeg dependency
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': file_path,
                'noplaylist': True,
                'ignoreerrors': True,
                'quiet': False,
                'postprocessors': [],  # No FFmpeg post-processors
            }
            
            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Downloading audio...")
                ydl.download([url])
                
            # Verify the file exists and has content
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                logger.warning(f"Downloaded file missing or empty: {file_path}")
                # Try with specific audio format
                ydl_opts_alternate = {
                    'format': 'bestaudio[ext=m4a]/bestaudio',
                    'outtmpl': file_path,
                    'noplaylist': True,
                    'ignoreerrors': True,
                    'quiet': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_alternate) as ydl:
                    logger.info("Trying alternate download method...")
                    ydl.download([url])
                
            # Final check if we have a valid file
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise HTTPException(status_code=500, detail="Failed to download audio file")
                
            logger.info(f"Successfully downloaded audio to: {file_path}")
            return file_path, video_info
            
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            # Check for specific error patterns to provide better feedback
            error_str = str(e).lower()
            if 'age' in error_str or 'restrict' in error_str:
                raise HTTPException(status_code=403, detail="The video is age-restricted and requires authentication")
            elif 'private' in error_str:
                raise HTTPException(status_code=403, detail="The video is private and cannot be accessed")
            elif 'available' in error_str or 'exist' in error_str:
                raise HTTPException(status_code=404, detail="The video is unavailable or does not exist")
            else:
                raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")
                
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions as is
        raise http_ex
    except Exception as e:
        logger.error(f"Unhandled error in download_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")

def transcribe_with_assemblyai(audio_path):
    """Transcribe audio file using AssemblyAI API"""
    try:
        logger.info(f"Starting transcription with AssemblyAI for {audio_path}")
        
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise HTTPException(status_code=500, detail="Audio file not found")
        
        # Configure AssemblyAI with best speech model
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            punctuate=True,
            auto_chapters=False,
            speaker_labels=False
        )
        
        # Create transcriber and transcribe the audio file
        transcriber = aai.Transcriber(config=config)
        logger.info("Uploading and transcribing audio file...")
        
        transcript = transcriber.transcribe(audio_path)
        
        # Check if transcription was successful
        if transcript.status == "error":
            logger.error(f"AssemblyAI transcription failed: {transcript.error}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        logger.info(f"Transcription complete with {len(transcript.text)} characters")
        return transcript.text
        
    except Exception as e:
        logger.error(f"Error in transcribe_with_assemblyai: {str(e)}")
        if "API key" in str(e).lower():
            raise HTTPException(
                status_code=500, 
                detail="Invalid AssemblyAI API key. Please update your API key in the configuration."
            )
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")

def enhance_transcript_with_gemini(transcript_text, video_info):
    """Enhance the raw transcript with video context using Gemini API"""
    try:
        logger.info("Enhancing transcript with video context using Gemini")
        
        # Create a Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Format duration in minutes and seconds
        duration_mins = video_info['duration'] // 60
        duration_secs = video_info['duration'] % 60
        
        # Format upload date
        upload_date = video_info['upload_date']
        if len(upload_date) == 8:  # YYYYMMDD format
            upload_date = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            
        # Prepare tags and categories as comma-separated strings
        tags = ', '.join(video_info.get('tags', [])[:10]) if video_info.get('tags') else 'None'
        categories = ', '.join(video_info.get('categories', [])) if video_info.get('categories') else 'None'
        
        # Create a prompt to enhance the transcript
        prompt = f"""
Please format and enhance this YouTube video transcript with proper structure and context. Here's the video information:

VIDEO METADATA:
Title: {video_info['title']}
Creator: {video_info['uploader']}
Duration: {duration_mins} minutes and {duration_secs} seconds
Upload Date: {upload_date}
Views: {video_info['view_count']}
Categories: {categories}
Tags: {tags}

RAW TRANSCRIPT:
{transcript_text}

Please:
1. Add proper formatting with paragraphs and sections
2. Add a brief introduction with video metadata
3. Clean up any obvious transcription errors
4. Add timestamps every few minutes
5. Maintain the original meaning and content
6. Make it easy to read and well-structured

Return the enhanced transcript in a clean, readable format.
"""
        
        # Generate enhanced content
        response = model.generate_content(prompt)
        
        # Extract the enhanced text
        try:
            if hasattr(response, 'text'):
                enhanced_text = response.text
            else:
                enhanced_text = str(response)
                if hasattr(response, 'parts') and response.parts:
                    enhanced_text = response.parts[0].text
        except Exception as e:
            logger.warning(f"Error enhancing transcript with Gemini: {str(e)}")
            # Return original transcript if enhancement fails
            return f"**{video_info['title']}**\n\n{transcript_text}"
        
        logger.info("Transcript enhancement complete")
        return enhanced_text
        
    except Exception as e:
        logger.warning(f"Error enhancing transcript: {str(e)}")
        # Return original transcript with basic formatting if enhancement fails
        return f"**{video_info['title']}**\n\n{transcript_text}"

def cleanup_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove file {file_path}: {str(e)}")

# Form-based endpoint (backward compatibility)
@app.post("/transcribe/")
async def transcribe_endpoint(url: str = Form(...)):
    audio_file = None
    
    try:
        logger.info(f"Received URL via form: {url}")
        
        # Validate the URL
        if not url or (not "youtube.com" in url and not "youtu.be" in url):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL provided")
            
        # Download audio and get video info
        audio_file, video_info = download_audio_and_get_info(url)
        
        # Transcribe with AssemblyAI
        raw_transcript = transcribe_with_assemblyai(audio_file)
        
        # Enhance with Gemini (optional, falls back to raw transcript if fails)
        enhanced_transcript = enhance_transcript_with_gemini(raw_transcript, video_info)
        
        return {"text": enhanced_transcript}
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions as is
        raise http_ex
    except Exception as e:
        logger.error(f"Error in transcribe_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up files regardless of success or failure
        cleanup_files(audio_file)

# JSON-based endpoint
@app.post("/transcribe-json/")
async def transcribe_json_endpoint(request: VideoRequest):
    audio_file = None
    
    try:
        url = request.url
        logger.info(f"Received URL via JSON: {url}")
        
        # Validate the URL
        if not url or (not "youtube.com" in url and not "youtu.be" in url):
            logger.warning(f"Invalid URL provided: {url}")
            return {"error": "Invalid YouTube URL provided"}
        
        # Download audio and get video info
        audio_file, video_info = download_audio_and_get_info(url)
        
        # Transcribe with AssemblyAI (real transcription)
        raw_transcript = transcribe_with_assemblyai(audio_file)
        
        # Enhance with Gemini (optional formatting enhancement)
        enhanced_transcript = enhance_transcript_with_gemini(raw_transcript, video_info)
        
        return {"text": enhanced_transcript}
    except HTTPException as http_ex:
        # Handle HTTP exceptions by returning an error message
        logger.error(f"HTTP error in transcribe_json_endpoint: {http_ex.detail}")
        return {"error": http_ex.detail}
    except Exception as e:
        # Handle general exceptions
        logger.error(f"Error in transcribe_json_endpoint: {str(e)}")
        return {"error": str(e)}
    finally:
        # Clean up files regardless of success or failure
        cleanup_files(audio_file)