"""Muhitni tekshirish: python tools/check_env.py"""
import importlib.util
import os
import shutil
import subprocess
import sys

from common import find_bin

ok = True
for b in ("ffmpeg", "ffprobe"):
    p = find_bin(b)
    v = subprocess.run([p, "-version"], capture_output=True, text=True).stdout.splitlines()[0]
    print(f"[ok] {b}: {v[:60]}")
for mod, hint in (("yt_dlp", "pip install -U yt-dlp"), ("faster_whisper", "pip install -U faster-whisper")):
    if importlib.util.find_spec(mod):
        print(f"[ok] {mod}")
    else:
        ok = False
        print(f"[--] {mod} yo'q -> {hint}")
_NODE_WIN = "C:/Program Files/nodejs/node.exe"  # winget o'rnatgan, lekin PATH hali yangilanmagan holat
node = shutil.which("node") or (_NODE_WIN if os.path.exists(_NODE_WIN) else None)
if node:
    print("[ok] node:", subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip(), "(Remotion uchun)")
else:
    print("[--] node yo'q -> winget install OpenJS.NodeJS.LTS (faqat Remotion uchun kerak)")
print("Python:", sys.version.split()[0])
sys.exit(0 if ok else 1)
