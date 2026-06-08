import requests
from util import findDiff
import re
from verify_schema import verify_schema

# mandatory labels for v1 SLOs (Pyrra based)
mandatory_labels_v1 = [
    ["deployment.environment", "deployment.environment.name"],
    "ingka.legal_company",
    "ingka.system_name",
    "ingka.team",
    "ingka.version",
]

# mandatory labels for v2 (v2beta1) SLOs (Sloth based) as defined by the
# Observability Framework, see docs/public/slos-as-a-service.md
mandatory_labels_v2 = [
    "deployment.environment.name",
    "ingka.legal_company",
    "ingka.system_name",
    "ingka.system_id",
    "ingka.team",
    "ingka.version",
]

allow_grouping = [  # allow these labels to be grouping instead (v1 only)
    ["deployment.environment", "deployment.environment.name"],
]


def get_label_list(yaml_data, any_error):
    # get a list of labels, reporting any label that is missing a value
    spec = yaml_data.get("spec")
    if not isinstance(spec, dict):
        return [], any_error
    cur_labels = spec.get("labels", [])
    if not isinstance(cur_labels, list):
        print("ERROR: spec.labels must be a list")
        return [], True
    label_list = []
    for i, each_label in enumerate(cur_labels):
        if not isinstance(each_label, dict):
            print(f"ERROR: spec.labels[{i}] must be a mapping, got {type(each_label).__name__}")
            any_error = True
            continue
        if "name" not in each_label:
            print(f"ERROR: spec.labels[{i}] is missing required 'name' field")
            any_error = True
            continue
        if "value" not in each_label or not each_label["value"]:
            print(f"ERROR: label {each_label['name']} is missing value")
            any_error = True
            continue
        label_list.append(each_label["name"])
    return label_list, any_error


def check_mandatory_labels(yaml_data, any_error):
    # v1: labels may be provided directly or as grouping on the indicator
    label_list, any_error = get_label_list(yaml_data, any_error)

    # get a list of grouping labels
    grouping_labels = []
    spec = yaml_data.get("spec") or {}
    indicator = spec.get("indicator")
    if not isinstance(indicator, dict) or not indicator:
        if indicator is not None:
            print("ERROR: spec.indicator must be a non-empty mapping")
            any_error = True
        # Cannot extract grouping labels without a valid indicator; skip grouping check
    else:
        field_name = next(iter(indicator))
        indicator_value = indicator[field_name]
        grouping_list = indicator_value.get("grouping", []) if isinstance(indicator_value, dict) else []
        for each_label in grouping_list:
            grouping_labels.append(each_label.replace(".", "_"))

    # check if all mandatory labels are present
    for label in mandatory_labels_v1:
        if type(label) is list:
            if not any(
                key in label_list or key.replace(".", "_") in grouping_labels
                for key in label
            ):
                print(f"ERROR: one of the labels {label} is missing")
                any_error = True
        elif label not in label_list:
            if (
                label not in allow_grouping
                or label.replace(".", "_") not in grouping_labels
            ):
                print(f"ERROR: label {label} is missing")
                any_error = True

    return any_error


def check_mandatory_labels_v2(yaml_data, any_error):
    # v2: grouping does not exist, all mandatory labels must be set under spec.labels
    label_list, any_error = get_label_list(yaml_data, any_error)

    for label in mandatory_labels_v2:
        if label not in label_list:
            print(f"ERROR: label {label} is missing")
            any_error = True

    return any_error


def get_slo_version(yaml_data):
    # determine resource version from apiVersion (e.g. "context.ingka.com/v2beta1")
    api_version = yaml_data.get("apiVersion", "")
    return api_version.split("/")[1] if "/" in api_version else ""


def check_required_fields_v1(yaml_data, any_error):
    """Check that all required top-level spec fields are present in a v1 SLO.

    The CRD schema lists indicator/target/window/location as required, but the
    schema validator alone may not catch their absence for newly added files
    (x-kubernetes-preserve-unknown-fields is set on spec).  This function
    performs an explicit existence and basic value check so that a new v1 SLO
    cannot slip through without these fields.
    """
    spec = yaml_data.get("spec") or {}
    required = ["location", "window", "target", "indicator"]
    for field in required:
        if not spec.get(field):
            print(f"ERROR: spec.{field} is required for v1 SLOs")
            any_error = True

    # Validate target value when the field is present
    target = spec.get("target")
    if target is not None:
        if not isinstance(target, str):
            print("ERROR: spec.target must be a string")
            any_error = True
        else:
            try:
                val = float(target)
                if val < 0 or val > 100:
                    print("ERROR: spec.target must be a number between 0 and 100")
                    any_error = True
            except ValueError:
                print("ERROR: spec.target must be a numeric string")
                any_error = True

    return any_error


def check_mandatory_labels_for_version(yaml_data, any_error):
    # dispatch to the correct mandatory label check based on the SLO version
    if get_slo_version(yaml_data) == "v2beta1":
        return check_mandatory_labels_v2(yaml_data, any_error)
    return check_mandatory_labels(yaml_data, any_error)


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

    # determine resource version from apiVersion (e.g. "context.ingka.com/v2beta1")
    api_version = new_yaml.get("apiVersion", "")
    version = get_slo_version(new_yaml)

    # verify k8s schema (the schema file holds both v1 and v2beta1 definitions,
    # the matching one is selected based on apiVersion)
    if not verify_schema(
        ".github/src/verify_change/crd_schemas/slodefinition.yaml", new_yaml
    ):
        print("ERROR: schema validation failed")
        any_error = True

    # check if resource name is prefixed by team name
    team_name = file_path.split("/")[1]
    any_error = check_resource_name(team_name, new_yaml, any_error)

    if version == "v1":
        any_error = verify_slo_v1(team_name, new_yaml, changes, any_error)
    elif version == "v2beta1":
        any_error = verify_slo_v2(team_name, new_yaml, changes, any_error)
    else:
        print(f"ERROR: unsupported SLO apiVersion '{api_version}'")
        any_error = True

    return any_error


def verify_slo_v1(team_name, new_yaml, changes, any_error):
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
    # Re-validate mandatory labels whenever labels *or* indicator grouping changes,
    # because mandatory labels can be satisfied by either spec.labels or
    # spec.indicator.<type>.grouping – a change to either can break compliance.
    indicator_changed = any(k.startswith("spec.indicator") for k in changes)
    if "spec.labels" in changes or indicator_changed:
        any_error = check_mandatory_labels(new_yaml, any_error)

    return any_error


def verify_slo_v2(team_name, new_yaml, changes, any_error):
    spec = new_yaml.get("spec")
    if not isinstance(spec, dict):
        print("ERROR: spec must be a mapping")
        return True
    spec = spec or {}

    # spec.owner is required for v2beta1 and must match the team (folder) name;
    # it is used to resolve the Grafana org and is part of the resource naming convention
    owner = spec.get("owner")
    if owner is None:
        print("ERROR: spec.owner is required for v2beta1 SLOs")
        any_error = True
    elif owner != team_name:
        print(
            f"ERROR: spec.owner '{owner}' must match the team name '{team_name}'"
        )
        any_error = True

    # Always validate spec.objective from the resulting spec, not only the diff,
    # because findDiff() only iterates keys from the old YAML and newly added
    # keys will not appear in changes.
    objective = spec.get("objective")
    if objective is None:
        print("ERROR: spec.objective is required for v2beta1 SLOs")
        any_error = True
    elif isinstance(objective, bool) or not isinstance(objective, (int, float)):
        print("ERROR: objective must be a number")
        any_error = True
    elif objective <= 0 or objective > 100:
        print("ERROR: objective must be a number greater than 0 and at most 100")
        any_error = True

    # Always validate mandatory labels from the resulting spec, not only the diff,
    # because findDiff() only iterates keys from the old YAML and a newly added
    # spec.labels section would be invisible to the diff.
    any_error = check_mandatory_labels_v2(new_yaml, any_error)

    return any_error


