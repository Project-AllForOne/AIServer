from fastapi import APIRouter
from services.keyword_stats_service import get_top_keywords

router = APIRouter()

@router.get("")  # ✅ 수정: 빈 문자열("")을 넣어서 prefix와 결합되도록 변경
def keyword_stats():
    """주간 키워드 통계를 반환하는 API"""
    return {"top_keywords": get_top_keywords()}
