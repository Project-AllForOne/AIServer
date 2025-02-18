import json
from typing import List
from collections import Counter
from datetime import datetime
import os


class RecommendationService:
    def __init__(self, cache_dir: str = "data/"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def save_recommended_perfumes_cache(self, perfumes: List[dict]) -> None:
        """
        추천된 향수를 캐시 파일에 저장합니다.
        :param perfumes: 추천된 향수 리스트 (이름, 브랜드, 이미지 포함)
        """
        existing_perfumes = self.load_cache_data()
        existing_perfumes.extend(perfumes)
        self.save_cache_data(existing_perfumes)

    def get_recommended_perfumes_from_cache(self) -> List[dict]:
        """
        저장된 추천 향수 캐시 데이터를 불러옵니다.
        :return: 캐시된 추천 향수 리스트
        """
        return self.load_cache_data()

    def calculate_weekly_recommendation_stats(self) -> dict:
        """
        주간 추천 향수 통계를 계산하여 상위 5개 향수와 전 주 대비 증감을 반환합니다.
        :return: 주간 추천 향수 통계
        """
        perfumes = self.get_recommended_perfumes_from_cache()
        perfume_freq = Counter([(p["name"], p["brand"]) for p in perfumes])
        sorted_perfumes = perfume_freq.most_common(5)

        current_date = datetime.now().strftime("%Y%m%d")
        current_file = os.path.join(
            self.cache_dir, f"weekly_recommendation_stats_{current_date}.json"
        )

        last_week_file = self.get_last_week_file()
        last_week_stats = self.load_json_file(last_week_file) if last_week_file else {}

        # 추천 변화 계산
        recommendation_changes = self.calculate_recommendation_changes(
            sorted_perfumes, last_week_stats.get("top_recommendations", [])
        )

        # 주간 통계 저장
        weekly_stats = {
            "date": current_date,
            "top_recommendations": sorted_perfumes,
            "total_recommendations": len(perfumes),
            "recommendation_changes": recommendation_changes,
        }
        self.save_json_file(current_file, weekly_stats)

        return weekly_stats

    def save_cache_data(self, data: List[dict]) -> None:
        cache_file = os.path.join(self.cache_dir, "recommended_perfumes_cache.json")
        self.save_json_file(cache_file, data)

    def load_cache_data(self) -> List[dict]:
        cache_file = os.path.join(self.cache_dir, "recommended_perfumes_cache.json")
        return self.load_json_file(cache_file, default=[])

    def get_last_week_file(self) -> str:
        """
        지난 주의 통계 파일을 찾아서 반환합니다.
        """
        files = [
            f
            for f in os.listdir(self.cache_dir)
            if f.startswith("weekly_recommendation_stats_")
        ]
        files.sort(reverse=True)
        return os.path.join(self.cache_dir, files[1]) if len(files) > 1 else ""

    def load_json_file(self, file_path: str, default=None):
        """
        JSON 파일을 읽어옵니다. 파일이 존재하지 않으면 기본값을 반환합니다.
        """
        if not os.path.exists(file_path):
            return default if default is not None else {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json_file(self, file_path: str, data):
        """
        데이터를 JSON 파일로 저장합니다.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def calculate_recommendation_changes(
        self, current_recommendations, last_recommendations
    ) -> dict:
        """
        주간 추천 향수의 추천 수 변화를 계산하여 반환합니다.
        :param current_recommendations: 현재 추천된 향수 목록
        :param last_recommendations: 지난 주 추천된 향수 목록
        :return: 추천 수 변화
        """
        current_freq = dict(current_recommendations)
        last_freq = dict(last_recommendations)
        changes = {}

        for perfume, count in current_freq.items():
            last_count = last_freq.get(perfume, 0)
            changes[perfume] = {
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
