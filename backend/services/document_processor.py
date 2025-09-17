import fitz  # PyMuPDF
import vosk
import json
import wave
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.vosk_model = None
        self._load_vosk_model()
    
    def _load_vosk_model(self):
        """Load Vosk model for speech recognition"""
        try:
            model_path = "models/vosk-model-en-us-0.22"  # You'll need to download this
            if os.path.exists(model_path):
                self.vosk_model = vosk.Model(model_path)
                logger.info("Vosk model loaded successfully")
            else:
                logger.warning(f"Vosk model not found at {model_path}. Audio transcription will not work.")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
    
    async def process_file(self, file_path: str, content_type: str) -> str:
        """Process different file types and extract text content"""
        try:
            if content_type == "application/pdf":
                return await self._process_pdf(file_path)
            elif content_type.startswith("audio/"):
                return await self._process_audio(file_path)
            elif content_type.startswith("video/"):
                return await self._process_video(file_path)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    async def _process_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text_content = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(f"Page {page_num + 1}:\n{text}")
            
            doc.close()
            
            if not text_content:
                return "No text content found in PDF"
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
    
    async def _process_audio(self, file_path: str) -> str:
        """Transcribe audio using Vosk"""
        if not self.vosk_model:
            filename = os.path.basename(file_path)
            return f"""Audio file: {filename}

Note: Audio transcription is not available because the Vosk speech recognition model is not installed.
To enable audio transcription, please download the Vosk model using the setup script or manually.

For now, you can upload PDF files for text-based document processing."""
        
        try:
            # Convert audio to WAV format if needed
            wav_path = await self._convert_to_wav(file_path)
            
            # Transcribe using Vosk
            with wave.open(wav_path, 'rb') as wf:
                if wf.getnchannels() != 1:
                    raise Exception("Audio must be mono channel")
                if wf.getsampwidth() != 2:
                    raise Exception("Audio must be 16-bit")
                if wf.getframerate() not in [8000, 16000, 32000, 44100, 48000]:
                    raise Exception("Audio sample rate must be 8000, 16000, 32000, 44100, or 48000 Hz")
                
                rec = vosk.KaldiRecognizer(self.vosk_model, wf.getframerate())
                
                transcription = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if 'text' in result and result['text']:
                            transcription.append(result['text'])
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                if 'text' in final_result and final_result['text']:
                    transcription.append(final_result['text'])
            
            # Clean up temporary WAV file if it was created
            if wav_path != file_path:
                os.unlink(wav_path)
            
            return " ".join(transcription) if transcription else "No speech detected in audio"
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    async def _process_video(self, file_path: str) -> str:
        """Extract audio from video and transcribe"""
        try:
            # Check if Vosk model is available
            if not self.vosk_model:
                logger.warning("Vosk model not available. Extracting basic video metadata instead.")
                return await self._extract_video_metadata(file_path)
            
            logger.info(f"Starting video processing for: {file_path}")
            
            # Use MoviePy to extract audio (simpler approach)
            import tempfile
            from moviepy.editor import VideoFileClip
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            try:
                # Extract audio using MoviePy
                logger.info("Extracting audio using MoviePy...")
                video = VideoFileClip(file_path)
                
                if video.audio is None:
                    video.close()
                    logger.warning("No audio track found in video")
                    return await self._extract_video_metadata(file_path)
                
                # Write audio as WAV with specific settings for Vosk
                audio = video.audio
                audio.write_audiofile(
                    temp_audio_path,
                    fps=16000,  # 16kHz sample rate
                    nbytes=2,   # 16-bit
                    codec='pcm_s16le',  # PCM format
                    verbose=False,
                    logger=None
                )
                
                video.close()
                audio.close()
                
                logger.info(f"Audio extracted successfully to: {temp_audio_path}")
                
                # Transcribe the audio
                transcription = await self._transcribe_audio_file(temp_audio_path)
                
                # Clean up
                os.unlink(temp_audio_path)
                
                if transcription and len(transcription.strip()) > 10:
                    logger.info(f"Transcription successful: {len(transcription)} characters")
                    return transcription
                else:
                    logger.warning("Transcription was empty or too short")
                    return await self._extract_video_metadata(file_path)
                    
            except Exception as audio_error:
                logger.error(f"Audio extraction failed: {audio_error}")
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                return await self._extract_video_metadata(file_path)
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return await self._extract_video_metadata(file_path)
    
    async def _extract_video_metadata(self, file_path: str) -> str:
        """Extract basic metadata from video when transcription is not available"""
        try:
            video = VideoFileClip(file_path)
            duration = video.duration
            fps = video.fps
            size = video.size
            video.close()
            
            filename = os.path.basename(file_path)
            metadata_text = f"""Video file: {filename}
Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)
Resolution: {size[0]}x{size[1]}
Frame rate: {fps:.1f} fps

Note: Audio transcription is not available because the Vosk speech recognition model is not installed.
To enable audio transcription, please download the Vosk model or use PDF files for text-based content."""
            
            return metadata_text
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            return f"Video file uploaded but could not be processed. Filename: {os.path.basename(file_path)}"
    
    async def _transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe audio file directly using Vosk"""
        if not self.vosk_model:
            return "Vosk model not available"
        
        try:
            import wave
            import json
            
            logger.info(f"Starting transcription of: {audio_path}")
            
            # Open the WAV file
            with wave.open(audio_path, 'rb') as wf:
                # Check audio format
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth() 
                framerate = wf.getframerate()
                
                logger.info(f"Audio format: {channels} channels, {sample_width*8}-bit, {framerate}Hz")
                
                # Create recognizer with the correct sample rate
                rec = vosk.KaldiRecognizer(self.vosk_model, framerate)
                
                # If stereo, we need to handle it differently
                if channels == 2:
                    logger.warning("Audio is stereo, converting to mono for Vosk")
                    # Read all frames and convert to mono
                    frames = wf.readframes(wf.getnframes())
                    import numpy as np
                    
                    # Convert bytes to numpy array
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    # Reshape to stereo and take mean to convert to mono
                    audio_data = audio_data.reshape(-1, 2).mean(axis=1).astype(np.int16)
                    
                    # Process in chunks
                    chunk_size = 4000
                    transcription = []
                    
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i+chunk_size].tobytes()
                        if rec.AcceptWaveform(chunk):
                            result = json.loads(rec.Result())
                            if 'text' in result and result['text']:
                                transcription.append(result['text'])
                    
                    # Get final result
                    final_result = json.loads(rec.FinalResult())
                    if 'text' in final_result and final_result['text']:
                        transcription.append(final_result['text'])
                
                else:
                    # Mono audio - process normally
                    transcription = []
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            if 'text' in result and result['text']:
                                transcription.append(result['text'])
                    
                    # Get final result
                    final_result = json.loads(rec.FinalResult())
                    if 'text' in final_result and final_result['text']:
                        transcription.append(final_result['text'])
            
            result_text = " ".join(transcription) if transcription else "No speech detected"
            logger.info(f"Transcription complete: {len(result_text)} characters")
            return result_text
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return f"Transcription failed: {str(e)}"
    
    async def _extract_audio_with_ffmpeg(self, file_path: str) -> str:
        """Extract audio using FFmpeg"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        # Use ffmpeg to extract audio in the correct format for Vosk
        cmd = [
            'ffmpeg', '-i', file_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ac', '1',  # Mono channel
            '-ar', '16000',  # 16kHz sample rate
            temp_audio_path,
            '-y'  # Overwrite output files
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return temp_audio_path
    
    async def _extract_audio_with_moviepy(self, file_path: str) -> str:
        """Extract audio using MoviePy and convert to Vosk format"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        # Extract audio using MoviePy
        video = VideoFileClip(file_path)
        audio = video.audio
        
        if audio is None:
            video.close()
            raise Exception("No audio track found in video")
        
        # Write audio file
        audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
        video.close()
        audio.close()
        
        # Now convert the audio to the proper format using a simple conversion
        return await self._convert_moviepy_audio_to_vosk_format(temp_audio_path)
    
    async def _convert_moviepy_audio_to_vosk_format(self, input_path: str) -> str:
        """Convert MoviePy audio output to Vosk-compatible format"""
        import wave
        import numpy as np
        from scipy import signal
        import soundfile as sf
        
        try:
            # Read the audio file
            data, samplerate = sf.read(input_path)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Resample to 16kHz if needed
            if samplerate != 16000:
                num_samples = int(len(data) * 16000 / samplerate)
                data = signal.resample(data, num_samples)
                samplerate = 16000
            
            # Convert to 16-bit integers
            data = (data * 32767).astype(np.int16)
            
            # Create new output file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_output:
                output_path = temp_output.name
            
            # Write as WAV file with correct format
            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(data.tobytes())
            
            # Clean up original file
            os.unlink(input_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            # If conversion fails, return original file and hope for the best
            return input_path
    
    async def _convert_to_wav(self, file_path: str) -> str:
        """Convert audio file to WAV format using scipy and soundfile"""
        try:
            # Check if it's already a WAV file
            if file_path.lower().endswith('.wav'):
                logger.info(f"File is already WAV format: {file_path}")
                # Still need to check if it's mono and correct format
                return await self._ensure_vosk_format(file_path)
            
            import tempfile
            import soundfile as sf
            import numpy as np
            from scipy import signal
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            logger.info(f"Converting audio file {file_path} to WAV format using soundfile...")
            
            try:
                # Read the audio file using soundfile (supports MP3, FLAC, etc.)
                data, samplerate = sf.read(file_path)
                logger.info(f"Original audio: {data.shape}, {samplerate}Hz")
                
                # Convert to mono if stereo
                if len(data.shape) > 1 and data.shape[1] > 1:
                    logger.info("Converting stereo to mono")
                    data = np.mean(data, axis=1)
                
                # Resample to 16kHz if needed
                if samplerate != 16000:
                    logger.info(f"Resampling from {samplerate}Hz to 16kHz")
                    num_samples = int(len(data) * 16000 / samplerate)
                    data = signal.resample(data, num_samples)
                    samplerate = 16000
                
                # Ensure data is in the correct range and type
                if data.dtype != np.float32:
                    data = data.astype(np.float32)
                
                # Normalize to prevent clipping
                max_val = np.max(np.abs(data))
                if max_val > 1.0:
                    data = data / max_val
                
                # Write as WAV file (soundfile automatically handles the format)
                sf.write(temp_wav_path, data, samplerate, subtype='PCM_16')
                
                logger.info(f"Successfully converted audio to Vosk-compatible format: {temp_wav_path}")
                return temp_wav_path
                
            except Exception as sf_error:
                logger.warning(f"Soundfile conversion failed: {sf_error}")
                # Fallback to MoviePy if soundfile fails
                return await self._convert_with_moviepy(file_path)
                
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise Exception(f"Audio conversion failed: {str(e)}")
    
    async def _ensure_vosk_format(self, wav_path: str) -> str:
        """Ensure WAV file is in correct format for Vosk (mono, 16kHz, 16-bit)"""
        try:
            import soundfile as sf
            import numpy as np
            from scipy import signal
            import tempfile
            
            # Read the existing WAV file
            data, samplerate = sf.read(wav_path)
            logger.info(f"Checking WAV format: {data.shape}, {samplerate}Hz")
            
            needs_conversion = False
            
            # Check if mono
            if len(data.shape) > 1 and data.shape[1] > 1:
                logger.info("Converting stereo WAV to mono")
                data = np.mean(data, axis=1)
                needs_conversion = True
            
            # Check sample rate
            if samplerate != 16000:
                logger.info(f"Resampling WAV from {samplerate}Hz to 16kHz")
                num_samples = int(len(data) * 16000 / samplerate)
                data = signal.resample(data, num_samples)
                samplerate = 16000
                needs_conversion = True
            
            if needs_conversion:
                # Create new file with correct format
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    new_path = temp_wav.name
                
                # Ensure correct data type and range
                if data.dtype != np.float32:
                    data = data.astype(np.float32)
                
                # Normalize if needed
                max_val = np.max(np.abs(data))
                if max_val > 1.0:
                    data = data / max_val
                
                sf.write(new_path, data, samplerate, subtype='PCM_16')
                logger.info(f"Created Vosk-compatible WAV: {new_path}")
                return new_path
            else:
                logger.info("WAV file is already in correct format")
                return wav_path
                
        except Exception as e:
            logger.error(f"Error ensuring Vosk format: {e}")
            return wav_path
    
    async def _convert_with_moviepy(self, file_path: str) -> str:
        """Fallback conversion using MoviePy"""
        try:
            from moviepy.editor import AudioFileClip
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            logger.info(f"Fallback: Converting with MoviePy...")
            
            # Load audio file using MoviePy
            audio = AudioFileClip(file_path)
            
            # Write as WAV with Vosk-compatible settings (mono, 16kHz, 16-bit)
            audio.write_audiofile(
                temp_wav_path,
                fps=16000,  # 16kHz sample rate
                nbytes=2,   # 16-bit
                codec='pcm_s16le',  # PCM format
                ffmpeg_params=['-ac', '1'],  # Force mono output
                verbose=False,
                logger=None
            )
            
            audio.close()
            logger.info(f"MoviePy conversion successful: {temp_wav_path}")
            return temp_wav_path
            
        except Exception as e:
            logger.error(f"MoviePy conversion failed: {e}")
            raise Exception(f"All audio conversion methods failed: {str(e)}")
