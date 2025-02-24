from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests

app = FastAPI()

# AI 서버 URL (환경에 따라 변경 필요)
AI_SERVER_URL = "http://localhost:8001"


class UserQuery(BaseModel):
    user_input: str


class WeeklyStatsResponse(BaseModel):
    date: str
    top_keywords: List[Dict[str, int]]
    total_keywords: int
    keyword_changes: Dict[str, Dict[str, float]]


@app.post("/extract_keywords")
def extract_keywords(user_query: UserQuery):
    """
    사용자 입력을 AI 서버로 보내 키워드를 추출하는 API
    """
    try:
        response = requests.post(
            f"{AI_SERVER_URL}/extract_keywords", json=user_query.dict()
        )
        response.raise_for_status()
        data = response.json()
        if data is None:
            raise HTTPException(status_code=404, detail="키워드가 추출되지 않았습니다.")
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI 서버 요청 실패: {str(e)}")


@app.get("/weekly_stats", response_model=WeeklyStatsResponse)
def get_weekly_stats():
    """
    AI 서버에서 주간 키워드 통계를 가져오는 API
    """
    try:
        response = requests.get(f"{AI_SERVER_URL}/weekly_stats")
        response.raise_for_status()
        data = response.json()
        if not data:
            raise HTTPException(status_code=404, detail="주간 통계가 없습니다.")
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI 서버 요청 실패: {str(e)}")


@app.get("/top_perfumes")
def get_top_perfumes():
    """
    AI 서버에서 주간 인기 향수 데이터를 가져오는 API
    """
    try:
        response = requests.get(f"{AI_SERVER_URL}/top_perfumes")
        response.raise_for_status()
        data = response.json()
        if data is None:
            raise HTTPException(status_code=404, detail="인기 향수 데이터가 없습니다.")
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI 서버 요청 실패: {str(e)}")
