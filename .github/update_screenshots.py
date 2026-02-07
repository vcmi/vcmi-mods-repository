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

def parse_raw_mod_url(url: str):
    """
    Expected:
      https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path_to_modjson}
    Returns: (owner, repo, ref, path_to_modjson) or (None,...)
    """
    m = re.match(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.*)$", url)
    if not m:
        return None, None, None, None
    return m.group(1), m.group(2), m.group(3), m.group(4)

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

for filename in glob.glob(os.path.join('.', '*.json')):
    if filename in ignore:
        continue

    print(f"Opening: {filename}")
    filecontent = open(filename, "r", encoding="utf-8").read()
    modlist = json.loads(filecontent)

    items = (
        modlist.items()
        if 'availableMods' not in modlist
        else modlist["availableMods"].items()
    )

    for mod, data in items:
        mod_url = (data.get("mod") or "").replace(" ", "%20")
        owner, repo, ref, mod_path = parse_raw_mod_url(mod_url)
        if not owner or not repo or not ref or not mod_path:
            print(f"Skipping {mod}: not a raw.githubusercontent.com mod URL")
            continue

        mod_dir = os.path.dirname(mod_path).replace("\\", "/").strip("/")
        candidates = [
            "screenshots",
            "Screenshots",
            f"{mod_dir}/screenshots" if mod_dir else "",
            f"{mod_dir}/Screenshots" if mod_dir else "",
            "mod-repo/screenshots",
            "mod-repo/Screenshots",
        ]
        candidates = [c for c in candidates if c]

        found = []
        for folder in candidates:
            urls = list_pngs(owner, repo, ref, folder)
            if urls:
                found = urls
                print(f"{mod}: found {len(found)} screenshots in {owner}/{repo}@{ref}:{folder}")
                break

        if found:
            data["screenshots"] = found
        else:
            # keep existing screenshots if any
            if "screenshots" in data:
                print(f"{mod}: no screenshots found, keeping existing ({len(data.get('screenshots', []))})")
            else:
                print(f"{mod}: no screenshots found, and none present")

    resultcontent = json.dumps(
        modlist,
        indent='\t',
        separators=(',', ' : ')
    ) + "\n"

    if filecontent != resultcontent:
        open(filename, "w", encoding="utf-8").write(resultcontent)

sys.exit(os.EX_OK)
