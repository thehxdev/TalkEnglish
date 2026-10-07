import base64
import os
import shutil
import subprocess
import sys

def _try_command(cmd: list[str], text_bytes: bytes) -> bool:
    try:
        subprocess.run(cmd, input=text_bytes, check=True, timeout=2)
        return True
    except (subprocess.SubprocessError, OSError):
        return False

def _emit_osc52(text_bytes: bytes) -> bool:
    try:
        b64_payload = base64.b64encode(text_bytes).decode("ascii")
        osc52_seq = f"\033]52;c;{b64_payload}\a"
        sys.stdout.write(osc52_seq)
        sys.stdout.flush()
        return True
    except Exception:
        return False

def copy_to_system_clipboard(text: str) -> bool:
    if not text:
        return False

    text_bytes = text.encode("utf-8")

    # 1. macOS
    if sys.platform == "darwin":
        if shutil.which("pbcopy") and _try_command(["pbcopy"], text_bytes):
            return True

    # 2. Windows
    if sys.platform == "win32":
        if shutil.which("clip") and _try_command(["clip"], text_bytes):
            return True

    # 3. Linux / BSD / Unix
    is_wayland = bool(os.environ.get("WAYLAND_DISPLAY")) or os.environ.get("XDG_SESSION_TYPE") == "wayland"
    is_x11 = bool(os.environ.get("DISPLAY"))

    # Wayland preferred
    if is_wayland and shutil.which("wl-copy"):
        if _try_command(["wl-copy"], text_bytes):
            return True

    # X11 preferred
    if is_x11:
        if shutil.which("xclip") and _try_command(["xclip", "-selection", "clipboard"], text_bytes):
            return True
        if shutil.which("xsel") and _try_command(["xsel", "--clipboard", "--input"], text_bytes):
            return True

    # Fallback to any installed Linux clipboard binary
    for candidate_args, bin_name in [
        (["wl-copy"], "wl-copy"),
        (["xclip", "-selection", "clipboard"], "xclip"),
        (["xsel", "--clipboard", "--input"], "xsel"),
    ]:
        if shutil.which(bin_name) and _try_command(candidate_args, text_bytes):
            return True

    # 4. ANSI OSC 52 terminal escape sequence fallback
    return _emit_osc52(text_bytes)
