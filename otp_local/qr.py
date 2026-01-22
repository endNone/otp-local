import sys
import os
from PIL import Image
from pyzbar.pyzbar import decode

def find_qr_image():
    # 优先使用命令行参数
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # 自动检测
    for name in ["qr.png", "qr.jpg", "qr.jpeg", "qr.webp"]:
        if os.path.exists(name):
            return name
    return None

img_file = find_qr_image()

if not img_file:
    print("[ERROR] No QR image found. Usage: python qr.py [image_file]")
    exit(1)

if not os.path.exists(img_file):
    print(f"[ERROR] File not found: {img_file}")
    exit(1)

print(f"[INFO] Loading QR code image: {img_file}")
img = Image.open(img_file)

print("[INFO] Decoding QR code...")
result = decode(img)

if not result:
    print("[ERROR] No QR code found in image")
    exit(1)

data = result[0].data.decode("utf-8")
print(f"[INFO] Decoded data: {data}")

output_file = "otpauth.txt"
with open(output_file, "w") as f:
    f.write(data)

print(f"[SUCCESS] Saved to {output_file}")