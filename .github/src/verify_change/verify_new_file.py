import sys
import yaml
import os
from verify_schema import verify_schema

max_per_kind = {"Team": 1, "SLO": 5}


def count_files(folder, count_per_kind={}):
    for file in os.listdir(folder):
        if file.endswith(".yaml"):
            with open(f"{folder}/{file}", "r") as f:
                yaml_data = yaml.safe_load(f)
            kind = yaml_data["kind"]
            if kind not in count_per_kind:
                count_per_kind[kind] = 1
            else:
                count_per_kind[kind] += 1
        # if it is a folder, check inside
        elif os.path.isdir(f"{folder}/{file}"):
            count_per_kind.update(count_files(f"{folder}/{file}", count_per_kind))
    return count_per_kind


file_list = sys.argv[1].split(",")

any_error = False
main_folders = []

for file in file_list:
    print("checking file: ", file)
    # if file doesn't end in .yaml, skip
    if not file.endswith(".yaml"):
        continue
    # read file
    try:
        with open(file, "r") as f:
            yaml_data = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: failed to parse yaml file: {e}")
        sys.exit(1)

    # check if it is a team or slo resource
    kind = yaml_data["kind"]

    # check schema
    if kind == "Team":
        if not verify_schema(
            ".github/src/verify_change/crd_schemas/teamdefinition.yaml", yaml_data
        ):
            print("ERROR: schema validation failed")
            any_error = True
    elif kind == "SLO":
        if not verify_schema(
            ".github/src/verify_change/crd_schemas/slodefinition.yaml", yaml_data
        ):
            print("ERROR: schema validation failed")
            any_error = True
    else:
        print(f"ERROR: unknown kind '{kind}'")
        sys.exit(1)
    print("schema validation passed")

    # get the first two folders, as under team can be subfolders
    folder_path = "/".join(file.split("/")[:2])
    if folder_path not in main_folders:
        main_folders.append(folder_path)

# check if max count is exceeded
for folder in main_folders:
    print(f"checking folder: {folder} for max count")
    count_per_kind = count_files(folder)
    for kind in max_per_kind:
        if kind not in count_per_kind:
            continue
        if count_per_kind[kind] > max_per_kind[kind]:
            print(
                f"ERROR: too many {kind}s, allowed: {max_per_kind[kind]}, found: {count_per_kind[kind]}"
            )
            any_error = True

if any_error:
    sys.exit(1)
