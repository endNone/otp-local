from PIL import Image
from pyzbar.pyzbar import decode

print("[INFO] Loading QR code image: qr.png")
img = Image.open("qr.png")

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