import time
import sys
from otp_local import otp_now_from_uri

input_file = "otpauth.txt"

print(f"[INFO] Reading URI from {input_file}")
with open(input_file, "r") as f:
    uri = f.read().strip()

print(f"[INFO] URI loaded: {uri[:50]}...")
print("[INFO] Generating OTP code...")

code, info = otp_now_from_uri(uri)

print(f"[INFO] Type: {info['type'].upper()}")
print(f"[INFO] Issuer: {info['issuer']}")
print(f"[INFO] Account: {info['account']}")
print(f"[INFO] Algorithm: {info['algorithm']}")
print(f"[INFO] Digits: {info['digits']}")
print("-" * 40)
print("[INFO] Press Ctrl+C to exit\n")

try:
    while True:
        code, info = otp_now_from_uri(uri)
        now = int(time.time())
        remain = info["period"] - (now % info["period"])
        sys.stdout.write(f"\r[OTP] {code}  |  Valid for {remain:2d}s  ")
        sys.stdout.flush()
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[INFO] Exited")