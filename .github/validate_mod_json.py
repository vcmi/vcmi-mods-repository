import jstyleson
import glob
import os
import sys
import urllib.request
from io import StringIO

from ignore_json import ignore

error = False

for filename in glob.glob(os.path.join('.', '*.json')):
    if filename not in ignore:
        print(f"Opening: {filename}")

        with open(filename, "r") as file:
            filecontent = file.read()

        try:
            modlist = jstyleson.loads(filecontent)
        except Exception as err:
            error = True
            print(f"❌ Error reading JSON file {filename}: {err}")
            continue

        for mod, data in modlist.items() if 'availableMods' not in modlist else modlist["availableMods"].items():
            url = data["mod"].replace(" ", "%20")
            print(f"{mod}: {url}")

            try:
                response = urllib.request.urlopen(url)
                print(f"✅ Download successful")
            except Exception as err:
                error = True
                print(f"❌ Download failed: {err}")
                continue

            try:
                filecontent = response.read().decode("utf-8")
                jstyleson.load(StringIO(filecontent))
                print(f"✅ JSON valid")
            except Exception as err:
                error = True
                print(f"❌ JSON invalid:")
                print(str(err))
                continue

if error:
    sys.exit(os.EX_SOFTWARE)
else:
    print("Everything is ok!")
    sys.exit(os.EX_OK)
