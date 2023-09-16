import json
import glob
import os
import sys
import urllib.request

from ignore_json import ignore

error = False

for filename in glob.glob(os.path.join('.', '*.json')):
    if filename not in ignore:
        print(f"Opening: {filename}")
        filecontent = open(filename, "r").read()

        try:
            json.loads(filecontent)
        except Exception as err:
            print("Error: " + str(err))
            sys.exit(os.EX_SOFTWARE)

print("Everything is ok!")
sys.exit(os.EX_OK)