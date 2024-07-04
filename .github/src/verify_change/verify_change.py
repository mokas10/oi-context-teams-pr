#!/usr/bin/env python
import sys
import yaml


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

print("all changes are permitted, continuing...")
