"""Cloudflare R2 업로더 (S3 호환 API)

크롤링 결과를 gzip JSON 한 파일로 R2에 올린다. 사이트는 이 파일을 읽는다.
필요한 환경변수: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
"""
import gzip
import json
import os
from typing import Dict, List

OBJECT_KEY = "v1/campaigns.json.gz"
REQUIRED_ENV = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")


def is_configured() -> bool:
    return all(os.environ.get(k) for k in REQUIRED_ENV)


def build_payload(campaigns: List[Dict]) -> bytes:
    raw = json.dumps(campaigns, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return gzip.compress(raw, compresslevel=9)


def upload_campaigns(campaigns: List[Dict]) -> None:
    import boto3  # 로컬에서 R2를 쓰지 않을 때를 위해 지연 import

    payload = build_payload(campaigns)
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    client.put_object(
        Bucket=os.environ["R2_BUCKET"],
        Key=OBJECT_KEY,
        Body=payload,
        ContentType="application/json",
    )
    print(f"[R2] Uploaded {len(campaigns)} items → {OBJECT_KEY} ({len(payload)/1024/1024:.2f} MB gzip)")
