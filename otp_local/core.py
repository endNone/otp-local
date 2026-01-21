import base64
import hashlib
import hmac
import struct
import time
from urllib.parse import urlparse, parse_qs, unquote


def _b32decode(secret_b32):
    s = secret_b32.strip().replace(" ", "").upper()
    pad = "=" * ((8 - len(s) % 8) % 8)
    return base64.b32decode(s + pad, casefold=True)


def _hotp(key, counter, digits, algorithm):
    algo = algorithm.upper()
    if algo == "SHA1":
        digestmod = hashlib.sha1
    elif algo == "SHA256":
        digestmod = hashlib.sha256
    elif algo == "SHA512":
        digestmod = hashlib.sha512
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, digestmod).digest()
    offset = h[-1] & 0x0F
    code_int = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7fffffff
    code = code_int % (10 ** digits)
    return str(code).zfill(digits)


def parse_otpauth_uri(uri):
    uri = unquote(uri.strip())

    u = urlparse(uri)
    if u.scheme != "otpauth":
        raise ValueError("Not an otpauth URI")

    otp_type = u.netloc.lower()
    label = u.path.lstrip("/")
    qs = parse_qs(u.query)

    def q1(name, default=None):
        v = qs.get(name)
        return v[0] if v else default

    secret = q1("secret")
    if not secret:
        raise ValueError("Missing secret in otpauth URI")

    algorithm = q1("algorithm", "SHA1").upper()
    digits = int(q1("digits", "6"))
    period = int(q1("period", "30"))
    counter = int(q1("counter", "0"))

    issuer_label = None
    account = label
    if ":" in label:
        issuer_label, account = label.split(":", 1)

    return {
        "type": otp_type,
        "label": label,
        "issuer": q1("issuer") or issuer_label,
        "account": account,
        "secret_b32": secret,
        "algorithm": algorithm,
        "digits": digits,
        "period": period,
        "counter": counter,
    }


def otp_now_from_uri(uri, at_time=None):
    info = parse_otpauth_uri(uri)
    key = _b32decode(info["secret_b32"])
    now = int(time.time()) if at_time is None else int(at_time)

    if info["type"] == "totp":
        timestep = now // info["period"]
        code = _hotp(key, timestep, info["digits"], info["algorithm"])
    elif info["type"] == "hotp":
        code = _hotp(key, info["counter"], info["digits"], info["algorithm"])
    else:
        raise ValueError(f"Unsupported otp type: {info['type']}")

    return code, info