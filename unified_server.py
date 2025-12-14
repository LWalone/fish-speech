import io
import os
import sys
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional

import gradio as gr
import pyrootutils
import soundfile as sf
import torch
import uvicorn
import whisper
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

from fish_speech.inference_engine import TTSInferenceEngine
from fish_speech.models.dac.inference import load_model as load_decoder_model
from fish_speech.models.text2semantic.inference import launch_thread_safe_queue
from fish_speech.utils.schema import ServeTTSRequest
from gpu_manager import gpu_manager
from tools.webui import build_app

os.environ["EINX_FILTER_TRACEBACK"] = "false"

# Configuration
PORT = int(os.getenv("PORT", "7862"))
DEVICE = os.getenv("BACKEND", "cuda")
COMPILE = os.getenv("COMPILE", "0") == "1"
HALF = os.getenv("HALF", "0") == "1"
LLAMA_PATH = Path(os.getenv("LLAMA_CHECKPOINT_PATH", "checkpoints/openaudio-s1-mini"))
DECODER_PATH = Path(os.getenv("DECODER_CHECKPOINT_PATH", "checkpoints/openaudio-s1-mini/codec.pth"))
DECODER_CONFIG = os.getenv("DECODER_CONFIG_NAME", "modded_dac_vq")
SPEAKERS_DIR = Path("speakers")

# Global inference engine
inference_engine = None
whisper_model = None
speakers_db: Dict[str, Dict] = {}

# Create speakers directory
SPEAKERS_DIR.mkdir(exist_ok=True)


def load_speakers_db():
    """Load speakers database from disk"""
    global speakers_db
    db_file = SPEAKERS_DIR / "speakers.json"
    if db_file.exists():
        with open(db_file, 'r', encoding='utf-8') as f:
            speakers_db = json.load(f)
    logger.info(f"Loaded {len(speakers_db)} speakers from database")


def save_speakers_db():
    """Save speakers database to disk"""
    db_file = SPEAKERS_DIR / "speakers.json"
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(speakers_db, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(speakers_db)} speakers to database")


def load_whisper_model():
    """Load Whisper Turbo model"""
    global whisper_model
    if whisper_model is None:
        logger.info("Loading Whisper Turbo model...")
        whisper_model = whisper.load_model("turbo", device=DEVICE)
        logger.info("Whisper Turbo model loaded")
    return whisper_model


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using Whisper Turbo"""
    try:
        model = load_whisper_model()
        result = model.transcribe(audio_path, language=None)
        return result["text"].strip()
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return ""


def load_models():
    """Load TTS models with proper error handling"""
    global inference_engine
    
    if inference_engine is not None:
        return inference_engine
    
    try:
        precision = torch.half if HALF else torch.bfloat16
        
        logger.info(f"Loading models from {LLAMA_PATH}")
        logger.info(f"Device: {DEVICE}, Compile: {COMPILE}, Half: {HALF}")
        
        llama_queue = launch_thread_safe_queue(
            checkpoint_path=LLAMA_PATH,
            device=DEVICE,
            precision=precision,
            compile=COMPILE,
        )
        
        decoder_model = load_decoder_model(
            config_name=DECODER_CONFIG,
            checkpoint_path=DECODER_PATH,
            device=DEVICE,
        )
        
        inference_engine = TTSInferenceEngine(
            llama_queue=llama_queue,
            decoder_model=decoder_model,
            compile=COMPILE,
            precision=precision,
        )
        
        # Warmup
        logger.info("Warming up model...")
        list(inference_engine.inference(ServeTTSRequest(
            text="Hello world.",
            references=[],
            reference_id=None,
            max_new_tokens=1024,
            chunk_length=200,
            top_p=0.7,
            repetition_penalty=1.5,
            temperature=0.7,
            format="wav",
        )))
        
        logger.info("Models loaded and ready")
        return inference_engine
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


# FastAPI app
app = FastAPI(
    title="Fish Speech Unified API",
    description="OpenAudio S1 Text-to-Speech API with UI, REST, and MCP support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize models on startup"""
    try:
        load_speakers_db()
        gpu_manager.get_model(load_models)
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")


@app.get("/health", tags=["Health"])
@app.get("/v1/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "fish-speech"}


@app.get("/api/gpu/status", tags=["GPU Management"])
async def gpu_status():
    """
    Get current GPU status and memory usage
    
    Returns GPU memory usage, model load status, and last activity time
    """
    return gpu_manager.get_status()


@app.post("/api/gpu/offload", tags=["GPU Management"])
async def gpu_offload():
    """
    Force offload model from GPU to free memory
    
    Useful for freeing GPU memory when not actively generating
    """
    gpu_manager.force_offload()
    return {"status": "offloaded", "message": "GPU memory freed"}


@app.post("/api/tts", tags=["Text-to-Speech"])
async def tts_api(
    text: str = Form(..., description="Text to convert to speech"),
    reference_audio: UploadFile = File(None, description="Reference audio file for voice cloning (5-10 seconds)"),
    reference_text: str = Form("", description="Transcript of reference audio"),
    max_new_tokens: int = Form(0, description="Maximum tokens per batch (0 = no limit)", ge=0, le=2048),
    chunk_length: int = Form(300, description="Iterative prompt length (0 = off)", ge=0, le=400),
    top_p: float = Form(0.8, description="Top-P sampling parameter", ge=0.7, le=0.95),
    repetition_penalty: float = Form(1.1, description="Repetition penalty", ge=1.0, le=1.2),
    temperature: float = Form(0.8, description="Sampling temperature", ge=0.7, le=1.0),
):
    """
    Generate speech from text using Fish Speech TTS
    
    Supports:
    - Basic text-to-speech
    - Voice cloning with reference audio
    - Emotion markers: (angry), (sad), (excited), etc.
    - Tone markers: (whispering), (shouting), etc.
    - Special effects: (laughing), (sighing), etc.
    
    Example with emotions:
    ```
    text = "(excited) This is amazing! (laughing) Ha,ha,ha!"
    ```
    """
    try:
        engine = gpu_manager.get_model(load_models)
        
        references = []
        audio_path = None
        if reference_audio:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", mode='wb') as tmp:
                content = await reference_audio.read()
                tmp.write(content)
                tmp.flush()
                audio_path = tmp.name
            
            # Auto-transcribe if no reference text provided
            if not reference_text or not reference_text.strip():
                logger.info("Auto-transcribing reference audio...")
                reference_text = transcribe_audio(audio_path)
                logger.info(f"Transcribed text: {reference_text}")
            
            # Read audio file as bytes for ServeTTSRequest
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            references.append({"audio": audio_bytes, "text": reference_text})
        
        request = ServeTTSRequest(
            text=text,
            references=references,
            reference_id=None,
            max_new_tokens=max_new_tokens,
            chunk_length=chunk_length,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            format="wav",
        )
        
        result = list(engine.inference(request))
        
        # Cleanup temp file
        if reference_audio and 'audio_path' in locals():
            try:
                os.unlink(audio_path)
            except:
                pass
        
        if result:
            inference_result = result[0]
            # Extract audio from InferenceResult: audio is (sample_rate, np.ndarray)
            if hasattr(inference_result, 'audio') and inference_result.audio:
                sample_rate, audio_array = inference_result.audio
                # Convert numpy array to WAV bytes
                buffer = io.BytesIO()
                import soundfile as sf
                sf.write(buffer, audio_array, sample_rate, format='WAV')
                buffer.seek(0)
                return StreamingResponse(
                    buffer,
                    media_type="audio/wav",
                    headers={"Content-Disposition": "attachment; filename=output.wav"}
                )
            else:
                raise HTTPException(status_code=500, detail="No audio generated")
        
        raise HTTPException(status_code=500, detail="Generation failed")
        
    except Exception as e:
        logger.error(f"TTS API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe", tags=["Transcription"])
async def transcribe_api(
    audio: UploadFile = File(..., description="Audio file to transcribe")
):
    """
    Transcribe audio file using Whisper Turbo
    
    Returns the transcribed text from the audio file.
    Supports multiple languages with automatic detection.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp.flush()
            audio_path = tmp.name
        
        text = transcribe_audio(audio_path)
        
        try:
            os.unlink(audio_path)
        except:
            pass
        
        return JSONResponse({"text": text})
        
    except Exception as e:
        logger.error(f"Transcription API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/speakers", tags=["Speaker Management"])
async def list_speakers():
    """
    List all registered speakers
    
    Returns a list of all speakers with their metadata.
    """
    return JSONResponse({
        "speakers": [
            {
                "id": speaker_id,
                "name": info["name"],
                "description": info.get("description", ""),
                "created_at": info.get("created_at", ""),
                "audio_file": info.get("audio_file", "")
            }
            for speaker_id, info in speakers_db.items()
        ],
        "total": len(speakers_db)
    })


@app.get("/api/speakers/{speaker_id}", tags=["Speaker Management"])
async def get_speaker(speaker_id: str):
    """
    Get speaker details by ID
    
    Returns detailed information about a specific speaker.
    """
    if speaker_id not in speakers_db:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    return JSONResponse(speakers_db[speaker_id])


@app.post("/api/speakers", tags=["Speaker Management"])
async def create_speaker(
    name: str = Form(..., description="Speaker name"),
    description: str = Form("", description="Speaker description"),
    audio: UploadFile = File(..., description="Reference audio file (5-10 seconds)"),
    reference_text: str = Form("", description="Reference text (leave empty for auto-transcription)")
):
    """
    Register a new speaker with reference audio
    
    Creates a new speaker profile with reference audio for voice cloning.
    If reference_text is not provided, it will be automatically transcribed.
    
    Returns the speaker ID and details.
    """
    try:
        import hashlib
        from datetime import datetime
        
        # Generate speaker ID
        speaker_id = hashlib.md5(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Save audio file
        audio_filename = f"{speaker_id}.wav"
        audio_path = SPEAKERS_DIR / audio_filename
        
        content = await audio.read()
        with open(audio_path, 'wb') as f:
            f.write(content)
        
        # Auto-transcribe if needed
        if not reference_text or not reference_text.strip():
            logger.info(f"Auto-transcribing speaker {name}...")
            reference_text = transcribe_audio(str(audio_path))
            logger.info(f"Transcribed: {reference_text}")
        
        # Save speaker info
        speakers_db[speaker_id] = {
            "id": speaker_id,
            "name": name,
            "description": description,
            "reference_text": reference_text,
            "audio_file": audio_filename,
            "created_at": datetime.now().isoformat()
        }
        
        save_speakers_db()
        
        return JSONResponse({
            "success": True,
            "speaker_id": speaker_id,
            "speaker": speakers_db[speaker_id]
        })
        
    except Exception as e:
        logger.error(f"Create speaker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/speakers/{speaker_id}", tags=["Speaker Management"])
async def update_speaker(
    speaker_id: str,
    name: str = Form(None, description="Speaker name"),
    description: str = Form(None, description="Speaker description")
):
    """
    Update speaker information
    
    Updates the name and/or description of an existing speaker.
    """
    if speaker_id not in speakers_db:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    if name:
        speakers_db[speaker_id]["name"] = name
    if description is not None:
        speakers_db[speaker_id]["description"] = description
    
    save_speakers_db()
    
    return JSONResponse({
        "success": True,
        "speaker": speakers_db[speaker_id]
    })


@app.delete("/api/speakers/{speaker_id}", tags=["Speaker Management"])
async def delete_speaker(speaker_id: str):
    """
    Delete a speaker
    
    Removes a speaker and their reference audio file.
    """
    if speaker_id not in speakers_db:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    # Delete audio file
    audio_file = speakers_db[speaker_id].get("audio_file")
    if audio_file:
        audio_path = SPEAKERS_DIR / audio_file
        if audio_path.exists():
            audio_path.unlink()
    
    # Remove from database
    del speakers_db[speaker_id]
    save_speakers_db()
    
    return JSONResponse({
        "success": True,
        "message": f"Speaker {speaker_id} deleted"
    })


@app.post("/api/tts/speaker/{speaker_id}", tags=["Text-to-Speech"])
async def tts_with_speaker(
    speaker_id: str,
    text: str = Form(..., description="Text to convert to speech"),
    max_new_tokens: int = Form(0, description="Maximum tokens per batch", ge=0, le=2048),
    chunk_length: int = Form(300, description="Iterative prompt length", ge=0, le=400),
    top_p: float = Form(0.8, description="Top-P sampling", ge=0.7, le=0.95),
    repetition_penalty: float = Form(1.1, description="Repetition penalty", ge=1.0, le=1.2),
    temperature: float = Form(0.8, description="Sampling temperature", ge=0.7, le=1.0),
):
    """
    Generate speech using a registered speaker
    
    Uses a pre-registered speaker's voice for text-to-speech generation.
    This is more convenient than uploading reference audio each time.
    """
    if speaker_id not in speakers_db:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    try:
        engine = gpu_manager.get_model(load_models)
        
        # Load speaker's reference audio
        speaker_info = speakers_db[speaker_id]
        audio_path = SPEAKERS_DIR / speaker_info["audio_file"]
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Speaker audio file not found")
        
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        references = [{
            "audio": audio_bytes,
            "text": speaker_info["reference_text"]
        }]
        
        request = ServeTTSRequest(
            text=text,
            references=references,
            reference_id=None,
            max_new_tokens=max_new_tokens,
            chunk_length=chunk_length,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            format="wav",
        )
        
        result = list(engine.inference(request))
        
        if result:
            inference_result = result[0]
            if hasattr(inference_result, 'audio') and inference_result.audio:
                sample_rate, audio_array = inference_result.audio
                buffer = io.BytesIO()
                sf.write(buffer, audio_array, sample_rate, format='WAV')
                buffer.seek(0)
                return StreamingResponse(
                    buffer,
                    media_type="audio/wav",
                    headers={"Content-Disposition": f"attachment; filename={speaker_id}_output.wav"}
                )
            else:
                raise HTTPException(status_code=500, detail="No audio generated")
        
        raise HTTPException(status_code=500, detail="Generation failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS with speaker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Gradio inference wrapper
def gradio_inference(
    text, reference_id, reference_audio, reference_text,
    max_new_tokens, chunk_length, top_p, repetition_penalty,
    temperature, seed, use_memory_cache
):
    """Gradio inference function with auto-transcription"""
    try:
        if not text or not text.strip():
            return None, "Please enter text to generate"
        
        # Auto-transcribe reference audio if provided but no reference text
        if reference_audio and (not reference_text or not reference_text.strip()):
            logger.info("Auto-transcribing reference audio...")
            reference_text = transcribe_audio(reference_audio)
            logger.info(f"Transcribed text: {reference_text}")
        
        engine = gpu_manager.get_model(load_models)
        
        references = []
        if reference_audio:
            # Gradio passes file path as string, need to read as bytes
            with open(reference_audio, 'rb') as f:
                audio_bytes = f.read()
            references.append({"audio": audio_bytes, "text": reference_text})
        
        request = ServeTTSRequest(
            text=text,
            references=references,
            reference_id=reference_id if reference_id else None,
            max_new_tokens=max_new_tokens,
            chunk_length=chunk_length,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            format="wav",
        )
        
        result = list(engine.inference(request))
        
        if result:
            inference_result = result[0]
            # Extract audio from InferenceResult: audio is (sample_rate, np.ndarray)
            if hasattr(inference_result, 'audio') and inference_result.audio:
                sample_rate, audio_array = inference_result.audio
                return (sample_rate, audio_array), ""
            else:
                return None, "No audio generated"
        
        return None, "Generation failed - no output produced"
        
    except Exception as e:
        logger.error(f"Gradio inference error: {e}")
        return None, f"Error: {str(e)}"


# Build Gradio UI
logger.info("Building Gradio UI...")
gradio_app = build_app(gradio_inference, theme="light")

# Mount Gradio to FastAPI
logger.info("Mounting Gradio app...")
app = gr.mount_gradio_app(app, gradio_app, path="/")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Fish Speech Unified Server")
    logger.info("=" * 60)
    logger.info(f"Port: {PORT}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"Model: {LLAMA_PATH}")
    logger.info(f"Compile: {COMPILE}")
    logger.info(f"Half Precision: {HALF}")
    logger.info("=" * 60)
    logger.info(f"UI:     http://0.0.0.0:{PORT}")
    logger.info(f"API:    http://0.0.0.0:{PORT}/api/tts")
    logger.info(f"Docs:   http://0.0.0.0:{PORT}/docs")
    logger.info(f"Health: http://0.0.0.0:{PORT}/health")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
    )
