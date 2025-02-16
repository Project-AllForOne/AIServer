from fastapi import APIRouter
from services.keyword_stats_service import get_top_keywords

router = APIRouter()

@router.get("/keyword-stats")
def keyword_stats():
    """주간 키워드 통계를 반환하는 API"""
    return {"top_keywords": get_top_keywords()}
