import os
import firebase_admin
from firebase_admin import credentials, firestore

def upload_to_firestore(campaigns):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(current_dir, "serviceAccountKey.json")

    if not os.path.exists(key_path):
        print("\n\n" + "="*60)
        print("🚨 [Firebase Error] 'serviceAccountKey.json' 파일이 없습니다!")
        print("Firebase Console (https://console.firebase.google.com/) 에 접속해서")
        print("프로젝트 설정 -> 서비스 계정 -> '새 비공개 키 생성' 버튼을 눌러")
        print("다운로드한 JSON 파일의 이름을 'serviceAccountKey.json'으로 변경한 후")
        print(f"[{current_dir}] 폴더 안에 넣어주세요!")
        print("="*60 + "\n\n")
        return

    # Initialize app if not already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    collection_ref = db.collection('campaigns')

    print(f"\n[Firebase] Starting to upload {len(campaigns)} campaigns to Firestore...")

    # Firestore Batch writes (Up to 500 per batch)
    batches = []
    batch = db.batch()
    count = 0

    for idx, c in enumerate(campaigns):
        # Create a unique ID from the URL using hashing or just string
        import hashlib
        doc_id = hashlib.md5(c['url'].encode('utf-8')).hexdigest()
        
        doc_ref = collection_ref.document(doc_id)
        batch.set(doc_ref, c, merge=True)
        count += 1
        
        if count == 500:
            batches.append(batch)
            batch = db.batch()
            count = 0

    if count > 0:
        batches.append(batch)

    # Commit all batches
    total_committed = 0
    for b in batches:
        b.commit()
        total_committed += 1

    print(f"[Firebase] Successfully completed {len(batches)} batch commits.")
    print(f"[Firebase] All {len(campaigns)} campaigns are now synced to Firestore!\n")

