"""Cloudflare R2 업로더 (S3 호환 API)

크롤링 결과를 gzip JSON 한 파일로 R2에 올린다. 사이트는 이 파일을 읽는다.
필요한 환경변수: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
"""
import datetime
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


def _client():
    import boto3  # 로컬에서 R2를 쓰지 않을 때를 위해 지연 import

    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def upload_campaigns(campaigns: List[Dict], generated_at: str = None) -> None:
    """generated_at: 마감 표기("N일 남음")를 계산한 시점(ISO). 사이트가 날짜 기준으로 보정하는 데 쓴다."""
    payload = build_payload(campaigns)
    client = _client()
    client.put_object(
        Bucket=os.environ["R2_BUCKET"],
        Key=OBJECT_KEY,
        Body=payload,
        ContentType="application/json",
        Metadata={"generated-at": generated_at} if generated_at else {},
    )
    print(f"[R2] Uploaded {len(campaigns)} items → {OBJECT_KEY} ({len(payload)/1024/1024:.2f} MB gzip)")


# ---------------------------------------------------------------------------
# 부분 파일(part): GitHub Actions에서 수집할 수 없는 사이트(예: 강남맛집)는 한국 IP 기기가
# 따로 수집해서 v1/parts/<name>.json.gz 로 올리고, aggregator가 합친다.
# ---------------------------------------------------------------------------
KST = datetime.timezone(datetime.timedelta(hours=9))


def part_key(name: str) -> str:
    return f"v1/parts/{name}.json.gz"


def upload_part(name: str, platform: str, items: List[Dict], client=None) -> None:
    body = {
        "platform": platform,
        "crawled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    payload = gzip.compress(raw, compresslevel=9)
    (client or _client()).put_object(
        Bucket=os.environ["R2_BUCKET"], Key=part_key(name), Body=payload, ContentType="application/json"
    )
    print(f"[R2] Uploaded part '{name}': {len(items)} items ({len(payload)/1024:.0f} KB gzip)")


def load_part(name: str, max_age_hours: float = 36, now=None, client=None) -> List[Dict]:
    """부분 파일을 읽어 반환한다. 너무 오래됐으면(max_age_hours 초과) 빈 목록.
    남은 일수 표기는 수집 시점 이후 지난 날짜만큼 보정하고, 마감이 지난 항목은 제외한다."""
    from helpers import shift_dday

    try:
        obj = (client or _client()).get_object(Bucket=os.environ["R2_BUCKET"], Key=part_key(name))
        body = json.loads(gzip.decompress(obj["Body"].read()).decode("utf-8"))
    except Exception as e:
        print(f"[R2] part '{name}' 없음/읽기 실패: {type(e).__name__}")
        return []

    now = now or datetime.datetime.now(datetime.timezone.utc)
    crawled_at = datetime.datetime.fromisoformat(body["crawled_at"])
    age_hours = (now - crawled_at).total_seconds() / 3600
    if age_hours > max_age_hours:
        print(f"[R2] part '{name}' 수집 후 {age_hours:.1f}시간 경과(기준 {max_age_hours}시간) → 제외")
        return []

    days_passed = (now.astimezone(KST).date() - crawled_at.astimezone(KST).date()).days
    items, dropped = [], 0
    for it in body["items"]:
        shifted = shift_dday(it["meta"].get("dday", ""), days_passed)
        if shifted is None:
            dropped += 1
            continue
        it["meta"]["dday"] = shifted
        items.append(it)
    print(f"[R2] part '{name}': {len(items)}개 사용 (수집 후 {age_hours:.1f}시간, 마감 경과 {dropped}개 제외)")
    return items


def load_previous(client=None):
    """직전에 올린 전체 데이터 파일과 그 생성 시각(ISO)을 읽는다. 없거나 읽기 실패면 ([], None)."""
    try:
        obj = (client or _client()).get_object(Bucket=os.environ["R2_BUCKET"], Key=OBJECT_KEY)
        items = json.loads(gzip.decompress(obj["Body"].read()).decode("utf-8"))
        generated_at = (obj.get("Metadata") or {}).get("generated-at")
        return items, generated_at
    except Exception as e:
        print(f"[R2] 직전 데이터를 읽지 못했습니다(유지 기능 건너뜀): {type(e).__name__}")
        return [], None
