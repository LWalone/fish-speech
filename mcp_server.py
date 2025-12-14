#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Optional

import pyrootutils
import torch
from fastmcp import FastMCP
from loguru import logger

pyrootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

from fish_speech.inference_engine import TTSInferenceEngine
from fish_speech.models.dac.inference import load_model as load_decoder_model
from fish_speech.models.text2semantic.inference import launch_thread_safe_queue
from fish_speech.utils.schema import ServeTTSRequest
from gpu_manager import gpu_manager

os.environ["EINX_FILTER_TRACEBACK"] = "false"

mcp = FastMCP("Fish Speech TTS")

# Configuration
DEVICE = os.getenv("BACKEND", "cuda")
COMPILE = os.getenv("COMPILE", "0") == "1"
HALF = os.getenv("HALF", "0") == "1"
LLAMA_PATH = Path(os.getenv("LLAMA_CHECKPOINT_PATH", "checkpoints/openaudio-s1-mini"))
DECODER_PATH = Path(os.getenv("DECODER_CHECKPOINT_PATH", "checkpoints/openaudio-s1-mini/codec.pth"))
DECODER_CONFIG = os.getenv("DECODER_CONFIG_NAME", "modded_dac_vq")


def load_models():
    precision = torch.half if HALF else torch.bfloat16
    
    logger.info("Loading models...")
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
    
    engine = TTSInferenceEngine(
        llama_queue=llama_queue,
        decoder_model=decoder_model,
        compile=COMPILE,
        precision=precision,
    )
    
    # Warmup
    list(engine.inference(ServeTTSRequest(
        text="Hello.",
        references=[],
        max_new_tokens=1024,
        chunk_length=200,
        top_p=0.7,
        repetition_penalty=1.5,
        temperature=0.7,
        format="wav",
    )))
    
    return engine


@mcp.tool()
def generate_speech(
    text: str,
    output_path: str,
    reference_audio: Optional[str] = None,
    reference_text: Optional[str] = None,
    max_new_tokens: int = 0,
    chunk_length: int = 300,
    top_p: float = 0.8,
    repetition_penalty: float = 1.1,
    temperature: float = 0.8,
) -> dict:
    """
    Generate speech from text using Fish Speech TTS.
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the generated audio (WAV format)
        reference_audio: Optional path to reference audio file for voice cloning
        reference_text: Optional text transcript of reference audio
        max_new_tokens: Maximum tokens per batch (0 = no limit)
        chunk_length: Iterative prompt length (0 = off)
        top_p: Top-P sampling parameter (0.7-0.95)
        repetition_penalty: Repetition penalty (1.0-1.2)
        temperature: Temperature for sampling (0.7-1.0)
    
    Returns:
        Dictionary with status and output path
    """
    try:
        engine = gpu_manager.get_model(load_models)
        
        references = []
        if reference_audio and reference_text:
            references.append({"audio": reference_audio, "text": reference_text})
        
        request = ServeTTSRequest(
            text=text,
            references=references,
            max_new_tokens=max_new_tokens,
            chunk_length=chunk_length,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            format="wav",
        )
        
        result = list(engine.inference(request))
        
        if result:
            with open(output_path, "wb") as f:
                f.write(result[0])
            
            gpu_manager.force_offload()
            
            return {
                "status": "success",
                "output_path": output_path,
                "message": f"Audio generated successfully at {output_path}"
            }
        
        return {"status": "error", "message": "Generation failed"}
        
    except Exception as e:
        gpu_manager.force_offload()
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_gpu_status() -> dict:
    """
    Get current GPU status and memory usage.
    
    Returns:
        Dictionary with GPU status information
    """
    return gpu_manager.get_status()


@mcp.tool()
def offload_gpu() -> dict:
    """
    Force offload model from GPU to free memory.
    
    Returns:
        Dictionary with offload status
    """
    gpu_manager.force_offload()
    return {"status": "success", "message": "GPU memory freed"}


if __name__ == "__main__":
    mcp.run()
