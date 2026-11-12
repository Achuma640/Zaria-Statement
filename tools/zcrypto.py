"""Decrypt / re-encrypt the PIN-locked report pages (PBKDF2-SHA256 600k + AES-GCM)."""
import base64, json, os, re
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_d = base64.b64decode
_e = lambda b: base64.b64encode(b).decode()
PAT = re.compile(r"var (ENC|E)=(\{.*?\});")

def _key(pin, salt, n):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=n).derive(pin.encode())

def load(path, pin):
    html = open(path).read()
    m = PAT.search(html)
    E = json.loads(m.group(2))
    data = AESGCM(_key(pin, _d(E["s"]), E["n"])).decrypt(_d(E["i"]), _d(E["c"]), None)
    return html, m, json.loads(data)

def save(path, html, m, payload, pin):
    """Re-encrypt payload with a fresh salt/IV and write it into the page."""
    salt, iv = os.urandom(16), os.urandom(12)
    n = json.loads(m.group(2))["n"]
    ct = AESGCM(_key(pin, salt, n)).encrypt(iv, json.dumps(payload, separators=(",", ":")).encode(), None)
    new = "var %s=%s;" % (m.group(1), json.dumps({"s": _e(salt), "i": _e(iv), "c": _e(ct), "n": n}, separators=(",", ":")))
    open(path, "w").write(html[:m.start()] + new + html[m.end():])
