"""
Multilingual Text-to-Speech (TTS) Advisory Service for CyberGuard AI.
Uses Microsoft Edge TTS to generate natural regional language voice warnings.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Regional Voice Mappings (High quality neural voices)
VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",     # Indian English (Female)
    "hi": "hi-IN-MadhurNeural",     # Hindi (Male)
    "te": "te-IN-MohanNeural",      # Telugu (Male)
    "ta": "ta-IN-PallaviNeural",    # Tamil (Female)
    "bn": "bn-IN-BashkarNeural"     # Bengali (Male)
}

async def generate_voice_advisory(
    text: str,
    language: str,
    output_dir: Path,
    session_id: str
) -> Optional[Path]:
    """
    Generates an MP3 voice briefing for users who prefer listening to spoken guidance.
    """
    output_path = output_dir / f"Advisory_{session_id}.mp3"
    voice = VOICE_MAP.get(language, VOICE_MAP["en"])

    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        return output_path
    except ImportError:
        logger.warning("edge-tts library not installed; skipping voice generation.")
        return None
    except Exception as e:
        logger.warning(f"Failed to generate TTS audio with voice {voice}: {e}")
        return None

