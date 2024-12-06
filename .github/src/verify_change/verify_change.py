#!/usr/bin/env python
import sys
import yaml
from verify_team import verify_team
from verify_slo import verify_slo
from util import findDiff


old_file = sys.argv[1]
new_file = sys.argv[2]

with open(old_file, "r") as file:
    try:
        old_yaml = yaml.safe_load(file)
    except Exception as e:
        print(f"ERROR: failed to parse old yaml file: {e}")
        sys.exit(1)

with open(new_file, "r") as file:
    try:
        new_yaml = yaml.safe_load(file)
    except Exception as e:
        print(f"ERROR: failed to parse new yaml file: {e}")
        sys.exit(1)

# find changes - are returned in the format
# {'metadata.name': None, 'spec.displayName': 'New Display Name', 'spec.locations': ['gcp-eu', 'alicloud-eu']}
changes = findDiff(old_yaml, new_yaml)
print(f" found changes: {changes}")

### validate if changes are permitted
# TODO: add more validation rules

any_error = False

# resource type can't be changed

if "kind" in changes:
    print("ERROR: resource type can't be changed")
    sys.exit(1)

# resource name can't be changed
if "metadata.name" in changes:
    print("ERROR: resource name can't be changed")
    any_error = True

# check if it is a team or slo resource
kind = new_yaml["kind"]

# changes in team file
if kind == "Team":
    any_error = verify_team(old_yaml, new_yaml, changes)

elif kind == "SLO":
    file_path = new_file
    any_error = verify_slo(file_path, old_yaml, new_yaml, changes)

if any_error:
    print("ERROR: found errors in changes, exiting...")
    sys.exit(1)

print("all changes are permitted, continuing...")
