# app_langscale/services/detector_service.py 
 
import httpx
import subprocess
import speech_recognition as sr
from pathlib import Path
from datetime import datetime
from utils.constants import SUPPORTED_LANGUAGES
import logging
import json
import tempfile
from typing import Dict
from fastapi import HTTPException

logger = logging.getLogger("LanguageDetectionAPI")

class VideoLanguageDetector:
    """
    Professional video language detection service with download capabilities
    """
    
    def __init__(self, base_dir: str = "language_detection_storage"):
        """
        Initialize the video language detector
        
        Args:
            base_dir: Base directory for storing temporary files
        """
        self.base_dir = Path(base_dir)
        self.videos_dir = self.base_dir / "videos"
        self.audio_dir = self.base_dir / "audio"
        
        # Create temporary directories (files will be cleaned automatically)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Job storage
        self.jobs: Dict[str, Dict] = {}
        
        # Speech recognizer
        self.recognizer = sr.Recognizer()
    
    async def download_video(self, video_url: str, job_id: str) -> Path:
        """
        Download video from URL to temporary file
        
        Args:
            video_url: URL of the video to download
            job_id: Unique job identifier
            
        Returns:
            Path: Path to the downloaded temporary video file
            
        Raises:
            HTTPException: If download fails
        """
        temp_file = None
        try:
            logger.info(f"Downloading video from {video_url}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', dir=self.videos_dir)
            download_path = Path(temp_file.name)
            
            # Download with streaming
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream('GET', video_url) as response:
                    response.raise_for_status()
                    
                    total_size = 0
                    for chunk in response.iter_bytes(chunk_size=8192):
                        temp_file.write(chunk)
                        total_size += len(chunk)
            
            temp_file.close()
            
            file_size_mb = total_size / (1024 * 1024)
            logger.info(f"Video downloaded to temporary file: {download_path} ({file_size_mb:.2f} MB)")
            return download_path
            
        except httpx.HTTPError as e:
            logger.error(f"Download failed: {str(e)}")
            if temp_file:
                temp_file.close()
                if Path(temp_file.name).exists():
                    Path(temp_file.name).unlink()
            raise HTTPException(status_code=400, detail=f"Failed to download video: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            if temp_file:
                temp_file.close()
                if Path(temp_file.name).exists():
                    Path(temp_file.name).unlink()
            raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")
    
    def extract_audio(self, video_path: Path, audio_path: Path) -> bool:
        """
        Extract audio from video using FFmpeg
        
        Args:
            video_path: Path to the input video file
            audio_path: Path where the audio file will be saved
            
        Returns:
            bool: True if extraction successful, False otherwise
        """
        try:
            logger.info(f"Extracting audio from {video_path.name}")
            
            command = [
                'ffmpeg', '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # Sample rate 16kHz
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                str(audio_path)
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Audio extracted successfully: {audio_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Audio extraction timeout")
            return False
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return False
    
    def detect_language_from_audio(
        self,
        audio_path: Path,
        duration: int = 30,
        test_all: bool = True
    ) -> Dict:
        """
        Detect language from audio file
        
        Args:
            audio_path: Path to the audio file
            duration: Duration in seconds to analyze
            test_all: If True, test all supported languages
            
        Returns:
            Dict: Detection results including language, confidence, and transcript
        """
        results = {
            "detected": False,
            "language": None,
            "language_code": None,
            "language_name": None,
            "confidence": 0.0,
            "transcript": None,
            "all_tests": []
        }
        
        try:
            with sr.AudioFile(str(audio_path)) as source:
                # Record audio for specified duration
                logger.info(f"Analyzing {duration} seconds of audio")
                audio_data = self.recognizer.record(source, duration=duration)
                
                if test_all:
                    # Test each supported language (stop when one is detected)
                    for language_code, language_display, language_name in SUPPORTED_LANGUAGES:
                        test_result = self._test_language(
                            audio_data,
                            language_code,
                            language_display,
                            language_name
                        )
                        results["all_tests"].append(test_result)
                        
                        # If we found a match, stop testing other languages
                        if test_result["recognized"]:
                            results.update({
                                "detected": True,
                                "language": language_display,
                                "language_code": language_code,
                                "language_name": language_name,
                                "transcript": test_result["transcript"],
                                "confidence": test_result["confidence"]
                            })
                            logger.info(f"✅ Language detected: {language_display} - Stopping further tests")
                            break  # Stop testing other languages
                else:
                    # Try automatic detection
                    try:
                        transcript = self.recognizer.recognize_google(audio_data)
                        if transcript and len(transcript.strip()) > 5:
                            results.update({
                                "detected": True,
                                "language": "🌍 Auto-detected",
                                "transcript": transcript,
                                "confidence": 0.8
                            })
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        logger.error(f"API Error: {e}")
                
        except Exception as e:
            logger.error(f"Error during language detection: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _test_language(
        self,
        audio_data,
        language_code: str,
        language_display: str,
        language_name: str
    ) -> Dict:
        """
        Test recognition with a specific language
        
        Args:
            audio_data: Audio data from speech_recognition
            language_code: Language code (e.g., 'fr-FR')
            language_display: Display name with flag
            language_name: English name of the language
            
        Returns:
            Dict: Test result with recognition status and transcript
        """
        test_result = {
            "language_code": language_code,
            "language_display": language_display,
            "language_name": language_name,
            "recognized": False,
            "transcript": None,
            "confidence": 0.0,
            "error": None
        }
        
        try:
            transcript = self.recognizer.recognize_google(
                audio_data,
                language=language_code
            )
            
            # Check if we got meaningful text
            if transcript and len(transcript.strip()) > 5:
                test_result.update({
                    "recognized": True,
                    "transcript": transcript,
                    "confidence": min(len(transcript) / 50.0, 1.0)  # Simple confidence metric
                })
                logger.info(f"Recognition successful for {language_display}")
            
        except sr.UnknownValueError:
            # This language didn't work, continue
            test_result["error"] = "Speech not recognized"
        except sr.RequestError as e:
            test_result["error"] = f"API error: {str(e)}"
            logger.warning(f"⚠️ API error for {language_display}: {e}")
        except Exception as e:
            test_result["error"] = str(e)
        
        return test_result
    
    def cleanup_temp_files(self, video_path: Path = None, audio_path: Path = None) -> None:
        """
        Clean up temporary files
        
        Args:
            video_path: Path to temporary video file
            audio_path: Path to temporary audio file
        """
        if video_path and video_path.exists():
            try:
                video_path.unlink()
                logger.info(f"Temporary video file cleaned: {video_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup video file {video_path}: {str(e)}")
        
        if audio_path and audio_path.exists():
            try:
                audio_path.unlink()
                logger.info(f"Temporary audio file cleaned: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup audio file {audio_path}: {str(e)}")