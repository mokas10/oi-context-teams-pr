# applies changes
# if displayName is changed - rename documents in Firestore
# if roles or locations are changed - update Firestore
# if tenants are changed - add as loki datasource in read_access teams
from firestore_funcs import (
    get_firestore_doc,
    update_firestore_field,
    get_firestore_doc_stream,
    set_firestore_field,
)
from google.cloud.firestore_v1.base_query import FieldFilter
from rename_team import rename_team
from create_firestore import create_team
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
    try:
        update_firestore_field(
            "GrafanaOrgs",
            id,
            key,
            data,
        )

    except Exception as e:
        print(f"ERROR updating GrafanaOrgs: {e}")
        sys.exit(1)

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
        update_firestore_field(
            "OITeams",
            id,
            "zzz_history",
            history,
        )
    except Exception as e:
        print(f"WARNING updating OITeams: {e}")


def update_tenants(tenant_info):
    for tenant in tenant_info:
        tenant_name = tenant["name"]
        # check if an org exists
        for team in tenant["read_access"]:
            team_info = get_firestore_doc_stream(
                "GrafanaOrgs", FieldFilter("resource_name", "==", team)
            )
            if not team_info or len(team_info) != 1:
                print(f"WARNING read_access: {team} doesn't exist or isn't unique")
                continue
            doc_id = list(team_info.keys())[0]
            if tenant_name not in team_info[doc_id]["tenants"]:
                update_all_firestore_fields(
                    doc_id, f"tenants.{tenant_name}", ["loki"], False
                )
                # set update to true for all operators
                print("setting update to true for all operators")
                data = {}
                for operator in team_info[doc_id]["grafana_orgs"]:
                    data[operator] = {"update": True}
                set_firestore_field("GrafanaOrgs", doc_id, "grafana_orgs", data)


def handle_changes(display_name, changes):
    if "spec.displayName" in changes:
        # check if new name doesn't exist as document
        exists = get_firestore_doc("GrafanaOrgs", changes["spec.displayName"])
        if exists:
            print("ERROR: new name already exists")
            sys.exit(1)

        # check if old name exists
        old_exists = get_firestore_doc("GrafanaOrgs", old_yaml["spec"]["displayName"])
        if not old_exists:
            print("WARNING: old name doesn't exist, creating in firestore")
            create_team(new_yaml)

        else:
            # if the old name exists, rename the existing documents in Firestore
            rename_team(
                old_yaml["spec"]["displayName"],
                changes["spec.displayName"],
                "GithubIntegration",
            )
        changes.pop("spec.displayName")

    exists = get_firestore_doc("GrafanaOrgs", display_name)
    if not exists:
        print("WARNING: document doesn't exist, creating")
        create_team(new_yaml)
        sys.exit(0)

    # handle updated roles
    if "spec.roles" in changes:
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

    # handle updated tenants
    if "spec.tenants" in changes:
        update_tenants(changes["spec.tenants"])


if __name__ == "__main__":
    old_file = sys.argv[1]
    new_file = sys.argv[2]
    with open(old_file, "r") as file:
        old_yaml = yaml.safe_load(file)
    with open(new_file, "r") as file:
        new_yaml = yaml.safe_load(file)
    changes = findDiff(old_yaml, new_yaml)

    print(f"update - found changes: {changes}")

    display_name = new_yaml["spec"]["displayName"]

    handle_changes(display_name, changes)
