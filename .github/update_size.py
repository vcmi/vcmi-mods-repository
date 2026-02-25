import json
import glob
import os
import sys
import urllib.request
import urllib.error
import re

from ignore_json import ignore


URL_SIZE_CACHE = {}


def parse_size_from_headers(headers) -> int:
    content_length = headers.get("Content-Length")
    if content_length and content_length.isdigit():
        return int(content_length)

    content_range = headers.get("Content-Range", "")
    match = re.match(r"^bytes\s+\d+-\d+/(\d+)$", content_range)
    if match:
        return int(match.group(1))

    return 0


def fetch_download_size_bytes(url: str) -> int:
    if url in URL_SIZE_CACHE:
        return URL_SIZE_CACHE[url]

    headers = {"User-Agent": "vcmi-downloadsize-script"}

    # Fast path: HEAD with redirects and Content-Length
    req = urllib.request.Request(url, headers=headers, method="HEAD")
    with urllib.request.urlopen(req, timeout=15) as resp:
        size = parse_size_from_headers(resp.headers)
    if size > 0:
        URL_SIZE_CACHE[url] = size
        return size

    # Fallback: range probe for servers not exposing Content-Length on HEAD
    range_headers = dict(headers)
    range_headers["Range"] = "bytes=0-0"
    req = urllib.request.Request(url, headers=range_headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        size = parse_size_from_headers(resp.headers)
    if size > 0:
        URL_SIZE_CACHE[url] = size
        return size

    # Some hosts don't expose size on HEAD/Range. Try regular GET headers first.
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        size = parse_size_from_headers(resp.headers)
        if size > 0:
            URL_SIZE_CACHE[url] = size
            return size

        # Last-resort fallback: stream body and count bytes.
        total = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)

    if total > 0:
        URL_SIZE_CACHE[url] = total
        return total

    raise ValueError("size not available from response headers/body")


def gha_notice(msg: str) -> None:
    print(f"::notice::{msg}")


def gha_warning(msg: str) -> None:
    print(f"::warning::{msg}")


def log_open(filename: str) -> None:
    print(f"\n📄 Opening: {filename}")


def log_ok(mod: str, size_mb: float) -> None:
    print(f"✅ {mod}: {size_mb} MB")


def log_keep(mod: str, reason: str, existing) -> None:
    if isinstance(existing, (int, float)):
        print(f"🟠 {mod}: download failed ({reason}) — keeping existing size: {existing} MB")
        gha_warning(f"{mod}: downloadSize kept ({existing} MB) — download failed ({reason})")
    else:
        print(f"⚠️ {mod}: download failed ({reason}) — no existing size to keep")
        gha_warning(f"{mod}: downloadSize missing — download failed ({reason})")


def log_missing_field(mod: str, field: str) -> None:
    print(f"⛔ {mod}: missing field '{field}' (skipping)")
    gha_warning(f"{mod}: missing field '{field}' (skipping)")


stats = {"updated": 0, "kept": 0, "missing": 0}

for filename in glob.glob(os.path.join(".", "*.json")):
    if filename in ignore:
        continue

    log_open(filename)

    filecontent = open(filename, "r", encoding="utf-8").read()
    modlist = json.loads(filecontent)

    items = modlist.items() if "availableMods" not in modlist else modlist["availableMods"].items()

    for mod, data in items:
        if "download" not in data:
            log_missing_field(mod, "download")
            stats["missing"] += 1
            continue

        url = (data.get("download") or "").replace(" ", "%20")
        if not url:
            log_missing_field(mod, "download")
            stats["missing"] += 1
            continue

        # Keep existing if we fail
        existing = data.get("downloadSize")

        try:
            size_bytes = fetch_download_size_bytes(url)
            filesize = round(size_bytes / 1024 / 1024, 3)
            data["downloadSize"] = filesize
            log_ok(mod, filesize)
            gha_notice(f"{mod}: downloadSize updated to {filesize} MB")
            stats["updated"] += 1

        except Exception as e:
            # Be robust: keep existing and continue
            reason = str(e)
            log_keep(mod, reason, existing)
            stats["kept"] += 1
            continue

    resultcontent = json.dumps(modlist, indent="\t", separators=(",", " : ")) + "\n"

    if filecontent != resultcontent:
        open(filename, "w", encoding="utf-8").write(resultcontent)

print("\n==== 📦 Download size summary ====")
print(f"✅ updated : {stats['updated']}")
print(f"🟠 kept   : {stats['kept']}")
print(f"⛔ missing: {stats['missing']}")

sys.exit(os.EX_OK)
