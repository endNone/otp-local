<p align="left">
    <a href="README_CN.md">中文</a>&nbsp ｜ &nbspEnglish
</p>
<br>

# otp-local

Offline TOTP/HOTP Generator. No cloud, no internet, no tracking.

Generate one-time passwords locally from QR codes or otpauth:// URIs. Supports SHA1, SHA256, SHA512 algorithms with 6-8 digit codes.

## Install
```bash
pip install pillow pyzbar
```

## Usage
```bash
python otp_local/qr.py    # Decode QR code -> otpauth.txt
python main.py            # Generate OTP from otpauth.txt
```

## Output
```
[SUCCESS] OTP Code: 123456
[INFO] Valid for ~25 seconds
```

## Structure
```
otp-local/
├── otp_local/
│   ├── __init__.py
│   ├── core.py
│   └── qr.py
├── main.py
├── qr.png <- Put your QR code image here
└── otpauth.txt
```

## License

MIT