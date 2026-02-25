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

REF_VERSION_RE = re.compile(r"^(?:vcmi-)?[0-9][0-9A-Za-z._-]*$")
PNG_LIST_CACHE = {}


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


def parse_mod_url(url: str):
    """
    Expected one of:
      - https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path_to_modjson}
      - https://github.com/{owner}/{repo}/blob/{ref}/{path_to_modjson}
      - https://github.com/{owner}/{repo}/releases/download/{ref}/{path_to_modjson}

    NOTE:
      {ref} can also be like "refs/heads/<branch>" (contains '/'),
      so we cannot just take a single path segment.
    Returns: (owner, repo, ref, path_to_modjson) or (None,...)
    """
    raw_match = re.match(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/(.*)$", url)
    if raw_match:
        owner, repo, rest = raw_match.group(1), raw_match.group(2), raw_match.group(3)
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

    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "github.com":
        return None, None, None, None

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 5:
        return None, None, None, None

    owner, repo = parts[0], parts[1]
    route = parts[2]

    if route == "blob" and len(parts) >= 5:
        ref = urllib.parse.unquote(parts[3])
        path = "/".join(parts[4:])
    elif route == "releases" and len(parts) >= 6 and parts[3] == "download":
        ref = urllib.parse.unquote(parts[4])
        path = "/".join(parts[5:])
    else:
        return None, None, None, None

    if not path:
        return None, None, None, None

    return owner, repo, ref, path


def ref_candidates_for_mod(url: str, ref: str, download_url: str = ""):
    """
    Build candidate refs for screenshots lookup.

    For release download URLs we often get tags like "1.7", while screenshots
    in the repo can live on a branch like "vcmi-1.7".
    """
    candidates = []

    def add_candidate(value: str) -> None:
        if value and value not in candidates:
            candidates.append(value)

    parsed = urllib.parse.urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    is_release_download = (
        parsed.netloc == "github.com"
        and len(parts) >= 6
        and parts[2] == "releases"
        and parts[3] == "download"
    )
    
    normalized_ref = ref.strip() if ref else ""

    # For release-hosted mod.json, prefer the VCMI branch convention first:
    # tag/ref "1.7" -> branch "vcmi-1.7".
    if is_release_download and normalized_ref and not normalized_ref.startswith("vcmi-"):
        add_candidate(f"vcmi-{normalized_ref}")

    add_candidate(ref)

    # Deterministic mapping in both directions, but only for version-like refs
    # (e.g. 1.7, vcmi-1.7) to avoid pointless probes like vcmi-main.
    if normalized_ref.startswith("vcmi-"):
        stripped_ref = normalized_ref[len("vcmi-"):]
        if REF_VERSION_RE.match(normalized_ref) and stripped_ref:
            add_candidate(stripped_ref)
    elif normalized_ref and REF_VERSION_RE.match(normalized_ref):
        add_candidate(f"vcmi-{normalized_ref}")

    # Download filename often contains branch hint, e.g. "...-vcmi-1.7.zip"
    if download_url:
        decoded_download = urllib.parse.unquote(download_url)
        filename = os.path.basename(urllib.parse.urlparse(decoded_download).path)
        stem = os.path.splitext(filename)[0]
        branch_hint = re.search(r"(vcmi-[0-9][0-9A-Za-z._-]*)", stem)
        if branch_hint:
            add_candidate(branch_hint.group(1))

    return candidates


def list_pngs(owner: str, repo: str, ref: str, folder: str):
    """
    Returns list of download_url for *.png in given folder (no recursion).
    If folder doesn't exist or isn't a dir, returns [].
    """
    folder = folder.strip("/")
    cache_key = (owner, repo, ref, folder)
    if cache_key in PNG_LIST_CACHE:
        return PNG_LIST_CACHE[cache_key]

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
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        PNG_LIST_CACHE[cache_key] = []
        return []

    if not isinstance(data, list):
        PNG_LIST_CACHE[cache_key] = []
        return []

    pngs = []
    for item in data:
        if item.get("type") != "file":
            continue

        name = item.get("name", "")
        if name.lower().endswith(".png"):
            dl = item.get("download_url")
            if dl:
                pngs.append((name.lower(), dl))

    pngs.sort(key=lambda x: x[0])
    result = [u for _, u in pngs]
    PNG_LIST_CACHE[cache_key] = result
    return result

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
        owner, repo, ref, mod_path = parse_mod_url(mod_url)
        if not owner or not repo or not ref or not mod_path:
            log_skip(mod, "unsupported mod URL")
            stats["skip"] += 1
            continue

        existing = data.get("screenshots")
        existing_count = len(existing) if isinstance(existing, list) else 0

        # Based on your JSON: almost always repo/screenshots (sometimes Screenshots)
        candidates = ["screenshots", "Screenshots"]

        found = []
        found_folder = None
        found_ref = ref
        for candidate_ref in ref_candidates_for_mod(mod_url, ref, data.get("download") or ""):
            for folder in candidates:
                urls = list_pngs(owner, repo, candidate_ref, folder)
                if urls:
                    found = urls
                    found_folder = folder
                    found_ref = candidate_ref
                    break
            if found:
                break

        if found:
            before = existing_count
            after = len(found)
            data["screenshots"] = found
            log_found(mod, owner, repo, found_ref, found_folder, after)
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
