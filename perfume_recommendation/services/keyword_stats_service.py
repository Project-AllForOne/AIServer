import json
import os
from collections import Counter
from datetime import datetime, timedelta

CACHE_FILE = "perfume_cache.json"

def load_cache():
    """캐시 파일을 로드하여 키워드 데이터를 반환"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"keywords": {}}

def save_cache(data):
    """키워드 데이터를 캐시에 저장"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_keyword_stats(extracted_keywords):
    """추출된 키워드를 주간 단위로 집계"""
    data = load_cache()
    keywords = data.get("keywords", {})

    today = datetime.now().strftime("%Y-%m-%d")
    for keyword in extracted_keywords:
        if keyword not in keywords:
            keywords[keyword] = {"count": 0, "history": {}}
        keywords[keyword]["count"] += 1
        keywords[keyword]["history"][today] = keywords[keyword]["count"]

    data["keywords"] = keywords
    save_cache(data)

def get_top_keywords():
    """가장 많이 입력된 상위 5개 키워드 반환"""
    data = load_cache()
    keywords = data.get("keywords", {})

    # 최근 7일치 데이터 필터링
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    sorted_keywords = sorted(
        keywords.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:5]

    result = []
    for keyword, details in sorted_keywords:
        prev_count = details["history"].get(last_week, 0)
        result.append({
            "keyword": keyword,
            "count": details["count"],
            "change": details["count"] - prev_count
        })

    return result
