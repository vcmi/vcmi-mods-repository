import json
import glob
import os
import sys
import urllib.request
import urllib.parse
import re

from ignore_json import ignore

GITHUB_API_CONTENTS = "https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def gha_notice(msg: str) -> None:
    print(f"::notice::{msg}")


def gha_warning(msg: str) -> None:
    print(f"::warning::{msg}")


def log_found(mod: str, owner: str, repo: str, ref: str, folder: str, count: int) -> None:
    print(f"✅ {mod}: {count} screenshots | {owner}/{repo}@{ref}:{folder}")


def log_missing(mod: str) -> None:
    print(f"⚠️ {mod}: no screenshots found (none defined)")


def log_keeping(mod: str, existing_count: int) -> None:
    print(f"🟠 {mod}: repo has no screenshots, keeping existing ({existing_count})")


def log_skip(mod: str, reason: str) -> None:
    print(f"⛔ {mod}: {reason}")


def parse_raw_mod_url(url: str):
    """
    Expected:
      https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path_to_modjson}

    NOTE:
      {ref} can also be like "refs/heads/<branch>" (contains '/'),
      so we cannot just take a single path segment.
    Returns: (owner, repo, ref, path_to_modjson) or (None,...)
    """
    m = re.match(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/(.*)$", url)
    if not m:
        return None, None, None, None

    owner, repo, rest = m.group(1), m.group(2), m.group(3)
    parts = rest.split("/")

    if len(parts) >= 3 and parts[0] == "refs" and parts[1] == "heads":
        ref = "/".join(parts[:3])      # refs/heads/<branch>
        path = "/".join(parts[3:])     # remainder
    else:
        if len(parts) < 2:
            return None, None, None, None
        ref = parts[0]                # main, tag, vcmi-1.7, ...
        path = "/".join(parts[1:])

    if not path:
        return None, None, None, None

    return owner, repo, ref, path


def list_pngs(owner: str, repo: str, ref: str, folder: str):
    """
    Returns list of download_url for *.png in given folder (no recursion).
    If folder doesn't exist or isn't a dir, returns [].
    """
    folder = folder.strip("/")
    api_url = GITHUB_API_CONTENTS.format(
        owner=owner,
        repo=repo,
        path=urllib.parse.quote(folder),
        ref=urllib.parse.quote(ref),
    )

    headers = {"User-Agent": "github-screenshots-script"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    pngs = []
    for item in data:
        if item.get("type") != "file":
            continue

        name = item.get("name", "")
        if name.lower().endswith(".png"):
            # download_url is already a raw URL
            dl = item.get("download_url")
            if dl:
                pngs.append((name.lower(), dl))

    pngs.sort(key=lambda x: x[0])
    return [u for _, u in pngs]


stats = {"found": 0, "missing": 0, "keeping": 0, "skip": 0}

for filename in glob.glob(os.path.join(".", "*.json")):
    if filename in ignore:
        continue

    print(f"\n📄 Opening: {filename}")
    filecontent = open(filename, "r", encoding="utf-8").read()
    modlist = json.loads(filecontent)

    items = (
        modlist.items()
        if "availableMods" not in modlist
        else modlist["availableMods"].items()
    )

    for mod, data in items:
        mod_url = (data.get("mod") or "").replace(" ", "%20")
        owner, repo, ref, mod_path = parse_raw_mod_url(mod_url)
        if not owner or not repo or not ref or not mod_path:
            log_skip(mod, "not a raw.githubusercontent.com mod URL")
            stats["skip"] += 1
            continue

        existing = data.get("screenshots")
        existing_count = len(existing) if isinstance(existing, list) else 0

        # Based on your JSON: almost always repo/screenshots (sometimes Screenshots)
        candidates = ["screenshots", "Screenshots"]

        found = []
        found_folder = None
        for folder in candidates:
            urls = list_pngs(owner, repo, ref, folder)
            if urls:
                found = urls
                found_folder = folder
                break

        if found:
            before = existing_count
            after = len(found)
            data["screenshots"] = found
            log_found(mod, owner, repo, ref, found_folder, after)
            gha_notice(f"{mod}: screenshots updated {before} → {after}")
            stats["found"] += 1
        else:
            # keep existing screenshots if any
            if existing_count > 0:
                log_keeping(mod, existing_count)
                gha_warning(f"{mod}: JSON has {existing_count} screenshots, but repo has no screenshots/ folder or PNGs (keeping existing)")
                stats["keeping"] += 1
            else:
                log_missing(mod)
                gha_warning(f"{mod}: no screenshots found in repo (screenshots/), and none defined in JSON")
                stats["missing"] += 1

    resultcontent = json.dumps(
        modlist,
        indent="\t",
        separators=(",", " : "),
    ) + "\n"

    if filecontent != resultcontent:
        open(filename, "w", encoding="utf-8").write(resultcontent)

print("\n==== 🖼️ Screenshots summary ====")
print(f"✅ found   : {stats['found']}")
print(f"⚠️ missing : {stats['missing']}")
print(f"🟠 keeping : {stats['keeping']}")
print(f"⛔ skipped : {stats['skip']}")

sys.exit(os.EX_OK)
