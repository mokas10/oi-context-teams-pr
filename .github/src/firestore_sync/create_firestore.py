# creates new files in the GrafanaOrgs collection in Firestore
# OITeams collection is updated through the onboarding flow

from firestore_funcs import create_firestore_doc, get_firestore_doc
import datetime
import sys
import yaml


def format_yaml(unformatted_yaml):
    spec_info = unformatted_yaml["spec"]

    formatted_yaml = {}
    formatted_yaml["name"] = spec_info["displayName"]
    formatted_yaml["status"] = "active"
    formatted_yaml["create_time"] = datetime.datetime.now()
    formatted_yaml["resource_name"] = unformatted_yaml["metadata"]["name"]

    formatted_yaml["grafana_orgs"] = {}
    formatted_yaml["locations"] = spec_info.get(
        "locations", ["gcp-eu"]
    )  # get locations, default to gcp-eu

    formatted_yaml["roles"] = {}
    for each_role in spec_info["roles"]:
        if "groups" in each_role and each_role["groups"]:
            formatted_yaml["roles"][each_role["name"]] = each_role["groups"]
        else:
            formatted_yaml["roles"][each_role["name"]] = []

    formatted_yaml["tenants"] = {}
    if "tenants" in spec_info:
        for each_tenant in spec_info["tenants"]:
            formatted_yaml["tenants"][each_tenant["name"]] = ["loki"]
    formatted_yaml["tenants"]["public"] = ["mimir", "tempo"]
    return formatted_yaml


# since the entry in OITeams is made by the onboarding workflow
# - this only needs to create GrafanaOrgs entry
def create_team(team_yaml):
    try:
        formatted_yaml = format_yaml(team_yaml)
    except Exception as e:
        print(f"ERROR formatting yaml: {e}")
        return
    try:
        team_name = team_yaml["spec"]["displayName"]
        create_firestore_doc("GrafanaOrgs", team_name, formatted_yaml)
    except Exception as e:
        print(f"ERROR creating document: {e}")
        return


if __name__ == "__main__":
    new_file = sys.argv[1]
    with open(new_file, "r") as file:
        try:
            new_file_data = yaml.safe_load(file)
            print("read data")
        except Exception as e:
            print(f"ERROR: failed to parse yaml file: {e}")
            sys.exit(1)
    # check if it is a team file
    if new_file_data["kind"] != "Team":
        print("INFO: not a team file, no firestore creation needed")
        sys.exit(0)

    exists = get_firestore_doc("GrafanaOrgs", new_file_data["spec"]["displayName"])
    if exists:
        print("WARNING: new name already exists, skipping creation")
        sys.exit(0)
    create_team(new_file_data)
