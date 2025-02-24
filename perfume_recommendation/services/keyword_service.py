from typing import List, Dict
from collections import Counter
from datetime import datetime
from db_service import DBService


class KeywordService:
    def __init__(self, db_service: DBService):
        self.db_service = db_service

    def save_keywords(self, user_query: str, keywords: List[str]) -> None:
        """키워드 저장 (MySQL + MongoDB 로그 기록)"""
        self.db_service.save_keywords(keywords)
        self.db_service.save_keyword_log(user_query, keywords)

    def get_keywords(self) -> List[str]:
        """저장된 키워드 조회 (MySQL에서 7일치 조회)"""
        return self.db_service.get_keywords()

    def calculate_weekly_keyword_stats(self) -> dict:
        """
        주간 키워드 통계를 계산하여 상위 5개 키워드와 전 주 대비 증감을 반환합니다.
        :return: 주간 키워드 통계
        """
        # MySQL에서 최근 7일간 키워드 조회
        keywords = self.db_service.get_keywords()
        keyword_freq = Counter(keywords)

        # 상위 5개 키워드 추출
        sorted_keywords = keyword_freq.most_common(5)

        # 현재 날짜
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 지난 주 키워드 통계 조회
        last_week_stats = self.db_service.get_last_week_stats()
        keyword_changes = self.calculate_keyword_changes(
            sorted_keywords, last_week_stats.get("top_keywords", [])
        )

        # 주간 통계 데이터 생성
        weekly_stats = {
            "date": current_date,
            "top_keywords": sorted_keywords,
            "total_keywords": len(keywords),
            "keyword_changes": keyword_changes,
        }

        # MySQL에 저장
        self.db_service.save_weekly_stats(weekly_stats)

        return weekly_stats

    def calculate_keyword_changes(self, current_keywords, last_keywords) -> dict:
        """
        현재 키워드와 지난 키워드를 비교하여 증감량을 계산합니다.
        :param current_keywords: 현재 주 키워드 리스트
        :param last_keywords: 지난 주 키워드 리스트
        :return: 키워드 증감량
        """
        current_freq = dict(current_keywords)
        last_freq = dict(last_keywords)

        changes = {}

        # 증감 계산
        for keyword, count in current_freq.items():
            last_count = last_freq.get(keyword, 0)
            changes[keyword] = {
                "current_count": count,
                "last_count": last_count,
                "change": count - last_count,
                "percentage_change": (
                    ((count - last_count) / last_count * 100)
                    if last_count > 0
                    else None
                ),
            }

        return changes
