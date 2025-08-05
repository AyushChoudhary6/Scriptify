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
    browser: str = "chrome"  # Default browser for cookies

# Enhanced request model for advanced summarization
class EnhancedVideoRequest(BaseModel):
    url: str
    browser: str = "chrome"
    summary_type: str = "comprehensive"  # comprehensive, brief, bullets, academic
    include_timestamps: bool = True
    include_chapters: bool = True
    include_highlights: bool = True

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
    """Transcribe audio file using AssemblyAI API with advanced features"""
    try:
        logger.info(f"Starting advanced transcription with AssemblyAI for {audio_path}")
        
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise HTTPException(status_code=500, detail="Audio file not found")
        
        # Configure AssemblyAI with advanced features
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            punctuate=True,
            format_text=True,
            auto_chapters=True,  # Enable chapter detection
            speaker_labels=True,  # Enable speaker identification
            auto_highlights=True,  # Enable key highlights
            entity_detection=True,  # Enable entity detection
            sentiment_analysis=True,  # Enable sentiment analysis
            summarization=True,  # Enable AI summarization
            summary_model=aai.SummarizationModel.informative,  # Use informative summary
            summary_type=aai.SummarizationType.bullets,  # Bullet point format
        )
        
        # Create transcriber and transcribe the audio file
        transcriber = aai.Transcriber(config=config)
        logger.info("Uploading and transcribing audio file with advanced features...")
        
        transcript = transcriber.transcribe(audio_path)
        
        # Check if transcription was successful
        if transcript.status == "error":
            logger.error(f"AssemblyAI transcription failed: {transcript.error}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        logger.info(f"Advanced transcription complete with {len(transcript.text)} characters")
        
        # Return structured data instead of just text
        return {
            "text": transcript.text,
            "summary": getattr(transcript, 'summary', None),
            "chapters": getattr(transcript, 'chapters', []),
            "auto_highlights": getattr(transcript, 'auto_highlights_result', None),
            "entities": getattr(transcript, 'entities', []),
            "sentiment_analysis": getattr(transcript, 'sentiment_analysis_results', []),
            "words": getattr(transcript, 'words', []),  # For detailed timestamps
        }
        
    except Exception as e:
        logger.error(f"Error in transcribe_with_assemblyai: {str(e)}")
        if "API key" in str(e).lower():
            raise HTTPException(
                status_code=500, 
                detail="Invalid AssemblyAI API key. Please update your API key in the configuration."
            )
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")

def enhance_transcript_with_gemini(transcript_data, video_info):
    """Create an intelligent video summary with timestamps and structured content"""
    try:
        logger.info("Creating intelligent video summary with Gemini")
        
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
        
        # Extract data from transcript
        raw_text = transcript_data.get('text', '') if isinstance(transcript_data, dict) else str(transcript_data)
        summary = transcript_data.get('summary', '') if isinstance(transcript_data, dict) else ''
        chapters = transcript_data.get('chapters', []) if isinstance(transcript_data, dict) else []
        highlights = transcript_data.get('auto_highlights', None) if isinstance(transcript_data, dict) else None
        
        # Build chapters section
        chapters_text = ""
        if chapters:
            chapters_text = "\n📑 CHAPTER BREAKDOWN:\n"
            for i, chapter in enumerate(chapters, 1):
                start_time = format_timestamp(chapter.get('start', 0))
                end_time = format_timestamp(chapter.get('end', 0))
                summary_text = chapter.get('summary', 'No summary available')
                chapters_text += f"\n{i}. [{start_time} - {end_time}] {summary_text}"
        
        # Build highlights section
        highlights_text = ""
        if highlights and hasattr(highlights, 'results'):
            highlights_text = "\n🔍 KEY HIGHLIGHTS:\n"
            for highlight in highlights.results[:5]:  # Top 5 highlights
                highlights_text += f"\n• {highlight.text} (Confidence: {highlight.rank:.1f})"
        
        # Create a comprehensive prompt for video summary
        prompt = f"""
Create a comprehensive, well-structured video summary from this YouTube video content. Focus on creating a professional summary that's easy to read and provides value to the viewer.

VIDEO METADATA:
🎬 Title: {video_info['title']}
👤 Creator: {video_info['uploader']}
⏱️ Duration: {duration_mins} minutes and {duration_secs} seconds
📅 Upload Date: {upload_date}
👁️ Views: {video_info.get('view_count', 'N/A')}
🏷️ Categories: {categories}
🔖 Tags: {tags}

RAW TRANSCRIPT:
{raw_text[:3000]}...  # Truncate for API limits

AI SUMMARY:
{summary}

{chapters_text}

{highlights_text}

Please create a professional video summary with the following structure:

1. **EXECUTIVE SUMMARY** (2-3 sentences about the main topic)

2. **KEY TAKEAWAYS** (3-5 bullet points of main insights)

3. **DETAILED BREAKDOWN WITH TIMESTAMPS** (organized by topics/sections with time markers)

4. **ACTION ITEMS/RECOMMENDATIONS** (if applicable)

5. **ADDITIONAL INSIGHTS** (interesting facts, quotes, or notable mentions)

Format the output in clean Markdown with proper headings, timestamps in [MM:SS] format, and bullet points. Make it engaging and informative for someone who wants to quickly understand the video content.

Focus on:
- Clear, concise language
- Logical flow and organization
- Specific timestamps for key moments
- Actionable insights where relevant
- Professional presentation
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
            # Return structured fallback if enhancement fails
            return create_fallback_summary(transcript_data, video_info)
        
        logger.info("Intelligent video summary creation complete")
        return enhanced_text
        
    except Exception as e:
        logger.warning(f"Error creating video summary: {str(e)}")
        # Return structured fallback if enhancement fails
        return create_fallback_summary(transcript_data, video_info)

def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    if not isinstance(seconds, (int, float)):
        return "00:00"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def create_fallback_summary(transcript_data, video_info):
    """Create a basic structured summary if AI enhancement fails"""
    
    # Format duration
    duration_mins = video_info['duration'] // 60
    duration_secs = video_info['duration'] % 60
    
    # Extract text
    raw_text = transcript_data.get('text', '') if isinstance(transcript_data, dict) else str(transcript_data)
    summary = transcript_data.get('summary', '') if isinstance(transcript_data, dict) else ''
    chapters = transcript_data.get('chapters', []) if isinstance(transcript_data, dict) else []
    
    # Create basic structured output
    fallback_summary = f"""
# 📋 VIDEO SUMMARY

## 📹 Video Information
- **Title:** {video_info['title']}
- **Creator:** {video_info['uploader']}
- **Duration:** {duration_mins}:{duration_secs:02d}
- **Views:** {video_info.get('view_count', 'N/A')}

## 📝 AI Summary
{summary if summary else 'Summary not available'}

## 📑 Content Breakdown
"""
    
    if chapters:
        for i, chapter in enumerate(chapters, 1):
            start_time = format_timestamp(chapter.get('start', 0))
            end_time = format_timestamp(chapter.get('end', 0))
            chapter_summary = chapter.get('summary', 'Content segment')
            fallback_summary += f"\n### {i}. [{start_time} - {end_time}] {chapter_summary}\n"
    else:
        # If no chapters, create basic sections from transcript
        words_per_minute = 150
        segment_length = 300  # 5 minutes
        segments = len(raw_text) // (words_per_minute * segment_length // 60) or 1
        
        for i in range(min(segments, 5)):  # Max 5 segments
            start_min = i * 5
            end_min = min((i + 1) * 5, duration_mins)
            fallback_summary += f"\n### [{start_min:02d}:00 - {end_min:02d}:00] Content Segment {i+1}\n"
    
    fallback_summary += f"\n## 📄 Full Transcript\n{raw_text}"
    
    return fallback_summary

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
        
        # Transcribe with AssemblyAI (advanced transcription with features)
        transcript_data = transcribe_with_assemblyai(audio_file)
        
        # Create intelligent summary with Gemini
        enhanced_summary = enhance_transcript_with_gemini(transcript_data, video_info)
        
        # Return comprehensive response
        return {
            "text": enhanced_summary,
            "video_info": {
                "title": video_info['title'],
                "uploader": video_info['uploader'],
                "duration": f"{video_info['duration'] // 60}:{video_info['duration'] % 60:02d}",
                "view_count": video_info.get('view_count', 'N/A'),
                "upload_date": video_info['upload_date']
            },
            "processing_info": {
                "has_chapters": bool(transcript_data.get('chapters', []) if isinstance(transcript_data, dict) else False),
                "has_summary": bool(transcript_data.get('summary', '') if isinstance(transcript_data, dict) else False),
                "has_highlights": bool(transcript_data.get('auto_highlights', None) if isinstance(transcript_data, dict) else False),
                "word_count": len(transcript_data.get('text', '').split() if isinstance(transcript_data, dict) else str(transcript_data).split())
            }
        }
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

# Enhanced endpoint for intelligent video summarization
@app.post("/transcribe-summary/")
async def transcribe_summary_endpoint(request: EnhancedVideoRequest):
    """Advanced endpoint for intelligent video summarization with customizable options"""
    audio_file = None
    
    try:
        url = request.url
        logger.info(f"Received enhanced summarization request for URL: {url}")
        logger.info(f"Summary type: {request.summary_type}, Include timestamps: {request.include_timestamps}")
        
        # Validate the URL
        if not url or (not "youtube.com" in url and not "youtu.be" in url):
            logger.warning(f"Invalid URL provided: {url}")
            return {"error": "Invalid YouTube URL provided"}
        
        # Download audio and get video info
        audio_file, video_info = download_audio_and_get_info(url)
        
        # Transcribe with AssemblyAI (advanced transcription with features)
        transcript_data = transcribe_with_assemblyai(audio_file)
        
        # Create customized summary based on request parameters
        enhanced_summary = create_customized_summary(
            transcript_data, 
            video_info, 
            request.summary_type,
            request.include_timestamps,
            request.include_chapters,
            request.include_highlights
        )
        
        # Return comprehensive response
        return {
            "text": enhanced_summary,
            "video_info": {
                "title": video_info['title'],
                "uploader": video_info['uploader'],
                "duration": f"{video_info['duration'] // 60}:{video_info['duration'] % 60:02d}",
                "duration_seconds": video_info['duration'],
                "view_count": video_info.get('view_count', 'N/A'),
                "upload_date": video_info['upload_date'],
                "description": video_info.get('description', '')[:500] + "..." if video_info.get('description', '') else 'N/A'
            },
            "processing_info": {
                "summary_type": request.summary_type,
                "has_chapters": bool(transcript_data.get('chapters', []) if isinstance(transcript_data, dict) else False),
                "has_summary": bool(transcript_data.get('summary', '') if isinstance(transcript_data, dict) else False),
                "has_highlights": bool(transcript_data.get('auto_highlights', None) if isinstance(transcript_data, dict) else False),
                "word_count": len(transcript_data.get('text', '').split() if isinstance(transcript_data, dict) else str(transcript_data).split()),
                "chapter_count": len(transcript_data.get('chapters', []) if isinstance(transcript_data, dict) else [])
            },
            "features_used": {
                "timestamps": request.include_timestamps,
                "chapters": request.include_chapters,
                "highlights": request.include_highlights,
                "ai_summary": True
            }
        }
    except HTTPException as http_ex:
        logger.error(f"HTTP error in transcribe_summary_endpoint: {http_ex.detail}")
        return {"error": http_ex.detail}
    except Exception as e:
        logger.error(f"Error in transcribe_summary_endpoint: {str(e)}")
        return {"error": str(e)}
    finally:
        # Clean up files regardless of success or failure
        cleanup_files(audio_file)

def create_customized_summary(transcript_data, video_info, summary_type, include_timestamps, include_chapters, include_highlights):
    """Create a customized summary based on user preferences"""
    try:
        logger.info(f"Creating {summary_type} summary with custom options")
        
        # Create a Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Format duration and metadata
        duration_mins = video_info['duration'] // 60
        duration_secs = video_info['duration'] % 60
        
        upload_date = video_info['upload_date']
        if len(upload_date) == 8:  # YYYYMMDD format
            upload_date = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        
        # Extract data from transcript
        raw_text = transcript_data.get('text', '') if isinstance(transcript_data, dict) else str(transcript_data)
        ai_summary = transcript_data.get('summary', '') if isinstance(transcript_data, dict) else ''
        chapters = transcript_data.get('chapters', []) if isinstance(transcript_data, dict) else []
        highlights = transcript_data.get('auto_highlights', None) if isinstance(transcript_data, dict) else None
        
        # Build prompt based on summary type
        if summary_type == "brief":
            prompt_style = "Create a brief, concise summary in 2-3 paragraphs. Focus on the main points only."
        elif summary_type == "bullets":
            prompt_style = "Create a bullet-point summary with clear, actionable takeaways. Use bullet points and short sentences."
        elif summary_type == "academic":
            prompt_style = "Create an academic-style summary with formal language, structured analysis, and scholarly presentation."
        else:  # comprehensive
            prompt_style = "Create a comprehensive, detailed summary with full analysis and insights."
        
        # Build optional sections
        timestamp_instruction = "Include specific timestamps in [MM:SS] format throughout the content." if include_timestamps else "Do not include specific timestamps."
        chapter_instruction = "Include chapter breakdowns with time ranges." if include_chapters and chapters else "Focus on content flow without chapter divisions."
        highlight_instruction = "Highlight the most important insights and quotes." if include_highlights else "Present information in a balanced manner."
        
        # Create comprehensive prompt
        prompt = f"""
{prompt_style}

VIDEO INFORMATION:
🎬 Title: {video_info['title']}
👤 Creator: {video_info['uploader']}
⏱️ Duration: {duration_mins}:{duration_secs:02d}
📅 Upload Date: {upload_date}
👁️ Views: {video_info.get('view_count', 'N/A')}

AI SUMMARY: {ai_summary}

CONTENT: {raw_text[:4000]}...

INSTRUCTIONS:
- {prompt_style}
- {timestamp_instruction}
- {chapter_instruction}
- {highlight_instruction}
- Use clear markdown formatting
- Make it engaging and valuable for the reader
- Maintain accuracy to the original content

Please create the summary now:
"""
        
        # Generate customized content
        response = model.generate_content(prompt)
        
        # Extract and return the customized text
        try:
            if hasattr(response, 'text'):
                return response.text
            else:
                return str(response)
        except Exception as e:
            logger.warning(f"Error creating customized summary: {str(e)}")
            return create_fallback_summary(transcript_data, video_info)
            
    except Exception as e:
        logger.warning(f"Error in create_customized_summary: {str(e)}")
        return create_fallback_summary(transcript_data, video_info)