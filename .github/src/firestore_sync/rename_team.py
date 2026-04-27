# script to rename a team in firestore
from google.cloud import firestore
from datetime import datetime


def rename_team(old_name, new_name, requester):

    db = firestore.Client()

    # Merge OITeams entry
    old_doc_ref = db.collection("OITeams").document(old_name)
    doc = old_doc_ref.get()
    if not doc.exists:
        print(f"No such document {old_name} in OITeams!")
    else:
        dict_doc = doc.to_dict()
        if "context" not in dict_doc["products"]:
            print(f"Product context not found in {old_name} in OITeams!")
        else:
            dict_doc["team"] = new_name
            history_dict = {
                "action": f"renamed from {old_name} to {new_name} for context",
                "timestamp": datetime.now(),
                "type": "update",
                "requester": requester,
            }
            dict_doc["zzz_history"].append(history_dict)
            new_doc_ref = db.collection("OITeams").document(new_name)
            new_doc_ref.set(dict_doc, merge=True)
            print(f"updated doc {new_name} in OITeams")

            # remove old entry
            if "splunk" not in dict_doc["products"]:
                old_doc_ref.delete()
                print(f"deleted old doc {old_name} in OITeams")
            else:
                old_doc_ref.update({"products.context": firestore.DELETE_FIELD})
                print(f"removed context from old doc {old_name} in OITeams")

    # Update OITenants entries
    doc_stream = (
        db.collection("OITenants")
        .where("owner", "==", old_name)
        .where("product", "==", "context")
        .stream()
    )
    for doc in doc_stream:
        dict_doc = doc.to_dict()
        dict_doc["owner"] = new_name
        dict_doc["access"]["full"].append(new_name)
        history_dict = {
            "action": f"renamed owner team from {old_name} to {new_name}",
            "timestamp": datetime.now(),
            "type": "update",
            "requester": requester,
        }
        dict_doc["zzz_history"].append(history_dict)
        doc_ref = db.collection("OITenants").document(doc.id)
        doc_ref.set(dict_doc, merge=True)
        print(f"updated doc {doc.id} with new owner {new_name}")

    # Update OITokens entries
    doc_stream = (
        db.collection("OITokens")
        .where("team", "==", old_name)
        .where("product", "==", "context")
        .stream()
    )
    for doc in doc_stream:
        dict_doc = doc.to_dict()
        dict_doc["team"] = new_name
        history_dict = {
            "action": f"renamed owner from {old_name} to {new_name}",
            "timestamp": datetime.now(),
            "type": "update",
            "requester": requester,
        }
        dict_doc["zzz_history"].append(history_dict)
        doc_ref = db.collection("OITokens").document(doc.id)
        doc_ref.set(dict_doc, merge=True)
        print(f"updated doc {doc.id} with new owner {new_name}")

    # Update Tokens entries
    doc_stream = db.collection("Tokens").stream()
    for doc in doc_stream:
        if doc.id.split("_")[2] == old_name:
            dict_doc = doc.to_dict()
            dict_doc["additional_info"] = (
                f"renamed team from {old_name} to {new_name} on {datetime.now()}"
            )
            doc_ref = db.collection("Tokens").document(doc.id)
            doc_ref.set(dict_doc, merge=True)
            print(f"updated doc {doc.id} with new owner {new_name}")
