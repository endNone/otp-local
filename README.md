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

## 🖥 HPC Compute-Node + VSCode (Optional)

`hpc_code.py` turns OTP login into a single command: it allocates a compute node
and opens VSCode Remote-SSH **on that node** (not the login gateway).

Flow: `local →(OTP, SSH ControlMaster reuse)→ login gateway →(ProxyJump)→ allocated compute node`.
The VSCode server runs on the compute node, so it is not killed by login-node limits.

### Configure
```bash
cp hpc.conf.example hpc.conf      # fill in user/host/port + resources (cpus/mem/partition/time)
```
`partition = auto` automatically picks a partition that currently has free capacity
(or give a comma-separated priority list).

### Commands
```bash
python hpc_code.py          # allocate node + open VSCode (prints cost, asks to confirm)
python hpc_code.py --status # show current allocation
python hpc_code.py --down   # release allocation + close connection (stops billing)
```

### Aliases (optional)
```bash
alias hpcup="python /path/to/otp-local/hpc_code.py"
alias hpcstat="python /path/to/otp-local/hpc_code.py --status"
alias hpcdown="python /path/to/otp-local/hpc_code.py --down"
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
├── hpc_code.py            # HPC compute-node + VSCode launcher
├── hpc.conf.example       # copy to hpc.conf (gitignored) and fill in
├── otpauth.txt
└── qr.png / qr.jpg
```

---

## 📜 License

MIT
