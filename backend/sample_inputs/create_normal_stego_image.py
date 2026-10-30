"""
True LSB (Least Significant Bit) Steganography Image Generator.
Creates a completely normal-looking scenic sunset photograph where a hidden
malicious phishing link is imperceptibly embedded into the least significant bits
of the pixel colors. To the human eye, it looks 100% like a normal wallpaper photo.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import math

def create_scenic_photo(width=800, height=600) -> Image.Image:
    """Generates an aesthetic, natural-looking sunset over mountain landscape."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # 1. Natural Sunset Sky Gradient (Deep Indigo -> Warm Amber -> Golden Sun)
    for y in range(height):
        ratio = y / height
        if ratio < 0.5:
            # Upper sky: Twilight Deep Indigo to Purple
            t = ratio / 0.5
            r = int(30 + t * (217 - 30))
            g = int(27 + t * (83 - 27))
            b = int(75 + t * (79 - 75))
        else:
            # Lower sky: Warm Orange to Sunset Gold
            t = (ratio - 0.5) / 0.5
            r = int(217 + t * (255 - 217))
            g = int(83 + t * (178 - 83))
            b = int(79 + t * (55 - 79))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Glowing Sun near horizon
    sun_x, sun_y = 400, 310
    for radius in range(70, 0, -2):
        alpha = int(255 * (1 - radius / 70))
        draw.ellipse(
            [(sun_x - radius, sun_y - radius), (sun_x + radius, sun_y + radius)],
            fill=(255, 235, 150)
        )

    # 3. Layered Natural Mountain Silhouettes
    # Distant Mountains (soft purple-gray)
    mountain1_points = [(0, 360)]
    for x in range(0, width + 20, 20):
        y = 350 - 45 * math.sin(x * 0.008) - 25 * math.cos(x * 0.02)
        mountain1_points.append((x, int(y)))
    mountain1_points.extend([(width, height), (0, height)])
    draw.polygon(mountain1_points, fill=(78, 42, 70))

    # Mid-range Mountains (darker slate)
    mountain2_points = [(0, 420)]
    for x in range(0, width + 20, 20):
        y = 410 - 55 * math.sin(x * 0.012 + 1.2) - 30 * math.cos(x * 0.018)
        mountain2_points.append((x, int(y)))
    mountain2_points.extend([(width, height), (0, height)])
    draw.polygon(mountain2_points, fill=(45, 24, 46))

    # Foreground Hills (Deep Silhouetted Charcoal)
    mountain3_points = [(0, 490)]
    for x in range(0, width + 15, 15):
        y = 485 - 35 * math.sin(x * 0.015 + 2.5) - 15 * math.cos(x * 0.03)
        mountain3_points.append((x, int(y)))
    mountain3_points.extend([(width, height), (0, height)])
    draw.polygon(mountain3_points, fill=(18, 11, 22))

    # 4. Subtle pine tree silhouettes in foreground
    for tx in [120, 145, 175, 620, 660, 710]:
        ty = 480
        th = 40
        draw.polygon([(tx, ty - th), (tx - 12, ty), (tx + 12, ty)], fill=(12, 7, 15))
        draw.polygon([(tx, ty - th + 15), (tx - 16, ty + 15), (tx + 16, ty + 15)], fill=(12, 7, 15))

    return img

def encode_lsb_steganography(image: Image.Image, secret_text: str) -> Image.Image:
    """
    Hides a secret string inside the Least Significant Bit (LSB) of the image pixels.
    Leaves the photo visually 100% indistinguishable to human eyes.
    """
    # Append delimiter to know where message ends
    secret_text += "<END_STEGO>"
    binary_message = ''.join(format(ord(c), '08b') for c in secret_text)
    
    encoded = image.copy()
    pixels = encoded.load()
    width, height = encoded.size

    msg_idx = 0
    msg_len = len(binary_message)

    for y in range(height):
        for x in range(width):
            if msg_idx >= msg_len:
                return encoded

            r, g, b = pixels[x, y]

            # Embed 1 bit into the red channel's least significant bit
            if msg_idx < msg_len:
                r = (r & ~1) | int(binary_message[msg_idx])
                msg_idx += 1

            # Embed 1 bit into green channel
            if msg_idx < msg_len:
                g = (g & ~1) | int(binary_message[msg_idx])
                msg_idx += 1

            # Embed 1 bit into blue channel
            if msg_idx < msg_len:
                b = (b & ~1) | int(binary_message[msg_idx])
                msg_idx += 1

            pixels[x, y] = (r, g, b)

    return encoded

def decode_lsb_steganography(image_path: Path) -> str:
    """Extracts hidden LSB steganographic payload from an ordinary image."""
    img = Image.open(image_path)
    pixels = img.load()
    width, height = img.size

    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(str(r & 1))
            bits.append(str(g & 1))
            bits.append(str(b & 1))

    # Convert bit stream into ASCII characters
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

    return "".join(chars[:100])

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    out_file = out_dir / "normal_scenic_photo_stego.png"

    # Step 1: Create ordinary-looking landscape photograph
    base_photo = create_scenic_photo(800, 600)

    # Step 2: Embed concealed phishing payload into LSB pixels
    hidden_payload = "HIDDEN_SCAM_PAYLOAD:https://sbi-kyc-update.xyz/verify-bank?victim_id=9876543210"
    stego_photo = encode_lsb_steganography(base_photo, hidden_payload)

    # Step 3: Save as PNG (lossless to preserve exact LSB pixel bits)
    stego_photo.save(out_file, "PNG")
    print("SUCCESS: Normal scenic photo with hidden steganography created successfully.")

    # Step 4: Verify extraction
    extracted = decode_lsb_steganography(out_file)
    print("VERIFICATION EXTRACTED PAYLOAD: " + extracted)

