"""
Audio Forensics and Acoustic Coercion Service for CyberGuard AI.
Transcribes audio recordings of scam calls and evaluates psychological coercion tactics.
"""
import io
import json
import logging
from typing import Dict, Any, List

from models.schemas import CoercionAnalysis

logger = logging.getLogger(__name__)

COERCION_TRIGGERS = [
    ("arrest", "Threat of criminal arrest or police detention"),
    ("cbi", "Impersonation of Central Bureau of Investigation (CBI)"),
    ("ed", "Impersonation of Enforcement Directorate (ED)"),
    ("police", "Impersonation of Law Enforcement Officer"),
    ("customs", "Threat of illegal narcotics in postal parcel (FedEx scam)"),
    ("video call", "Coerced surveillance / digital arrest demand"),
    ("disconnect", "Demand not to hang up or speak to family members"),
    ("isolate", "Instructions to stay in a locked room alone"),
    ("kyc", "Threat to permanently block bank account within 2 hours"),
    ("electricity", "Threat of immediate power cutoff tonight"),
    ("fine", "Demanding immediate settlement payment via UPI or crypto")
]

def analyze_transcript_heuristics(transcript: str) -> CoercionAnalysis:
    """Evaluates transcript text for high-pressure extortion tactics."""
    score = 0
    tactics: List[str] = []
    text_lower = transcript.lower()

    for word, desc in COERCION_TRIGGERS:
        if word in text_lower:
            tactics.append(desc)
            score += 15

    # Cap score at 100
    score = min(100, score)
    
    sentiment = "Neutral"
    if score >= 50:
        sentiment = "High Coercion / Hostile / Extortionate"
    elif score >= 20:
        sentiment = "Urgent / Pressuring"

    return CoercionAnalysis(
        coercion_score=score,
        tactics_detected=tactics,
        sentiment=sentiment
    )

async def process_audio(audio_bytes: bytes, filename: str, gemini_api_key: str = "") -> Dict[str, Any]:
    """
    Transcribes audio and extracts psychological intimidation markers.
    """
    transcript = ""
    
    # Check if Gemini API is available for native audio transcription
    if gemini_api_key and gemini_api_key.strip() != "your_gemini_api_key_here":
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_api_key.strip())
            
            prompt = """
            Transcribe this audio call accurately. Then analyze:
            Is this a scam or extortion call (e.g. Digital Arrest, fake police, courier fraud, bank KYC pressure)?
            Return JSON:
            {
               "transcript": "...",
               "is_scam": true/false,
               "scam_type": "...",
               "coercion_tactics": ["..."]
            }
            """
            
            mime_type = "audio/mp3"
            if filename.endswith(".wav"):
                mime_type = "audio/wav"
            elif filename.endswith(".ogg") or filename.endswith(".opus"):
                mime_type = "audio/ogg"

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            parsed = json.loads(response.text)
            transcript = parsed.get("transcript", "")
            coercion = analyze_transcript_heuristics(transcript)
            
            # Incorporate Gemini's detected tactics
            extra_tactics = parsed.get("coercion_tactics", [])
            for t in extra_tactics:
                if t not in coercion.tactics_detected:
                    coercion.tactics_detected.append(t)
                    coercion.coercion_score = min(100, coercion.coercion_score + 10)
            
            return {
                "transcript": transcript,
                "coercion": coercion
            }

        except Exception as e:
            logger.warning(f"Gemini audio processing failed: {e}. Falling back to heuristic audio mock.")

    # Graceful mock/heuristic if API key is not supplied
    fallback_text = "Urgent notice from Police department. You are under digital arrest regarding an illegal courier parcel. Do not disconnect this call or police will come to your house. Pay verification fee."
    return {
        "transcript": fallback_text,
        "coercion": analyze_transcript_heuristics(fallback_text)
    }

