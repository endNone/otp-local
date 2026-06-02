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

## 🖥 HPC 计算节点 + VSCode（可选）

`hpc_code.py` 把 OTP 登录变成一条命令：申请一个计算节点，并在**该节点上**打开 VSCode Remote-SSH（而非登录网关）。

链路：`本机 →(OTP, SSH ControlMaster 复用)→ 登录网关 →(ProxyJump)→ 申请到的计算节点`。
vscode-server 跑在计算节点上，不会被登录节点资源限制杀掉。

### 配置
```bash
cp hpc.conf.example hpc.conf      # 填写 user/host/port + 资源（cpus/mem/partition/time）
```
`partition = auto` 会自动挑当前有空闲的分区（也可填逗号分隔的优先级列表）。

### 命令
```bash
python hpc_code.py          # 申请节点 + 打开 VSCode（先显示核时成本并确认）
python hpc_code.py --status # 查看当前分配
python hpc_code.py --down   # 释放分配 + 关闭连接（停止计费）
```

### Alias（可选）
```bash
alias hpcup="python /path/to/otp-local/hpc_code.py"
alias hpcstat="python /path/to/otp-local/hpc_code.py --status"
alias hpcdown="python /path/to/otp-local/hpc_code.py --down"
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
├── hpc_code.py            # HPC 计算节点 + VSCode 启动器
├── hpc.conf.example       # 复制为 hpc.conf（已 gitignore）并填写
├── otpauth.txt
└── qr.png / qr.jpg
```

---

## 📜 许可证

MIT
