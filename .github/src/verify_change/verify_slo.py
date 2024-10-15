import requests
from util import findDiff
import os
from verify_schema import verify_schema


def verify_slo(old_yaml, new_yaml, changes):
    any_error = False

    # verify k8s schema
    if not verify_schema(
        ".github/src/verify_change/crd_schemas/slodefinition.yaml", new_yaml
    ):
        print("ERROR: schema validation failed")
        any_error = True

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

    return any_error
