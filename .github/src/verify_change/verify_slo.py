import requests
from util import findDiff
import re
from verify_schema import verify_schema

mandatory_labels = [
    ["deployment.environment", "deployment.environment.name"],
    "ingka.legal_company",
    "ingka.system_name",
    "ingka.team",
    "ingka.version",
]


def check_mandatory_labels(yaml_data, any_error):
    cur_labels = yaml_data["spec"]["labels"]
    # get a list of labels
    label_list = []
    for each_label in cur_labels:
        if "value" not in each_label or not each_label["value"]:
            print(f"ERROR: label {each_label['name']} is missing value")
            any_error = True
            continue
        label_list.append(each_label["name"])

    # check if all mandatory labels are present
    for label in mandatory_labels:
        if type(label) is list:
            if not any(key in label_list for key in label):
                print(f"ERROR: one of the labels {label} is missing")
                any_error = True
        elif label not in label_list:
            print(f"ERROR: label {label} is missing")
            any_error = True
    return any_error


def check_resource_name(team_name, yaml_data, any_error):
    # check if resource name is prefixed by team name
    resource_name = yaml_data["metadata"]["name"]
    if not resource_name.startswith(team_name):
        print(f"ERROR: resource name must be prefixed by team name '{team_name}'")
        any_error = True

    # check if resource name fulfill the naming convention
    if not re.match(r"^[a-z0-9][-a-z0-9]*$", resource_name):
        print("ERROR: resource name must be lowercase alphanumeric and '-'")
        any_error = True

    # check if max length of resource name is 63
    if len(resource_name) > 63:
        print("ERROR: resource name must be less than 63 characters")
        any_error = True

    return any_error


def verify_slo(file_path, old_yaml, new_yaml, changes):
    any_error = False

    # verify k8s schema
    if not verify_schema(
        ".github/src/verify_change/crd_schemas/slodefinition.yaml", new_yaml
    ):
        print("ERROR: schema validation failed")
        any_error = True

    # check if resource name is prefixed by team name
    team_name = file_path.split("/")[1]
    any_error = check_resource_name(team_name, new_yaml, any_error)

    # check if target is a string and a number
    if "spec.target" in changes:
        target = changes["spec.target"]
        if not isinstance(target, str):
            print("ERROR: target must be a string")
            any_error = True
        else:
            try:
                val = float(target)
                if val < 0 or val > 100:
                    print("ERROR: target must be a number between 0 and 100")
                    any_error = True
            except ValueError:
                print("ERROR: target must be a number")
                any_error = True
    if "spec.labels" in changes:
        any_error = check_mandatory_labels(new_yaml, any_error)

    return any_error
