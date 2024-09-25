from google.cloud import firestore
import os


def get_firestore_doc(collection, id):
    print(f"fetching document {id}")
    doc_dict = None
    try:
        db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
        doc_ref = db.collection(collection).document(id)
        doc = doc_ref.get()
        if doc.exists:
            doc_dict = doc.to_dict()
    except Exception as e:
        print(f"ERROR: {e}")

    return doc_dict


def get_firestore_doc_stream(collection, filter=None):
    print(f"fetching documents in {collection}")
    entries = {}
    try:
        db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
        doc_filter = db.collection(collection)
        if filter:
            doc_filter = doc_filter.where(filter=filter)
        doc_ref = doc_filter.stream()
        for doc in doc_ref:
            dict_doc = doc.to_dict()
            entries[doc.id] = dict_doc
    except Exception as e:
        print(f"ERROR: {e}")

    return entries


def data_transform(data):
    # transform data in a way that firestore can handle it correctly
    new_data = data
    # if it is an array (list in python) and not empty, use firestore ArrayUnion
    if isinstance(data, list) and data:
        new_data = firestore.ArrayUnion(data)
    elif isinstance(data, dict):
        for key in data:
            # recursion to check if any arrays in the dict
            transformed_data = data_transform(data[key])
            new_data[key] = transformed_data
    return new_data


def create_firestore_doc(collection, id, data):
    print(f"creating new document {id} in Firestore")
    firestore_data = data_transform(data)
    db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
    doc_ref = db.collection(collection).document(id)
    doc_ref.set(firestore_data, merge=True)
    print(f"created doc {id} in GrafanaOrgs")


def update_firestore_field(collection, id, field_name, field_data, array_merge=False):
    db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
    # spec holds the full current array, merge in case its wanted
    if array_merge:
        field_data = data_transform(field_data)
    org_ref = db.collection(collection).document(id)
    # handle non-alphanumeric characters in field_name
    if "." in field_name:
        # if an actual field path is given in dot notation, don't convert that part to firestore field path
        field_name_split = field_name.split(".")
        field_name = ""
        for x in field_name_split:
            field_name = field_name + db.field_path(x) + "."
        field_name = field_name.strip(".")
    else:
        field_name = db.field_path(field_name)
    data = {field_name: field_data}
    org_ref.update(data)


def set_firestore_field(collection, id, field_name, field_data):
    db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
    field_data = data_transform(field_data)
    org_ref = db.collection(collection).document(id)
    data = {field_name: field_data}
    org_ref.set(data, merge=True)
