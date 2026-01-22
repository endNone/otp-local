#!/usr/bin/env python3
import os
import sys
import time

if sys.platform == "win32":
    import wexpect as pexpect
else:
    import pexpect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from otp_local import otp_now_from_uri

USER = os.environ.get("OTP_SSH_USER") or input("User: ").strip()
HOST = os.environ.get("OTP_SSH_HOST") or input("Host: ").strip()
PORT = os.environ.get("OTP_SSH_PORT") or input("Port [22]: ").strip() or "22"

otpauth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "otpauth.txt")

if not os.path.exists(otpauth_file):
    print(f"[ERROR] {otpauth_file} not found!")
    sys.exit(1)
else:
    with open(otpauth_file, "r") as f:
        uri = f.read().strip()

otp, info = otp_now_from_uri(uri)
now = int(time.time())
remain = info["period"] - (now % info["period"])

if remain < 3:
    print(f"[INFO] Waiting for new OTP...")
    time.sleep(remain + 1)
    otp, info = otp_now_from_uri(uri)
    remain = info["period"]

print(f"[INFO] OTP: {otp} (valid for {remain}s)")
print(f"[INFO] Connecting to {USER}@{HOST}:{PORT}...")

child = pexpect.spawn(f"ssh -p {PORT} {USER}@{HOST}", timeout=30, encoding="utf-8")

child.expect(r"[Oo]ne-time [Pp]assword.*:")
child.sendline(otp)
index = child.expect([r"[\$#>]", r"[Oo]ne-time [Pp]assword", r"[Pp]ermission denied", pexpect.TIMEOUT])

if index == 0:
    print("[SUCCESS] Logged in!")
    child.sendline("")
    child.interact()
elif index == 1:
    print("[ERROR] OTP rejected, trying again...")
    otp, _ = otp_now_from_uri(uri)
    print(f"[INFO] New OTP: {otp}")
    child.sendline(otp)
    child.interact()
elif index == 2:
    print("[ERROR] Permission denied")
else:
    print("[ERROR] Timeout")
    print(child.before)