<p align="left">
    中文&nbsp ｜ &nbsp<a href="README.md">English</a>
</p>
<br>

# otp-local

离线 **TOTP / HOTP** 一次性密码生成器。  
无需云端 · 无需联网 · 无追踪。

从 **二维码图片** 或 `otpauth://` URI 本地生成动态验证码，  
完全兼容 **Google Authenticator / FreeOTP / FreeOTP Plus**。

---

## 📦 安装

### Python 依赖
```bash
pip install pillow pyzbar pexpect
```

### 系统依赖（pyzbar 必需）

**Linux**
```bash
sudo apt install libzbar0
```

**macOS**
```bash
brew install zbar
```

---

## 🛠 使用方法

### 第一步：解析二维码

```bash
python otp_local/qr.py
python otp_local/qr.py image.png
```

支持格式：
```
png / jpg / jpeg / webp
```

输出文件：
```
otpauth.txt
```

---

### 第二步：生成动态验证码

```bash
python main.py
```

实时显示：
```
[OTP] 123456  |  Valid for 27s
```

---

## 🔐 SSH 自动登录（可选）

可选环境变量：
```bash
export OTP_SSH_USER=用户名
export OTP_SSH_HOST=服务器地址
export OTP_SSH_PORT=22
```

```bash
python ssh_auto.py
```

---

## 🔒 安全说明

- ❌ 不联网
- ❌ 不同步
- ❌ 不上传密钥
- ✔ 所有密钥仅保存在本地
- ✔ 符合 RFC 4226 / RFC 6238 标准

---

## 📁 项目结构

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

## 📜 许可证

MIT
