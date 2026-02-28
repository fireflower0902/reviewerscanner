import os
import firebase_admin
from firebase_admin import credentials, storage

def upload_to_storage(json_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(current_dir, "serviceAccountKey.json")

    if not os.path.exists(key_path):
        print("🚨 'serviceAccountKey.json' is missing.")
        return

    # Initialize app if not already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'reviewerscanner-dev.firebasestorage.app'
        })

    print(f"\n[Storage] Uploading {json_path} to Firebase Storage...")
    
    bucket = storage.bucket()
    blob = bucket.blob('campaigns.json')
    
    # Upload the file
    blob.upload_from_filename(json_path, content_type='application/json')
    
    # Generate download url (Firebase Storage URL format)
    # Allows download without token if security rules allow public read
    # or we can make it public
    try:
        blob.make_public()
        print(f"[Storage] Successfully uploaded. Public URL: {blob.public_url}")
    except Exception as e:
        print(f"[Storage] Uploaded, but couldn't make public via GCP: {e}")
        print("[Storage] It will still be accessible via Firebase rules if configured.")
    
    print("[Storage] All data is now available as a single file!\n")
