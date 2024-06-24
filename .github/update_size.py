import json
import glob
import os
import sys
import urllib.request

from ignore_json import ignore

for filename in glob.glob(os.path.join('.', '*.json')):
    if filename not in ignore:
        print(f"Opening: {filename}")
        filecontent = open(filename, "r").read()
        modlist = json.loads(filecontent)
        for mod, data in modlist.items():
            url = data["download"].replace(" ", "%20")
            print(f"Download {mod}: {url}")
            try:
                response = urllib.request.urlopen(url)
            except:
                print("Error: download failed!")
                sys.exit(os.EX_SOFTWARE)
            filesize = round(len(response.read()) / 1024 / 1024, 3)
            print(f"Size: {filesize}")
            data["downloadSize"] = filesize

        resultcontent = json.dumps(modlist, indent='\t', separators=(',', ' : ')) + "\n"

        if filecontent != resultcontent:
            open(filename, "w").write(resultcontent)

sys.exit(os.EX_OK)
