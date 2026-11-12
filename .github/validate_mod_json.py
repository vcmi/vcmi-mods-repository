import jstyleson
import glob
import os
import sys
import urllib.parse
import urllib.request

import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT4

from ignore_json import ignore

SCHEMA_URL = "https://raw.githubusercontent.com/vcmi/vcmi/develop/config/schemas/mod.json"
# Mod lists for VCMI versions older than the schema, which they may not match
SCHEMA_IGNORE = ["./vcmi-1.7.json"]


def load_url(url):
    with urllib.request.urlopen(url.replace(" ", "%20")) as response:
        return response.read().decode("utf-8")


# mod.json schema references other schemas by path relative to it
def retrieve_schema(uri):
    return Resource.from_contents(jstyleson.loads(load_url(urllib.parse.urljoin(SCHEMA_URL, uri))), default_specification=DRAFT4)


# Schema is fetched from VCMI repository; if it is unavailable, mods are still checked for download and JSON errors
try:
    validator = jsonschema.Draft4Validator(jstyleson.loads(load_url(SCHEMA_URL)), registry=Registry(retrieve=retrieve_schema))
except Exception as err:
    validator = None
    print(f"::warning::Unable to load mod schema from {SCHEMA_URL}, schema validation skipped: {err}")

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
            # Plain string entry is URL to mod.json released by shared CI
            url = data if isinstance(data, str) else data["mod"]
            print(f"{mod}: {url}")

            try:
                filecontent = load_url(url)
                print(f"✅ Download successful")
            except Exception as err:
                error = True
                print(f"❌ Download failed: {err}")
                continue

            try:
                modjson = jstyleson.loads(filecontent)
                print(f"✅ JSON valid")
            except Exception as err:
                error = True
                print(f"❌ JSON invalid:")
                print(str(err))
                continue

            schema_errors = []
            if validator and filename not in SCHEMA_IGNORE:
                # referenced schemas are fetched lazily, a network error must not stop validation of remaining mods
                try:
                    schema_errors = list(validator.iter_errors(modjson))
                except Exception as err:
                    print(f"::warning::{mod}: schema validation skipped: {err}")
            for err in schema_errors:
                print(f"❌ Schema: {err.json_path}: {err.message}")
            if schema_errors:
                error = True
                continue

            # Plain string entry has no other fields, so mod.json must provide them
            if isinstance(data, str) and "download" not in modjson:
                error = True
                print(f"❌ No 'download' in mod.json, required for plain string entry")
                continue

            print(f"✅ Schema valid")

if error:
    sys.exit(os.EX_SOFTWARE)
else:
    print("Everything is ok!")
    sys.exit(os.EX_OK)
