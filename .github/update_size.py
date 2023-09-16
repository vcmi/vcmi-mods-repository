import json
import glob
import os
import urllib.request

ignore = [ "./github.json", "./vcmi-1.2.json", "./vcmi-1.3.json" ]

for filename in glob.glob(os.path.join('.', '*.json')):
    if filename not in ignore:
        print(f"Opening: {filename}")
        filecontent = open(filename, "r").read()
        modlist = json.loads(filecontent)
        for mod, data in modlist.items():
            url = data["download"]
            print(f"Download {mod}: {url}")
            response = urllib.request.urlopen(data["download"])
            filesize = len(response.read()) / 1024 / 1024
            print(f"Size: {filesize}")
            data["size"] = filesize
        resultcontent = json.dumps(modlist, indent='\t', separators=(',', ' : '))

        if filecontent != resultcontent:
            open(filename, "w").write(resultcontent)
