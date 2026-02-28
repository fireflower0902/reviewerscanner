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
    
    # 1. 기존 chunk 삭제 (옵션, 덮어쓰기 위해 보통 그냥 씁니다만, 
    # 이전 크롤링보다 이번 크롤링 개수가 적어서 남는 찌꺼기 chunk를 지우려면 수행하는 것이 좋음,
    # 이번 구현에서는 덮어쓰기로 진행하고, 총 청크 개수를 메타데이터에 기록합니다.)
    
    CHUNK_SIZE = 1000
    chunks = list(chunk_list(campaigns, CHUNK_SIZE))
    total_chunks = len(chunks)
    
    print(f"\n[Firebase Chunking] Total {len(campaigns)} items will be divided into {total_chunks} chunks.")
    
    batch = db.batch()
    
    # campaigns_chunks 컬렉션에 chunk_0, chunk_1 형식으로 저장
    for i, chunk_data in enumerate(chunks):
        doc_ref = db.collection('campaigns_chunks').document(f'chunk_{i}')
        # Firestore 문서는 dict 형태여야 하므로 배열을 감싸줍니다.
        batch.set(doc_ref, {'items': chunk_data})
        print(f" -> Prepared [chunk_{i}] with {len(chunk_data)} items.")
        
    # metrics 컬렉션에 status 문서로 현재 총 청크 수 및 업데이트 시간 저장
    meta_ref = db.collection('metrics').document('status')
    batch.set(meta_ref, {
        'total_chunks': total_chunks,
        'total_items': len(campaigns),
        'last_updated': datetime.datetime.now(datetime.timezone.utc)
    })
    
    # Batch commit
    batch.commit()
    print(f"[Firebase Chunking] Successfully committed {total_chunks} chunks and 1 metadata document!")
    print(f"[Firebase Chunking] Now web clients will only need {total_chunks + 1} reads instead of {len(campaigns)}!\n")
