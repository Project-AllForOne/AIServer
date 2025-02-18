import json
from typing import List
from collections import Counter
from datetime import datetime
import os


class KeywordService:
    def __init__(self, cache_dir: str = "data/"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

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

        # 빈도수 높은 순으로 정렬하여 상위 5개 키워드 추출 (메인 페이지는 Top 3로 수정)
        sorted_keywords = keyword_freq.most_common(3)

        # 현재 날짜 기반 파일명 생성
        current_date = datetime.now().strftime("%Y%m%d")
        current_file = os.path.join(
            self.cache_dir, f"weekly_keyword_stats_{current_date}.json"
        )

        # 지난 주 파일 찾기
        last_week_file = self.get_last_week_file()
        last_week_stats = self.load_json_file(last_week_file) if last_week_file else {}

        # 현재 주와 지난 주의 키워드 비교 후 증감 계산
        keyword_changes = self.calculate_keyword_changes(
            sorted_keywords, last_week_stats.get("top_keywords", [])
        )

        # 주간 통계 저장
        weekly_stats = {
            "date": current_date,
            "top_keywords": sorted_keywords,
            "total_keywords": len(keywords),
            "keyword_changes": keyword_changes,
        }
        self.save_json_file(current_file, weekly_stats)

        return weekly_stats

    def save_cache_data(self, data: List[str]) -> None:
        """
        데이터를 JSON 형식으로 캐시 파일에 저장합니다.
        :param data: 저장할 데이터
        """
        cache_file = os.path.join(self.cache_dir, "keywords_cache.json")
        self.save_json_file(cache_file, data)

    def load_cache_data(self) -> List[str]:
        """
        캐시 파일에서 데이터를 로드합니다.
        :return: 로드된 데이터
        """
        cache_file = os.path.join(self.cache_dir, "keywords_cache.json")
        return self.load_json_file(cache_file, default=[])

    def get_last_week_file(self) -> str:
        """
        가장 최근의 주간 키워드 통계 파일을 찾습니다.
        :return: 가장 최근 파일 경로 (없으면 빈 문자열 반환)
        """
        files = [
            f
            for f in os.listdir(self.cache_dir)
            if f.startswith("weekly_keyword_stats_")
        ]
        files.sort(reverse=True)  # 최신 파일이 먼저 오도록 정렬
        return os.path.join(self.cache_dir, files[1]) if len(files) > 1 else ""

    def load_json_file(self, file_path: str, default=None):
        """
        JSON 파일을 로드합니다.
        :param file_path: 파일 경로
        :param default: 파일이 없을 경우 반환할 기본값
        :return: 로드된 데이터
        """
        if not os.path.exists(file_path):
            return default if default is not None else {}

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json_file(self, file_path: str, data):
        """
        데이터를 JSON 파일로 저장합니다.
        :param file_path: 저장할 파일 경로
        :param data: 저장할 데이터
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

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
