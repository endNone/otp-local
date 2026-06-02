"""
hpc_code.py — 一条命令：自动登录 HPC → 申请计算节点 → 保存节点信息 → 弹出 VSCode 连接该节点。

架构：
  本机 --(OTP, ControlMaster 复用)--> 登录网关 --(ProxyJump)--> 申请到的计算节点
  VSCode Remote-SSH 连接计算节点（vscode-server 跑在有资源的计算节点上，不会被登录节点限制杀掉）。

资源（核数/内存/分区/时长）在 hpc.conf 中预定义。个人信息全在 hpc.conf（已 gitignore）。

用法：
  python hpc_code.py              # 申请节点并打开 VSCode（申请前会显示核时成本并确认）
  python hpc_code.py --status     # 查看当前分配
  python hpc_code.py --down       # 取消分配 + 关闭 master
  python hpc_code.py --yes        # 跳过成本确认（自动化用）

依赖：pip install pexpect；本机装有 VSCode（建议装 `code` 命令）。
配置：cp hpc.conf.example hpc.conf 并填写；otpauth.txt 放本目录。
"""
import os
import re
import sys
import json
import time
import math
import shutil
import subprocess
import configparser

OTP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OTP_DIR)
CONF = os.path.join(OTP_DIR, "hpc.conf")
ALLOC_FILE = os.path.join(OTP_DIR, ".hpc_alloc.json")
SSH_CONFIG = os.path.expanduser("~/.ssh/config")
LOGIN_ALIAS = "hpc-login"
COMPUTE_ALIAS = "hpc-compute"
MARK_START = "# >>> hpc_code managed >>>"
MARK_END = "# <<< hpc_code managed <<<"

if sys.platform == "win32":
    import wexpect as pexpect
else:
    import pexpect
from otp_local import otp_now_from_uri

def load_conf():
    if not os.path.exists(CONF):
        sys.exit(f"[ERROR] 缺少 {CONF}，请 `cp hpc.conf.example hpc.conf` 并填写")
    c = configparser.ConfigParser()
    c.read(CONF)
    return c

def mem_to_gb(s):
    s = s.strip().upper()
    m = re.match(r"^([\d.]+)\s*([GMT]?)", s)
    v = float(m.group(1))
    return {"T": v * 1024, "M": v / 1024, "G": v, "": v}[m.group(2)]

def time_to_hours(s):

    d, h, mn, sec = 0, 0, 0, 0
    if "-" in s:
        d, s = s.split("-", 1)
        d = int(d)
    parts = [int(x) for x in s.split(":")]
    while len(parts) < 3:
        parts = [0] + parts
    h, mn, sec = parts
    return d * 24 + h + mn / 60 + sec / 3600

def master_alive():
    return subprocess.run(["ssh", "-O", "check", LOGIN_ALIAS],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0

def write_ssh_block(user, host, port, compute_host):
    """在 ~/.ssh/config 中写入/更新受管块（hpc-login + hpc-compute）。"""
    block = f"""{MARK_START}
Host {LOGIN_ALIAS}
    HostName {host}
    User {user}
    Port {port}
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 12h
    ServerAliveInterval 60

Host {COMPUTE_ALIAS}
    HostName {compute_host}
    User {user}
    ProxyJump {LOGIN_ALIAS}
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
    ServerAliveCountMax 3
{MARK_END}"""
    os.makedirs(os.path.dirname(SSH_CONFIG), exist_ok=True)
    existing = ""
    if os.path.exists(SSH_CONFIG):
        with open(SSH_CONFIG) as f:
            existing = f.read()
    if MARK_START in existing and MARK_END in existing:
        new = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
                     block, existing, flags=re.S)
    else:
        new = (existing.rstrip() + "\n\n" + block + "\n") if existing.strip() else block + "\n"
    with open(SSH_CONFIG, "w") as f:
        f.write(new)
    os.chmod(SSH_CONFIG, 0o600)

def establish_master(user, host, port, compute_placeholder="127.0.0.1"):
    """确保到登录网关的 master 连接存在（自动 OTP）。"""

    write_ssh_block(user, host, port, compute_placeholder)
    if master_alive():
        print(f"[OK] 复用已存在的 {LOGIN_ALIAS} master 连接")
        return
    with open(os.path.join(OTP_DIR, "otpauth.txt")) as f:
        uri = f.read().strip()
    otp, info = otp_now_from_uri(uri)
    remain = info["period"] - (int(time.time()) % info["period"])
    if remain < 5:
        time.sleep(remain + 1)
        otp, _ = otp_now_from_uri(uri)
    print(f"[INFO] 用 OTP 建立到 {host} 的 master 连接 ...")
    child = pexpect.spawn(f"ssh -fN {LOGIN_ALIAS}", timeout=40, encoding="utf-8")
    child.expect(r"[Oo]ne-time [Pp]assword.*:")
    child.sendline(otp)
    idx = child.expect([pexpect.EOF, r"[Oo]ne-time [Pp]assword.*:",
                        r"[Pp]ermission denied", pexpect.TIMEOUT], timeout=30)
    if idx == 1:
        otp, _ = otp_now_from_uri(uri)
        child.sendline(otp)
        child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=30)
    elif idx >= 2:
        sys.exit(f"[ERROR] 认证失败:\n{child.before}")
    time.sleep(1.5)
    if not master_alive():
        sys.exit("[ERROR] master 未建立（检查网络/VPN/OTP）")
    print("[SUCCESS] master 已建立")

def ssh_login(cmd):
    """经 master 在登录节点执行命令，返回 stdout。
    用登录 shell(bash -l)并经 stdin 传命令：加载 SLURM 等 PATH，且避免引号转义问题。"""
    r = subprocess.run(["ssh", LOGIN_ALIAS, "bash -l"],
                       input=cmd, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def node_spec(partition):
    """从 sinfo 取该分区单节点的总 CPU 与总内存(GB)，取最大配置。"""
    out, _, _ = ssh_login(f"sinfo -e -h -p {partition} -o '%c|%m'")
    cpus, mem = 64, 480
    best = 0
    for line in out.splitlines():
        try:
            c, m = line.split("|")
            c = int(c)
            if c > best:
                best, cpus, mem = c, c, int(m) / 1024
        except ValueError:
            continue
    return cpus, mem

AUTO_PARTITIONS = ["intel-sc3", "amd-ep2", "amd-ep2-short"]

def partition_capacity(part, cpus, mem_gb):
    """该分区当前是否有单节点能立即满足 cpus + mem_gb；返回 (能否, 该分区单节点总CPU, 总内存G)。"""
    out, _, _ = ssh_login(f"sinfo -h -N -p {part} -t idle,mix -o '%C|%e|%m'")
    avail = False
    node_cpus, node_mem = 0, 0
    for line in out.splitlines():
        try:
            cstr, free_mb, tot_mb = line.split("|")
            idle = int(cstr.split("/")[1])
            node_cpus = max(node_cpus, int(cstr.split("/")[3]))
            node_mem = max(node_mem, int(tot_mb) / 1024)
            if idle >= cpus and int(free_mb) / 1024 >= mem_gb:
                avail = True
        except (ValueError, IndexError):
            continue
    return avail, node_cpus, node_mem

def pick_partition(conf, cpus, mem_gb):
    """按可用性动态选区。返回 (分区, 是否立即可用, 节点总CPU, 节点总内存G)。"""
    spec = conf["alloc"]["partition"].strip()
    cands = AUTO_PARTITIONS if spec.lower() == "auto" else        [p.strip() for p in spec.split(",") if p.strip()]
    fallback = None
    for p in cands:
        ok, nc, nm = partition_capacity(p, cpus, mem_gb)
        if fallback is None:
            fallback = (p, False, nc or 64, nm or 478)
        if ok:
            return p, True, nc, nm
    return fallback

def cost_preview(conf, part, cpus, mem_gb, node_cpus, node_mem, avail):
    a = conf["alloc"]
    hours = time_to_hours(a["time"])
    cpu_ratio = cpus / node_cpus
    mem_ratio = mem_gb / node_mem
    billed = math.ceil(max(cpu_ratio, mem_ratio) * node_cpus)
    core_hours = billed * hours
    print("\n" + "=" * 56)
    print("  即将申请计算节点（VSCode 用）")
    print("-" * 56)
    print(f"  分区/QOS : {part} / {a['qos']}   ({'立即可用' if avail else '可能需排队'})")
    print(f"  资源     : {cpus} CPU, {a['mem']} 内存, 墙钟上限 {a['time']}")
    print(f"  节点规格 : {node_cpus} CPU / {node_mem:.0f}G")
    print(f"  计费占用 : max(CPU {cpu_ratio:.0%}, 内存 {mem_ratio:.0%}) × {node_cpus} = {billed} 计费CPU")
    print(f"  预估成本 : {billed} × {hours:.1f}h = ~{core_hours:.0f} 核时")
    print("=" * 56)
    return core_hours

def submit_holder(conf, part):
    a = conf["alloc"]
    cmd = (f"sbatch -p {part} -q {a['qos']} -c {a['cpus']} "
           f"--mem={a['mem']} -t {a['time']} -J {a['job_name']} "
           f"--wrap='sleep infinity'")
    out, err, rc = ssh_login(cmd)
    m = re.search(r"Submitted batch job (\d+)", out)
    if not m:
        sys.exit(f"[ERROR] 提交失败: {out} {err}")
    jid = m.group(1)
    print(f"[INFO] 已提交占位作业 {jid}，等待分配节点 ...")
    return jid

def wait_node(jid, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        out, _, _ = ssh_login(f"squeue -j {jid} -h -o '%T|%N'")
        if "|" in out:
            state, node = out.split("|", 1)
            if state == "RUNNING" and node.strip():
                return node.strip()
        time.sleep(3)
    return None

def find_code_cli():
    if shutil.which("code"):
        return "code"
    for p in ("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
              os.path.expanduser("~/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code")):
        if os.path.exists(p):
            return p
    return None

def launch_vscode(remote_path):
    uri_target = f"ssh-remote+{COMPUTE_ALIAS}"
    code = find_code_cli()
    if code:
        subprocess.run([code, "--remote", uri_target, remote_path])
        print(f"[SUCCESS] 已打开 VSCode → {COMPUTE_ALIAS}:{remote_path}")
        return
    folder_uri = f"vscode-remote://{uri_target}{remote_path}"
    subprocess.run(["open", "-b", "com.microsoft.VSCode", "--args", "--folder-uri", folder_uri])
    print(f"[WARN] 未找到 code 命令，已尝试用 open 调起；若没连上请在 VSCode Remote-SSH 手动连主机 {COMPUTE_ALIAS}")

def cmd_up(conf, skip_confirm):
    s = conf["ssh"]
    establish_master(s["user"], s["host"], s["port"])
    if os.path.exists(ALLOC_FILE):
        info = json.load(open(ALLOC_FILE))
        out, _, _ = ssh_login(f"squeue -j {info['jobid']} -h -o '%T|%N'")
        if out.startswith("RUNNING") and "|" in out:
            node = out.split("|", 1)[1].strip()
            print(f"[INFO] 已有活动分配（作业 {info['jobid']} @ {node}），直接复用，不重复申请")
            write_ssh_block(s["user"], s["host"], s["port"], node)
            launch_vscode(conf["vscode"]["remote_path"])
            return
    cpus = int(conf["alloc"]["cpus"])
    mem_gb = mem_to_gb(conf["alloc"]["mem"])
    print("[INFO] 按可用性动态选区 ...")
    part, avail, node_cpus, node_mem = pick_partition(conf, cpus, mem_gb)
    cost_preview(conf, part, cpus, mem_gb, node_cpus, node_mem, avail)
    jid = submit_holder(conf, part)
    node = wait_node(jid)
    if not node:
        sys.exit(f"[ERROR] 等待分配超时（分区 {part} 可能在排队），可 --status 查看或稍后重试")
    print(f"[INFO] 分配到节点：{node}")
    write_ssh_block(s["user"], s["host"], s["port"], node)
    info = {"jobid": jid, "node": node, "partition": part,
            "cpus": conf["alloc"]["cpus"], "mem": conf["alloc"]["mem"],
            "time": conf["alloc"]["time"], "since": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(ALLOC_FILE, "w") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 分配信息已保存 → {ALLOC_FILE}")
    launch_vscode(conf["vscode"]["remote_path"])

def cmd_status(conf):
    if not os.path.exists(ALLOC_FILE):
        print("无记录的分配")
        return
    info = json.load(open(ALLOC_FILE))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    if master_alive():
        out, _, _ = ssh_login(f"squeue -j {info['jobid']} -h -o '%T|%N|%L'")
        print(f"实时状态(State|Node|剩余): {out or '作业已结束'}")
    else:
        print("(master 未连接，无法查询实时状态)")

def cmd_down(conf):
    if os.path.exists(ALLOC_FILE) and master_alive():
        info = json.load(open(ALLOC_FILE))
        ssh_login(f"scancel {info['jobid']}")
        print(f"[INFO] 已取消作业 {info['jobid']}（停止计费）")
    subprocess.run(["ssh", "-O", "exit", LOGIN_ALIAS],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(ALLOC_FILE):
        os.remove(ALLOC_FILE)
    print("[INFO] master 已关闭，分配记录已清除")

def main():
    conf = load_conf()
    args = sys.argv[1:]
    if "--status" in args:
        cmd_status(conf)
    elif "--down" in args:
        cmd_down(conf)
    else:
        cmd_up(conf, skip_confirm="--yes" in args)

if __name__ == "__main__":
    main()
