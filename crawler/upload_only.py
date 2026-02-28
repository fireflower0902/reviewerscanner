import json
import os
from firebase_chunk_client import upload_to_firestore_chunks

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
json_path = os.path.join(project_root, "public", "campaigns.json")

print(f"Reading data from {json_path}...")

with open(json_path, 'r', encoding='utf-8') as f:
    campaigns = json.load(f)
    print(f"Loaded {len(campaigns)} campaigns.")
    upload_to_firestore_chunks(campaigns)

print("Chunk Upload complete.")
