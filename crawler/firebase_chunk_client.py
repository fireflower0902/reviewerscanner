import os
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def upload_to_firestore_chunks(campaigns):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(current_dir, "serviceAccountKey.json")

    if not os.path.exists(key_path):
        print("🚨 'serviceAccountKey.json' 파일이 없습니다!")
        return

    # Initialize app if not already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    
    CHUNK_SIZE = 1000
    chunks = list(chunk_list(campaigns, CHUNK_SIZE))
    total_chunks = len(chunks)
    
    print(f"\n[Firebase Chunking] Total {len(campaigns)} items will be divided into {total_chunks} chunks.")
    
    # ✅ 수정: 각 청크를 개별 set()으로 저장 (batch 500개 제한 우회)
    # Firestore batch는 최대 500개 연산 제한이 있어,
    # 이전 방식(단일 batch)으로는 청크가 많을 경우 commit 자체가 실패했음.
    for i, chunk_data in enumerate(chunks):
        doc_ref = db.collection('campaigns_chunks').document(f'chunk_{i}')
        doc_ref.set({'items': chunk_data})
        print(f" -> Uploaded [chunk_{i}] with {len(chunk_data)} items.")
        
    # metrics 컬렉션에 status 문서로 현재 총 청크 수 및 업데이트 시간 저장
    meta_ref = db.collection('metrics').document('status')
    meta_ref.set({
        'total_chunks': total_chunks,
        'total_items': len(campaigns),
        'last_updated': datetime.datetime.now(datetime.timezone.utc)
    })
    
    print(f"[Firebase Chunking] ✅ Successfully uploaded {total_chunks} chunks and 1 metadata document!")
    print(f"[Firebase Chunking] Total {len(campaigns)} campaigns are now live!\n")
