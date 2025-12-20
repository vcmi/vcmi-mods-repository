import json
import glob
import os
import sys
import urllib.request
import re

from ignore_json import ignore

GITHUB_API = "https://api.github.com/repos/{owner}/{repo}"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def extract_github_repo(url):
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return None, None
    return match.group(1), match.group(2)

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
            url = data.get("download", "")
            owner, repo = extract_github_repo(url)

            if not owner or not repo:
                print(f"Skipping {mod}: not a GitHub URL")
                continue

            api_url = GITHUB_API.format(owner=owner, repo=repo)
            print(f"Fetching stars for {mod}: {owner}/{repo}")

            headers = {"User-Agent": "github-stars-script"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

            try:
                request = urllib.request.Request(api_url, headers=headers)
                response = urllib.request.urlopen(request, timeout=10)
                repo_data = json.loads(response.read().decode("utf-8"))
                stars = repo_data.get("stargazers_count")
                if stars is not None:
                    data["githubStars"] = stars
                    print(f"Stars updated: {stars}")
                else:
                    print("No stars field in response, keeping old value")

            except Exception as e:
                existing = data.get("githubStars")
                if existing is not None:
                    print(f"Error ({e}), keeping existing stars: {existing}")
                else:
                    print(f"Error ({e}), no existing stars to keep")

        resultcontent = json.dumps(
            modlist,
            indent='\t',
            separators=(',', ' : ')
        ) + "\n"

        if filecontent != resultcontent:
            open(filename, "w", encoding="utf-8").write(resultcontent)

sys.exit(os.EX_OK)
