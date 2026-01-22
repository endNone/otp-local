<p align="left">
    中文&nbsp ｜ &nbsp<a href="README.md">English</a>
</p>
<br>

# otp-local

离线 TOTP/HOTP 生成器。无需云端，无需联网，无需追踪。

从二维码或 otpauth:// URI 本地生成一次性密码。支持 SHA1、SHA256、SHA512 算法，6-8 位验证码。

## 安装
```bash
pip install pillow pyzbar
```

## 使用
```bash
python otp_local/qr.py              # 自动检测 qr.png/qr.jpg
python otp_local/qr.py image.jpg    # 指定图片文件
python main.py                      # 从 otpauth.txt 生成 OTP
```

## 输出
```
[SUCCESS] OTP Code: 123456
[INFO] Valid for ~25 seconds
```

## 结构
```
otp-local/
├── otp_local/
│   ├── __init__.py
│   ├── core.py
│   └── qr.py
├── main.py
├── qr.png / qr.jpg   <- 放二维码图片（支持 png, jpg, jpeg, webp）
└── otpauth.txt
```

## 许可证

MIT