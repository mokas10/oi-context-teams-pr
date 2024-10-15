import requests
from util import findDiff
import os
from verify_schema import verify_schema


def check_name(name):
    if name is None:
        print("ERROR: display name can't be deleted")
        return True

    # check if new displayName is already in use in Grafana
    print("checking if name already in use")
    url = f"{os.getenv('GCP_BACKEND_URL')}/team/exists?product=context&name={name}"
    response = requests.get(
        url, headers={"Authorization": "Bearer " + os.getenv("GCP_ID_TOKEN")}
    )
    if response.status_code != 200:
        print(f"ERROR: failed to check if name already in use: {response.text}")
    else:
        if response.json()["onboarded"]:
            print(
                f"ERROR: display name {name} already in use in Grafana, needs to be unique"
            )
            return True
    return False


def verify_team(old_yaml, new_yaml, changes):
    any_error = False

    # verify k8s schema
    if not verify_schema(
        ".github/src/verify_change/crd_schemas/teamdefinition.yaml", new_yaml
    ):
        print("ERROR: schema validation failed")
        any_error = True
        return any_error

    # display name can't be deleted (can later be updated to verify it's a valid Grafana org name)
    if "spec.displayName" in changes:
        name = changes["spec.displayName"]
        any_error = check_name(name)

    if "spec.tokens" in changes:
        print("ERROR: tokens can't be changed")
        any_error = True

    # check changes within tenants
    if "spec.tenants" in changes:
        if "tenants" in old_yaml["spec"] and "tenants" in new_yaml["spec"]:
            if len(old_yaml["spec"]["tenants"]) != len(new_yaml["spec"]["tenants"]):
                print("ERROR: tenants can't be added or removed")
                any_error = True
            else:
                for i in range(len(old_yaml["spec"]["tenants"])):
                    old = old_yaml["spec"]["tenants"][i]
                    new = new_yaml["spec"]["tenants"][i]
                    # need to force an empty dict here, otherwise it will keep adding to the same dict
                    diffs = findDiff(old, new, changes={})
                    if "name" in diffs:
                        print("ERROR: tenant name can't be changed")
                        any_error = True
    return any_error
