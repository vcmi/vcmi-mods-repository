import json
import glob
import os
import sys
import urllib.request
import urllib.parse
import re

from ignore_json import ignore

def parse_mod_url(url: str):
    """
    Expected one of:
      - https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path_to_modjson}
      - https://github.com/{owner}/{repo}/blob/{ref}/{path_to_modjson}
      - https://github.com/{owner}/{repo}/releases/download/{ref}/{path_to_modjson}

    Returns: (owner, repo, ref, path_to_modjson) or (None, None, None, None)
    """
    raw_match = re.match(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/(.*)$", url)
    if raw_match:
        owner, repo, rest = raw_match.group(1), raw_match.group(2), raw_match.group(3)
        parts = rest.split("/")

        if len(parts) >= 3 and parts[0] == "refs" and parts[1] == "heads":
            ref = "/".join(parts[:3])
            path = "/".join(parts[3:])
        else:
            if len(parts) < 2:
                return None, None, None, None
            ref = parts[0]
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


def make_description_url(mod_url: str):
    owner, repo, ref, mod_path = parse_mod_url(mod_url)
    if not owner or not repo or not ref or not mod_path:
        return None

    mod_folder = os.path.dirname(mod_path).strip("/")
    description_path = "description.md" if not mod_folder else f"{mod_folder}/description.md"

    encoded_path = urllib.parse.quote(description_path, safe="/")
    encoded_ref = urllib.parse.quote(ref, safe="")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{encoded_ref}/{encoded_path}"


for filename in glob.glob(os.path.join('.', '*.json')):
    if filename not in ignore:
        print(f"Opening: {filename}")
        filecontent = open(filename, "r", encoding="utf-8").read()
        modlist = json.loads(filecontent)

        items = (
            modlist.items()
            if 'availableMods' not in modlist
            else modlist["availableMods"].items()
        )

        for mod, data in items:
            mod_url = (data.get('mod') or '').replace(' ', '%20')
            description_url = make_description_url(mod_url)
            if not description_url:
                data.pop('descriptionURL', None)
                continue

            try:
                request = urllib.request.Request(description_url)
                response = urllib.request.urlopen(request, timeout=10)
      
                data['descriptionURL'] = description_url

            except Exception as e:
               data.pop('descriptionURL', None)

        resultcontent = json.dumps(
            modlist,
            indent='\t',
            separators=(',', ' : ')
        ) + "\n"

        if filecontent != resultcontent:
            open(filename, "w", encoding="utf-8").write(resultcontent)

sys.exit(os.EX_OK)
