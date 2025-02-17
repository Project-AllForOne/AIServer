import json
from typing import List
from collections import Counter
from datetime import datetime


class KeywordService:
    def __init__(self, cache_file: str = "data/keywords_cache.json"):
        self.cache_file = cache_file

    def save_keywords_cache(self, keywords: List[str]) -> None:
        """
        추출된 키워드를 캐시 파일에 저장합니다.
        :param keywords: 추출된 키워드 리스트
        """
        # 기존 캐시 로딩
        existing_keywords = self.load_cache_data()

        # 새로운 키워드를 기존 캐시와 합침
        existing_keywords.extend(keywords)

        # 캐시 파일에 저장
        self.save_cache_data(existing_keywords)

    def get_keywords_from_cache(self) -> List[str]:
        """
        저장된 키워드 캐시 데이터를 불러옵니다.
        :return: 캐시된 키워드 리스트
        """
        return self.load_cache_data()

    def calculate_weekly_keyword_stats(self) -> dict:
        """
        주간 키워드 통계를 계산하여 상위 5개 키워드와 전 주 대비 증감을 반환합니다.
        :return: 주간 키워드 통계
        """
        # 캐시에서 키워드 로드
        keywords = self.get_keywords_from_cache()

        # 키워드의 빈도수 계산 (collections.Counter 사용)
        keyword_freq = Counter(keywords)

        # 빈도수 높은 순으로 정렬하여 상위 5개 키워드 추출
        sorted_keywords = keyword_freq.most_common(5)

        # 현재 주 (주 단위로 키워드를 구분하기 위해)
        current_week = datetime.now().strftime("%Y-%U")  # Format as Year-Week

        # 지난 주 통계 로드 (파일에서)
        last_week_stats = self.load_last_week_stats()

        # 현재 주와 지난 주의 키워드 비교 후 증감 계산
        keyword_changes = self.calculate_keyword_changes(
            sorted_keywords, last_week_stats.get("top_keywords", [])
        )

        # 주간 통계 반환
        return {
            "week": current_week,
            "top_keywords": sorted_keywords,
            "total_keywords": len(keywords),
            "keyword_changes": keyword_changes,
        }

    def save_cache_data(self, data: List[str]) -> None:
        """
        데이터를 JSON 형식으로 캐시 파일에 저장합니다.
        :param data: 저장할 데이터
        """
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_cache_data(self) -> List[str]:
        """
        캐시 파일에서 데이터를 로드합니다.
        :return: 로드된 데이터
        """
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # 파일이 없는 경우 빈 리스트 반환
            return []

    def load_last_week_stats(self) -> dict:
        """
        지난 주의 키워드 통계를 로드합니다.
        :return: 지난 주 키워드 통계
        """
        try:
            with open("data/weekly_keyword_stats.json", "r", encoding="utf-8") as f:
                stats = json.load(f)
                # 지난 주와 현재 주가 다를 경우만 로드
                last_week = datetime.now().strftime("%Y-%U")
                if stats["week"] != last_week:
                    return stats
                else:
                    return {}
        except FileNotFoundError:
            # 첫 번째 주 통계라면 빈 딕셔너리 반환
            return {}

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
