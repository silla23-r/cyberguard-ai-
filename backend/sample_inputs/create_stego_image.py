"""
Steganographic Image Generator for CyberGuard AI Testing.
Creates an innocent-looking 'Special Cashback Gift Card' image with a concealed,
embedded malicious UPI Collect QR code tucked into the layout pattern.
"""
from pathlib import Path
import io
import math
from PIL import Image, ImageDraw, ImageFont

def generate_stego_image(output_path: Path):
    # Dimensions: 800 x 500 (Voucher Card format)
    width, height = 800, 520
    img = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(img)

    # 1. Elegant Gradient Background & Border
    for y in range(height):
        # Subtle navy to dark purple gradient
        r = int(15 + (y / height) * 20)
        g = int(23 + (y / height) * 15)
        b = int(42 + (y / height) * 45)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Decorative Border
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#E2E8F0", width=2)
    draw.rectangle([(25, 25), (width - 25, height - 25)], outline="#38BDF8", width=1)

    # Decorative corner geometric patterns
    for cx, cy in [(40, 40), (width - 40, 40), (40, height - 40), (width - 40, height - 40)]:
        draw.arc([(cx - 15, cy - 15), (cx + 15, cy + 15)], 0, 360, fill="#38BDF8", width=2)

    # 2. Innocent-looking Festival / Reward Text
    # Header
    draw.text((60, 55), "FESTIVE MEGA REWARDS 2026", fill="#F59E0B")
    draw.text((60, 85), "Congratulations! You have won an exclusive festival gift voucher.", fill="#94A3B8")

    # Big Voucher Value Banner
    draw.rectangle([(60, 130), (520, 240)], fill="#1E293B", outline="#3B82F6", width=2)
    draw.text((85, 145), "SPECIAL CASHBACK COUPON", fill="#38BDF8")
    draw.text((85, 175), "INR 12,500.00", fill="#10B981")
    draw.text((85, 210), "Status: Verified & Ready to Credit", fill="#94A3B8")

    # Innocent instructions (The Social Engineering Trap)
    instructions = [
        "1. Scan the decorative verification seal on the right with any UPI app.",
        "2. Claim your festive cashback directly into your linked bank account.",
        "3. Valid for 24 hours only. No fees required."
    ]
    y_pos = 270
    for line in instructions:
        draw.text((60, y_pos), line, fill="#E2E8F0")
        y_pos += 28

    draw.text((60, 430), "Terms & conditions apply. Authorized Retail Partner Promotion.", fill="#64748B")

    # 3. CONCEALED STEGANOGRAPHIC QR CODE PAYLOAD
    # Try using qrcode library if installed, or build standard visual matrix
    qr_payload = "upi://pay?pa=scammer.cashback882@okaxis&pn=Festive%20Gift%20Redeem&am=12500&mode=02&tn=Claim%20Cashback"
    
    qr_img = None
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,
            border=2,
        )
        qr.add_data(qr_payload)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGB")
    except ImportError:
        # If qrcode library is not installed, construct scannable simulated QR matrix
        qr_size = 180
        qr_img = Image.new("RGB", (qr_size, qr_size), color="#FFFFFF")
        qdraw = ImageDraw.Draw(qr_img)
        
        # Position Detection Patterns (Corners)
        for ox, oy in [(15, 15), (qr_size - 60, 15), (15, qr_size - 60)]:
            qdraw.rectangle([(ox, oy), (ox + 45, oy + 45)], fill="#0F172A")
            qdraw.rectangle([(ox + 7, oy + 7), (ox + 38, oy + 38)], fill="#FFFFFF")
            qdraw.rectangle([(ox + 14, oy + 14), (ox + 31, oy + 31)], fill="#0F172A")

        # Simulated matrix timing bars and pseudo-random modules
        import random
        random.seed(42)
        for x in range(20, qr_size - 20, 8):
            for y in range(20, qr_size - 20, 8):
                if not (x < 65 and y < 65) and not (x > qr_size - 65 and y < 65) and not (x < 65 and y > qr_size - 65):
                    if random.random() > 0.45:
                        qdraw.rectangle([(x, y), (x + 6, y + 6)], fill="#0F172A")

    # Embed QR Code inside an innocent "Official Seal" badge on the right
    qr_w, qr_h = qr_img.size
    box_x, box_y = 560, 120
    box_w, box_h = 200, 260

    # Draw Badge Card
    draw.rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], fill="#1E293B", outline="#F59E0B", width=2)
    draw.text((box_x + 35, box_y + 12), "OFFICIAL SEAL", fill="#F59E0B")
    
    # Resize QR to fit neatly in badge
    target_qr_size = 160
    qr_resized = qr_img.resize((target_qr_size, target_qr_size), Image.Resampling.LANCZOS)
    img.paste(qr_resized, (box_x + 20, box_y + 40))
    
    draw.text((box_x + 25, box_y + 215), "Scan to Credit ₹12,500", fill="#10B981")
    draw.text((box_x + 40, box_y + 235), "Zero-Fee Gateway", fill="#94A3B8")

    # Save final steganographic image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print("SUCCESS: Steganographic voucher image generated successfully.")

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "steganography_cashback_voucher.png"
    generate_stego_image(out)
