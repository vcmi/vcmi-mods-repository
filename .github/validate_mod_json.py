import json
import glob
import os
import sys
import urllib.request

ignore = [ "./github.json", "./vcmi-1.2.json" ]

error = False

for filename in glob.glob(os.path.join('.', '*.json')):
    if filename not in ignore:
        print(f"Opening: {filename}")
        filecontent = open(filename, "r").read()
        modlist = json.loads(filecontent)
        for mod, data in modlist.items():
            url = data["mod"]
            print(f"Download {mod}: {url}")
            try:
                response = urllib.request.urlopen(url)
            except:
                error = True
                print(f"Error: download failed!")
                continue
            filecontent = response.read()
            
            try:
                json.loads(filecontent)
            except Exception as err:
                error = True
                print("Error: " + err)
                continue
if error:
    sys.exit(os.EX_SOFTWARE)
else:
    print("Everything is ok!")
    sys.exit(os.EX_OK)