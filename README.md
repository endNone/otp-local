<p align="left">
    English&nbsp ｜ &nbsp<a href="README_CN.md">中文</a>
</p>
<br>

# otp-local

Offline **TOTP / HOTP** Generator.  
No cloud · No internet · No tracking.

Generate one-time passwords locally from **QR codes** or `otpauth://` URIs.  
Fully compatible with **Google Authenticator**, **FreeOTP**, **FreeOTP Plus**.


---

## 📦 Installation

### Python dependencies
```bash
pip install pillow pyzbar pexpect
```

### System dependency (required by pyzbar)

**Linux**
```bash
sudo apt install libzbar0
```

**macOS**
```bash
brew install zbar
```

---

## 🛠 Usage

### Step 1️⃣ Decode QR Code

```bash
python otp_local/qr.py
python otp_local/qr.py image.png
```

Supported formats:
```
png / jpg / jpeg / webp
```

Output:
```
otpauth.txt
```

---

### Step 2️⃣ Generate OTP (Live)

```bash
python main.py
```

Example output:
```
[OTP] 123456  |  Valid for 27s
```

---

## 🔐 SSH Auto Login (Optional)

Environment variables:
```bash
export OTP_SSH_USER=username
export OTP_SSH_HOST=example.com
export OTP_SSH_PORT=22
```

```bash
python ssh_auto.py
```

---

## 🔒 Security Notes

- ❌ No internet access
- ❌ No cloud synchronization
- ❌ No secret upload
- ✔ All secrets stay local
- ✔ RFC 4226 / 6238 compliant

---

## 📁 Project Structure

```
otp-local/
├── otp_local/
│   ├── __init__.py
│   ├── core.py
│   └── qr.py
├── main.py
├── ssh_auto.py
├── otpauth.txt
└── qr.png / qr.jpg
```

---

## 📜 License

MIT
