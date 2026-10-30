"""
QR Code Forensic Decoder and UPI Intent Parser.
Extracts QR codes from screenshots and analyzes UPI transaction mechanics.
"""
import io
import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlparse
from PIL import Image

logger = logging.getLogger(__name__)

# Try importing pyzbar or fallback to cv2 QRCodeDetector
_HAS_PYZBAR = False
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    _HAS_PYZBAR = True
except ImportError:
    pass

_HAS_CV2 = False
try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    pass

def parse_upi_intent(raw_str: str) -> Dict[str, Any]:
    """
    Parses UPI deep links e.g. upi://pay?pa=scammer@okaxis&pn=Electricity%20Dept&am=12000&mode=02
    Detects critical fraud vectors like collect request inverted scams.
    """
    result: Dict[str, Any] = {
        "is_upi": False,
        "raw": raw_str,
        "payee_vpa": None,
        "payee_name": None,
        "amount": None,
        "currency": "INR",
        "mode": "pay",
        "is_collect_request": False,
        "suspicion_flags": []
    }
    
    if not (raw_str.startswith("upi://") or "pa=" in raw_str):
        return result

    result["is_upi"] = True
    parsed_url = urlparse(raw_str)
    params = parse_qs(parsed_url.query)
    
    # Extract standard UPI parameters
    if "pa" in params:
        result["payee_vpa"] = params["pa"][0]
    if "pn" in params:
        result["payee_name"] = params["pn"][0]
    if "am" in params:
        result["amount"] = params["am"][0]
    if "cu" in params:
        result["currency"] = params["cu"][0]
    if "tn" in params:
        result["note"] = params["tn"][0]
        
    # Check for Collect Request trickery
    # Scammers tell victims: "Scan this QR to receive your prize/refund!"
    # But the QR is a DEBIT/PAYMENT authorization!
    if "mode" in params and params["mode"][0] in ["02", "collect"]:
        result["is_collect_request"] = True
        result["suspicion_flags"].append("QR triggers a bank COLLECT/DEBIT request, NOT a credit/refund!")
        
    if result["amount"] and float(result["amount"] or 0) > 0:
        result["suspicion_flags"].append(f"Scanning this QR will DEDUCT ₹{result['amount']} from your account.")

    return result

def decode_qr_from_image(image_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Inspects image bytes, decodes any present QR code, and classifies its payload.
    """
    decoded_text = None

    # Strategy 1: pyzbar
    if _HAS_PYZBAR:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            results = pyzbar_decode(image)
            if results:
                decoded_text = results[0].data.decode("utf-8")
        except Exception as e:
            logger.debug(f"pyzbar decode failed: {e}")

    # Strategy 2: OpenCV QR Detector
    if not decoded_text and _HAS_CV2:
        try:
            np_arr = np.frombuffer(image_bytes, np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if cv_img is not None:
                detector = cv2.QRCodeDetector()
                data, _, _ = detector.detectAndDecode(cv_img)
                if data:
                    decoded_text = data
        except Exception as e:
            logger.debug(f"OpenCV QR decode failed: {e}")

    if not decoded_text:
        return None

    # Classify the extracted QR text
    info: Dict[str, Any] = {
        "raw_payload": decoded_text,
        "type": "UNKNOWN"
    }

    if decoded_text.startswith("upi://") or "pa=" in decoded_text:
        info["type"] = "UPI_PAYMENT"
        info["upi_details"] = parse_upi_intent(decoded_text)
    elif re.match(r"^https?://", decoded_text, re.IGNORECASE):
        info["type"] = "WEB_URL"
        info["url"] = decoded_text
    else:
        info["type"] = "PLAIN_TEXT"

    return info
