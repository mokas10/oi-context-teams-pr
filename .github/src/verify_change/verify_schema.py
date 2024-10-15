import yaml


def translate_schema(schema):
    if "properties" in schema:
        required_keys = schema.get("required", [])
        return {
            (k + "*" if k in required_keys else k): translate_schema(v)
            for k, v in schema["properties"].items()
        }
    if "items" in schema:
        return [translate_schema(schema["items"])]
    if "type" in schema:
        return schema["type"]
    return None


# need to recursively check the schema
def check_mandatory(input, schema):
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key.endswith("*") and key[:-1] not in input:
                print(f"ERROR: mandatory key {key[:-1]} is missing")
                return False
            elif not key.endswith("*") and key not in input:
                continue
            new_key = key
            if key.endswith("*"):
                new_key = key[:-1]
            if not check_mandatory(input[new_key], value):
                return False
    elif isinstance(schema, list):
        for i in input:
            if not check_mandatory(i, schema[0]):
                return False
    return True


# check if input has extra keys
def check_extra(input, schema):
    if isinstance(input, dict):
        for key, value in input.items():
            if key not in schema and f"{key}*" not in schema:
                print(f"ERROR: extra key {key} found")
                return False
            if key in schema:
                if not check_extra(value, schema[key]):
                    return False
            elif f"{key}*" in schema:
                if not check_extra(value, schema[f"{key}*"]):
                    return False
    return True


def validate_input(input, schema):
    validation_list = []
    # check mandatory values are set
    validation_list.append(check_mandatory(input, schema))

    # check if no extra keys are present
    validation_list.append(check_extra(input, schema))

    # TODO: check if input is valid (correct type, if int is within range, string regex, etc)

    return False not in validation_list


def verify_schema(definition, input_file):
    with open(definition, "r") as file:
        slo_definition = yaml.safe_load(file)

    version = input_file["apiVersion"].split("/")[1]

    version_def = None

    for eachVersion in slo_definition["spec"]["versions"]:
        if eachVersion["name"] == version:
            version_def = eachVersion
            break

    if not version_def:
        print(f"ERROR: unknown schema version {version}")
        return False

    # openAPIV3Schema is the schema for validating custom objects
    schema = version_def["schema"]["openAPIV3Schema"]

    # validate the spec input
    schema_specs = schema["properties"]["spec"]

    # translate the schema into a parsable format
    specs_schema = translate_schema(schema_specs)

    # compare the input to the schema
    specs_input = input_file["spec"]

    # validate the input
    input_valid = validate_input(specs_input, specs_schema)
    return input_valid
