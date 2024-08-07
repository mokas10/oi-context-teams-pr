from firestore_funcs import get_firestore_doc, update_firestore_field
import sys
import os
from datetime import datetime


action = sys.argv[1]


if action == "get_last_sha":
    doc_info = get_firestore_doc("SyncStatus", "oi-context-teams")
    if doc_info:
        print(f'last sha: {doc_info["last_sha"]}')
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            print(f'last_sha={doc_info["last_sha"]}', file=fh)

elif action == "update_last_sha":
    new_sha = sys.argv[2]
    timestamp = datetime.now()
    print(f"updating sync status to sha {new_sha}")
    update_firestore_field("SyncStatus", "oi-context-teams", "last_sha", new_sha)
    update_firestore_field("SyncStatus", "oi-context-teams", "timestamp", timestamp)
