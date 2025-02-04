import pymysql
import logging
from typing import List, Dict
from services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = self.connect_to_db()  # ✅ 초기 연결 설정

    def connect_to_db(self):
        try:
            connection = pymysql.connect(
                host=self.db_config["host"],
                port=int(self.db_config["port"]),
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info("✅ 데이터베이스 연결 성공!")
            return connection
        except pymysql.MySQLError as e:
            logger.error(f"🚨 데이터베이스 연결 오류: {e}")
            return None

    def fetch_spices_by_line(self, line_name: str) -> List[str]:
        """
        특정 line_name에 속한 향료 목록을 가져옵니다.
        """
        line_query = """
        SELECT id FROM line WHERE name = %s
        """
        spice_query = """
        SELECT s.name_kr FROM spice s WHERE s.line_id = %s
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(line_query, (line_name,))
                line_result = cursor.fetchone()
                if not line_result:
                    logger.error(f"No line found for line_name: {line_name}")
                    return []
                line_id = line_result['id']

                cursor.execute(spice_query, (line_id,))
                spices = [row['name_kr'] for row in cursor.fetchall()]
                logger.info(f"✅ 향료 데이터 조회 성공: {spices}")
                return spices
        except pymysql.MySQLError as e:
            logger.error(f"🚨 데이터베이스 오류 발생: {e}")
            return []

    def fetch_product(self) -> List[Dict]:

        query = """
        SELECT * FROM product 
        LIMIT 3;
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)  # ✅ 향료 조건 없이 전체 향수 조회
                products = cursor.fetchall()
                logger.info(f"✅ 향수 데이터 조회 성공: {products}")
                return products
        except pymysql.MySQLError as e:
            logger.error(f"🚨 데이터베이스 오류 발생: {e}")
            return []

    def close_connection(self):
        """ DB 연결 닫기 """
        if self.connection:
            self.connection.close()
            logger.info("🔌 데이터베이스 연결 닫힘")


    # def fetch_product_by_user_input(self, user_input: str, max_results: int = 3):
    #     """
    #     사용자 입력을 기반으로 필터링된 향수 목록을 반환하며, 최대 결과 수를 제한합니다.
    #     """
    #     # Load the perfume cache
    #     base_path = os.path.abspath(os.path.dirname(__file__))
    #     cache_path = os.path.join(base_path, "..", "data", "perfume_cache.json")

    #     if not os.path.exists(cache_path):
    #         raise RuntimeError(f"Perfume cache file not found: {cache_path}")

    #     with open(cache_path, "r", encoding="utf-8") as file:
    #         product = json.load(file)

    #     # Preprocess user input
    #     user_input = user_input.strip().lower()

    #     # Use regular expressions to filter product based on user input
    #     filtered_product = [
    #         perfume for perfume in product
    #         if re.search(user_input, perfume["brand"].lower()) or re.search(user_input, perfume["name"].lower())
    #     ]

    #     # Log filtered product
    #     logger.info(f"Filtered product (before limiting results): {filtered_product}")

    #     # Return limited results
    #     limited_results = filtered_product[:max_results]
    #     logger.info(f"Filtered product (limited to {max_results}): {limited_results}")

    #     if not limited_results:
    #         raise ValueError(f"No product found for the given user input: {user_input}")

    #     return limited_results
