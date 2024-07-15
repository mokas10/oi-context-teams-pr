#!/usr/bin/env python
import sys
import yaml
import os
import requests


GCP_ID_TOKEN = os.getenv("GCP_ID_TOKEN")
GCP_BACKEND_URL = os.getenv("GCP_BACKEND_URL")


def findDiff(d1, d2, path="", changes={}):
    for k in d1:
        try:
            if k in d2:
                if type(d1[k]) is dict:
                    findDiff(
                        d1[k], d2[k], "%s -> %s" % (path, k) if path else k, changes
                    )
                if d1[k] != d2[k] and path:
                    changes[f"{path}.{k}"] = d2[k]
            else:
                changes[f"{path}.{k}"] = None
        except Exception:
            changes[f"{path}.{k}"] = None
    return changes


old_file = sys.argv[1]
new_file = sys.argv[2]

with open(old_file, "r") as file:
    old_yaml = yaml.safe_load(file)

with open(new_file, "r") as file:
    new_yaml = yaml.safe_load(file)

# find changes - are returned in the format
# {'metadata.name': None, 'spec.displayName': 'New Display Name', 'spec.locations': ['gcp-eu', 'alicloud-eu']}
changes = findDiff(old_yaml, new_yaml)
print(f" found changes: {changes}")

### validate if changes are permitted
# TODO: add more validation rules

# resource name can't be changed
if "metadata.name" in changes:
    print("ERROR: resource name can't be changed")
    sys.exit(1)

# display name can't be deleted (can later be updated to verify it's a valid Grafana org name)
if "spec.displayName" in changes and changes["spec.displayName"] is None:
    print("ERROR: display name can't be deleted")
    sys.exit(1)

# check if new displayName is already in use in Grafana
if "spec.displayName" in changes:
    print("checking if name already in use")
    url = f"{GCP_BACKEND_URL}/team/exists?product=context&name={changes['spec.displayName']}"
    response = requests.get(url, headers={"Authorization": "Bearer " + GCP_ID_TOKEN})
    if response.status_code != 200:
        print(f"ERROR: failed to check if name already in use: {response.text}")
    else:
        if response.json()["onboarded"]:
            print(
                f"ERROR: display name {changes['spec.displayName']} already in use in Grafana, needs to be unique"
            )
            sys.exit(1)

print("all changes are permitted, continuing...")
