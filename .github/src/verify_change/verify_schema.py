import yaml
from typing import Any

Schema = dict[str, Any]
InputData = dict[str, Any] | list[Any]


def translate_schema(schema: Schema) -> dict[str, Any] | list[Any] | str | None:
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
    if "additionalProperties" in schema:
        # Handle additionalProperties - allows any keys with specified value type
        return {"-": translate_schema(schema["additionalProperties"])}
    if "items" in schema:
        return [translate_schema(schema["items"])]
    if "type" in schema:
        return schema["type"]
    return None


# need to recursively check the schema
def check_mandatory(input_data: InputData, schema: dict[str, Any] | list[Any]) -> bool:
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key.endswith("*") and key[:-1] not in input_data:
                print(f"ERROR: mandatory key {key[:-1]} is missing")
                return False
            elif not key.endswith("*") and key not in input_data:
                continue
            new_key = key
            if key.endswith("*"):
                new_key = key[:-1]
            if not check_mandatory(input_data[new_key], value):
                return False
    elif isinstance(schema, list):
        for i in input_data or []:
            if not check_mandatory(i, schema[0]):
                return False
    return True


# check if input has extra keys
def check_extra(input_data: InputData, schema: dict[str, Any] | list[Any]) -> bool:
    if "-" in schema:
        return True

    if isinstance(input_data, dict):
        for key, value in input_data.items():
            schema_key = schema.get(key) or schema.get(f"{key}*")
            if not schema_key:
                print(f"ERROR: extra key {key} found")
                return False
            if not check_extra(value, schema_key):
                return False

    elif isinstance(input_data, list):
        for item in input_data:
            if not check_extra(item, schema[0]):
                return False

    return True


def get_count(input_data: InputData, required_values: list[str]) -> list[int]:
    total_counter_num = []
    # if input is a list, check all elements separately
    if isinstance(input_data, list):
        for i in input_data:
            total_counter = 0
            for each in required_values:
                if each in i:
                    total_counter += 1
            total_counter_num.append(total_counter)
    # if input is a dict, check the whole dict
    elif isinstance(input_data, dict):
        total_counter = 0
        for each in required_values:
            if each in input_data:
                total_counter += 1
        total_counter_num.append(total_counter)
    return total_counter_num


def validate_conditions(input_data: InputData, schema: Schema, condition: str) -> bool:
    required_values = [
        item["required"][0] for item in schema[condition] if "required" in item
    ]
    count = get_count(input_data, required_values)
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


def verify_object(input_data: dict[str, Any], schema: Schema) -> bool:
    if schema["type"] == "object":
        for condition in [
            "allOf",
            "anyOf",
            "oneOf",
        ]:
            if condition in schema:
                return validate_conditions(
                    input_data,
                    schema,
                    condition,
                )

        if "properties" in schema:
            for key, value in schema["properties"].items():
                if key in input_data and not check_quantors(input_data[key], value):
                    return False
    return True


def check_quantors(input_data: Any, schema: Schema) -> bool:
    if input_data is None or "type" not in schema:
        return True

    success = verify_object(input_data, schema)
    if not success:
        return False

    elif schema["type"] == "array":
        all_items = []
        for item in input_data:
            if not check_quantors(item, schema["items"]):
                return False
            all_items.append(item)
        if False in all_items:
            return False

    elif schema["type"] == "string":
        if not isinstance(input_data, str):
            print(
                f"ERROR: expected type string but got {type(input_data).__name__} for value {input_data}"
            )
            return False
    return True


def validate_input(input_data: dict[str, Any], schema: dict[str, Any], original_schema: Schema) -> bool:
    validation_list = []
    # check mandatory values are set
    validation_list.append(check_mandatory(input_data, schema))

    # check if no extra keys are present
    validation_list.append(check_extra(input_data, schema))

    # check if quantors are met (allOf, anyOf, oneOf)
    validation_list.append(check_quantors(input_data, original_schema))

    # TODO: check if input is valid (correct type, if int is within range, string regex, etc)

    return False not in validation_list


def verify_schema(definition: str, input_file: dict[str, Any]) -> bool:
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
