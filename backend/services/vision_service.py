"""
Vision Forensics Service for CyberGuard AI.
Leverages Gemini 2.0 Flash Multimodal Vision with offline fallback heuristics
to extract logos, text, phone numbers, and scam intent from screenshots.
"""
import io
import json
import logging
from typing import Dict, Any, List, Optional
from PIL import Image

from models.schemas import ForensicEvidence
from tools.qr_decoder import decode_qr_from_image
from tools.url_analyzer import extract_urls_from_text
from tools.upi_validator import extract_vpas_from_text

logger = logging.getLogger(__name__)

# Heuristic scam regexes for offline fallback
PHONE_REGEX = r"(?:\+91[\-\s]?)?[6789]\d{9}"

def analyze_text_heuristics(text: str) -> Dict[str, Any]:
    """Extracts brand impersonation, urgency, and contact info from raw message text."""
    text_lower = text.lower()
    
    brand = None
    if "sbi" in text_lower or "yono" in text_lower:
        brand = "State Bank of India (YONO)"
    elif "hdfc" in text_lower:
        brand = "HDFC Bank"
    elif "icici" in text_lower:
        brand = "ICICI Bank"
    elif "axis" in text_lower:
        brand = "Axis Bank"
    elif "paytm" in text_lower:
        brand = "Paytm"
    elif "phonepe" in text_lower:
        brand = "PhonePe Rewards"
    elif "amazon" in text_lower:
        brand = "Amazon"
    elif "electricity" in text_lower or "power" in text_lower or "bescom" in text_lower:
        brand = "State Electricity Board (BESCOM)"
    elif "police" in text_lower or "cbi" in text_lower or "customs" in text_lower or "cyber crime" in text_lower:
        brand = "Law Enforcement / Police"
    elif "fedex" in text_lower or "courier" in text_lower:
        brand = "FedEx / Courier Service"

    urgency = []
    if "immediately" in text_lower or "urgent" in text_lower or "now" in text_lower:
        urgency.append("Urgent action demanded")
    if "disconnect" in text_lower or "cut off" in text_lower or "blackout" in text_lower:
        urgency.append("Immediate service disconnection threat (Electricity/SIM)")
    if "arrest" in text_lower or "warrant" in text_lower or "custody" in text_lower:
        urgency.append("Imminent arrest / police warrant intimidation")
    if "block" in text_lower or "suspended" in text_lower or "deactivated" in text_lower:
        urgency.append("Account suspension / debit card freeze threat")
    if "kyc" in text_lower or "pan" in text_lower or "aadhaar" in text_lower:
        urgency.append("Forced KYC / credential verification demand")
    if "within 24 hours" in text_lower or "tonight" in text_lower or "2 hours" in text_lower:
        urgency.append("Tight time-limit countdown pressure")

    import re
    phones = re.findall(PHONE_REGEX, text)

    return {
        "impersonated_brand": brand,
        "urgency_signals": urgency,
        "phone_numbers": list(dict.fromkeys(phones))
    }

def _heuristic_vision_fallback(text: str) -> Dict[str, Any]:
    return analyze_text_heuristics(text)

def check_lsb_steganography(image_bytes: bytes) -> Optional[str]:
    """Inspects pixel least significant bits for concealed steganographic payloads."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        pixels = img.load()
        width, height = img.size
        bits = []
        limit = min(width * height, 5000)
        count = 0
        for y in range(height):
            for x in range(width):
                px = pixels[x, y]
                r, g, b = px[0], px[1], px[2]
                bits.append(str(r & 1))
                bits.append(str(g & 1))
                bits.append(str(b & 1))
                count += 1
                if count >= limit:
                    break
            if count >= limit:
                break
        
        all_bits = ''.join(bits)
        chars = []
        for i in range(0, len(all_bits), 8):
            byte = all_bits[i:i+8]
            if len(byte) < 8:
                break
            char = chr(int(byte, 2))
            chars.append(char)
            if "".join(chars[-11:]) == "<END_STEGO>":
                return "".join(chars[:-11])
    except Exception as e:
        logger.debug(f"LSB check skipped or failed: {e}")
    return None

async def analyze_image(image_bytes: bytes, gemini_api_key: str = "") -> ForensicEvidence:
    """
    Analyzes an uploaded screenshot or photo.
    Extracts QR codes, visual brand impersonation, URLs, phone numbers, and scam intent.
    """
    evidence = ForensicEvidence()
    
    # Step 1: Decode any embedded QR Code (local CV pass)
    qr_result = decode_qr_from_image(image_bytes)
    if qr_result:
        evidence.qr_payload = qr_result.get("raw_payload")
        evidence.qr_parsed = qr_result
        if qr_result.get("type") == "WEB_URL":
            evidence.extracted_urls.append(qr_result["url"])
        elif qr_result.get("type") == "UPI_PAYMENT" and "upi_details" in qr_result:
            upi_det = qr_result["upi_details"]
            if upi_det.get("payee_vpa"):
                evidence.upi_vpas.append(upi_det["payee_vpa"])

    # Step 1B: LSB Steganography Pixel Extraction Pass
    stego_text = check_lsb_steganography(image_bytes)
    if stego_text:
        evidence.raw_text = (evidence.raw_text or "") + f" [Steganographic Payload: {stego_text}]"
        evidence.urgency_signals.append("Concealed LSB pixel-level steganography payload detected")
        stego_urls = extract_urls_from_text(stego_text)
        evidence.extracted_urls.extend(stego_urls)

    # Step 2: Gemini 2.0 Flash Multimodal Vision
    if gemini_api_key and gemini_api_key.strip() != "your_gemini_api_key_here":
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_api_key.strip())
            
            prompt = """
            You are a senior digital forensics and cyber fraud investigator.
            Analyze this screenshot or photo thoroughly for signs of financial fraud, UPI scams, phishing, or coercion.
            
            Return ONLY a valid JSON object matching this schema:
            {
                "extracted_text": "all readable text from image",
                "impersonated_brand": "brand or authority spoofed, e.g. SBI, Bescom, FedEx, Mumbai Police, or null if none",
                "phone_numbers": ["list of phone numbers found"],
                "extracted_urls": ["list of links/domains found"],
                "upi_vpas": ["list of UPI handles found like user@bank"],
                "urgency_signals": ["phrases showing intimidation, urgency, arrest threats, or account block threats"]
            }
            """
            
            # Use raw bytes with mime type
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            parsed = json.loads(response.text)
            evidence.raw_text = parsed.get("extracted_text")
            evidence.impersonated_brand = parsed.get("impersonated_brand")
            evidence.phone_numbers.extend(parsed.get("phone_numbers", []))
            evidence.extracted_urls.extend(parsed.get("extracted_urls", []))
            evidence.upi_vpas.extend(parsed.get("upi_vpas", []))
            evidence.urgency_signals.extend(parsed.get("urgency_signals", []))
            
        except Exception as e:
            logger.warning(f"Gemini Vision call failed: {e}. Falling back to heuristic pass.")
            if evidence.raw_text:
                heuristics = _heuristic_vision_fallback(evidence.raw_text)
                if not evidence.impersonated_brand:
                    evidence.impersonated_brand = heuristics.get("impersonated_brand")
                evidence.urgency_signals.extend(heuristics.get("urgency_signals", []))
                evidence.phone_numbers.extend(heuristics.get("phone_numbers", []))
    else:
        # Offline / Demo heuristic pass
        if evidence.raw_text:
            heuristics = _heuristic_vision_fallback(evidence.raw_text)
            evidence.impersonated_brand = heuristics.get("impersonated_brand")
            evidence.urgency_signals.extend(heuristics.get("urgency_signals", []))
            evidence.phone_numbers.extend(heuristics.get("phone_numbers", []))
    
    # Step 3: Deduplicate and normalize
    evidence.extracted_urls = list(dict.fromkeys(evidence.extracted_urls))
    evidence.phone_numbers = list(dict.fromkeys(evidence.phone_numbers))
    evidence.upi_vpas = list(dict.fromkeys(evidence.upi_vpas))
    evidence.urgency_signals = list(dict.fromkeys(evidence.urgency_signals))
    
    return evidence

