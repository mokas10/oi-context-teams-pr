# applies changes
# if displayName is changed - rename documents in Firestore
# if roles or locations are changed - update Firestore
# if tenants are changed - add as loki datasource in read_access teams
from firestore_funcs import (
    get_firestore_doc,
    update_firestore_field,
)
from rename_team import rename_team
import sys
import yaml
import datetime


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


def update_all_firestore_fields(id, key, data, update_oiteams=True):
    if not update_oiteams:
        return

    try:
        update_firestore_field(
            "OITeams",
            id,
            f"products.context.{key}",
            data,
        )
        history = [
            {
                "type": "update",
                "action": f"updating field {key} to {data}",
                "timestamp": datetime.datetime.now(),
                "requester": "GithubIntegration",
            }
        ]
        update_firestore_field("OITeams", id, "zzz_history", history, True)
    except Exception as e:
        print(f"WARNING updating OITeams: {e}")


def handle_changes(display_name, changes):
    if "spec.displayName" in changes:
        # rename the team in OITeams Firestore
        rename_team(
            old_yaml["spec"]["displayName"],
            changes["spec.displayName"],
            "GithubIntegration",
        )
        changes.pop("spec.displayName")

    # handle updated roles
    if "spec.roles" in changes and changes["spec.roles"]:
        # get correct format
        roles_dict = {}
        for role in changes["spec.roles"]:
            roles_dict[role["name"]] = role.get("groups", [""])
        # update the role
        update_all_firestore_fields(
            display_name,
            "roles",
            roles_dict,
        )

    # handle updated locations
    if "spec.locations" in changes:
        update_all_firestore_fields(
            display_name,
            "locations",
            changes["spec.locations"],
        )


if __name__ == "__main__":
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
    # check if these are team files
    if old_yaml["kind"] != "Team" or new_yaml["kind"] != "Team":
        print("INFO: not a team file, no firestory update needed")
        sys.exit(0)

    changes = findDiff(old_yaml, new_yaml)

    print(f"update - found changes: {changes}")

    display_name = new_yaml["spec"]["displayName"]

    handle_changes(display_name, changes)
