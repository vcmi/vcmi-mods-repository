import json
import glob
import os
import sys
import urllib.request
import re

from ignore_json import ignore

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
            description_url = data['mod'].replace('mod.json', 'description.md')

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
