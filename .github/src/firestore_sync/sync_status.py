from firestore_funcs import get_firestore_doc, update_firestore_field
import sys
import datetime


action = sys.argv[1]


if action == "get_last_sha":
    doc_info = get_firestore_doc("SyncStatus", "oi-context-teams")
    if doc_info:
        print(doc_info["last_sha"])

elif action == "update_last_sha":
    new_sha = sys.argv[2]
    update_firestore_field("SyncStatus", "oi-context-teams", "last_sha", new_sha)
    update_firestore_field(
        "SyncStatus", "oi-context-teams", "timestamp", datetime.now()
    )
