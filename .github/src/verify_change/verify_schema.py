import yaml


def translate_schema(schema):
    if "properties" in schema:
        required_keys = schema.get("required", [])
        allow_unknown = schema.get("x-kubernetes-preserve-unknown-fields", False)
        ret_val = {
            (k + "*" if k in required_keys else k): translate_schema(v)
            for k, v in schema["properties"].items()
        }
        if allow_unknown:
            ret_val["-"] = "any"
        return ret_val
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
        for i in input or []:
            if not check_mandatory(i, schema[0]):
                return False
    return True


# check if input has extra keys
def check_extra(input, schema):
    if "-" in schema:
        return True

    if isinstance(input, dict):
        for key, value in input.items():
            schema_key = schema.get(key) or schema.get(f"{key}*")
            if not schema_key:
                print(f"ERROR: extra key {key} found")
                return False
            if not check_extra(value, schema_key):
                return False

    elif isinstance(input, list):
        for item in input:
            if not check_extra(item, schema[0]):
                return False

    return True


def get_count(input, required_values):
    total_counter_num = []
    # if input is a list, check all elements separetely
    if isinstance(input, list):
        for i in input:
            total_counter = 0
            for each in required_values:
                if each in i:
                    total_counter += 1
            total_counter_num.append(total_counter)
    # if input is a dict, check the whole dict
    elif isinstance(input, dict):
        total_counter = 0
        for each in required_values:
            if each in i:
                total_counter += 1
        total_counter_num.append(total_counter)
    return total_counter_num


def validate_conditions(input, schema, condition):
    required_values = [
        item["required"][0] for item in schema[condition] if "required" in item
    ]
    count = get_count(input, required_values)
    for total_counter in count:
        if condition == "allOf" and total_counter != len(required_values):
            print(f"ERROR: all of {required_values} have to be provided!")
            return False
        elif condition == "anyOf" and len(required_values) > 0 and total_counter == 0:
            print(f"ERROR: any of {required_values} have to be provided!")
            return False
        elif condition == "oneOf" and total_counter != 1:
            print(f"ERROR: exactly one of {required_values} has to be provided!")
            return False
    return True


def check_quantors(input, schema):
    if "type" not in schema:
        return True

    if schema["type"] == "object":
        for condition in [
            "allOf",
            "anyOf",
            "oneOf",
        ]:
            if condition in schema:
                return validate_conditions(
                    input,
                    schema,
                    condition,
                )

        if "properties" in schema:
            for key, value in schema["properties"].items():
                if key in input and not check_quantors(input[key], value):
                    return False

    elif schema["type"] == "array":
        return check_quantors(input, schema["items"])

    return True


def validate_input(input, schema, original_schema):
    validation_list = []
    # check mandatory values are set
    validation_list.append(check_mandatory(input, schema))

    # check if no extra keys are present
    validation_list.append(check_extra(input, schema))

    # check if quantors are met (allOf, anyOf, oneOf)
    validation_list.append(check_quantors(input, original_schema))

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
    input_valid = validate_input(specs_input, specs_schema, schema_specs)
    return input_valid
