import json
import glob
import os
import sys
import urllib.request
import urllib.error

from ignore_json import ignore


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
            # Add a UA to reduce chances of weird 403s
            req = urllib.request.Request(url, headers={"User-Agent": "vcmi-downloadsize-script"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()

            filesize = round(len(content) / 1024 / 1024, 3)
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
