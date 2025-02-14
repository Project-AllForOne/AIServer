from pymongo import MongoClient
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MongoService:
    def __init__(self):
        # MongoDB 연결 설정
        MONGO_URI = "mongodb://banghyang:banghyang@192.168.0.182:27017/banghyang?authSource=banghyang"
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client["banghyang"]

            # 컬렉션 설정
            self.chat_history = self.db["chat_history"]  
            self.chat_summary = self.db["chat_summary"]  
            self.image_embeddings = self.db["image_embeddings"]
            self.text_embeddings = self.db["text_embeddings"]

            # 인덱스 생성
            self.image_embeddings.create_index("identifier", unique=True)
            self.text_embeddings.create_index("identifier", unique=True)

            logger.info("✅ MongoDB 연결 성공")
        except Exception as e:
            logger.error(f"🚨 MongoDB 연결 실패: {e}")
            raise

    def save_image_embedding(self, image_url: str, embedding: np.ndarray):
        """이미지 임베딩을 MongoDB에 저장"""
        try:
            document = {
                "identifier": image_url,
                "embedding": embedding.tolist(),
                "type": "image",
            }
            self.image_embeddings.update_one(
                {"identifier": image_url}, {"$set": document}, upsert=True
            )
            logger.info(f"✅ 이미지 임베딩 저장 완료: {image_url}")
            return True
        except Exception as e:
            logger.error(f"🚨 이미지 임베딩 저장 실패: {e}")
            return False

    def load_image_embedding(self, image_url: str):
        """MongoDB에서 이미지 임베딩 불러오기"""
        try:
            result = self.image_embeddings.find_one({"identifier": image_url})
            if result:
                logger.info(f"✅ 이미지 임베딩 로드 완료: {image_url}")
                return np.array(result["embedding"])
            logger.info(f"❌ 이미지 임베딩 없음: {image_url}")
            return None
        except Exception as e:
            logger.error(f"🚨 이미지 임베딩 로드 실패: {e}")
            return None

    def save_text_embedding(self, text: str, embedding: np.ndarray):
        """텍스트 임베딩을 MongoDB에 저장"""
        try:
            document = {
                "identifier": text,
                "embedding": embedding.tolist(),
                "type": "text",
            }
            self.text_embeddings.update_one(
                {"identifier": text}, {"$set": document}, upsert=True
            )
            logger.info(f"✅ 텍스트 임베딩 저장 완료: {text}")
            return True
        except Exception as e:
            logger.error(f"🚨 텍스트 임베딩 저장 실패: {e}")
            return False

    def load_text_embedding(self, text: str):
        """MongoDB에서 텍스트 임베딩 불러오기"""
        try:
            result = self.text_embeddings.find_one({"identifier": text})
            if result:
                logger.info(f"✅ 텍스트 임베딩 로드 완료: {text}")
                return np.array(result["embedding"])
            logger.info(f"❌ 텍스트 임베딩 없음: {text}")
            return None
        except Exception as e:
            logger.error(f"🚨 텍스트 임베딩 로드 실패: {e}")
            return None
        

    def get_recent_chat_history(self, user_id: str, limit: int = 3) -> list:
        """MongoDB에서 최근 대화 기록을 가져옴 (최신 3개)"""
        chats = (
            self.chat_history.find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return [chat["content"] for chat in chats if "content" in chat]

    def save_chat_summary(self, user_id: str, summary: str):
        """오래된 대화 내용을 요약하여 MongoDB에 저장"""
        summary_data = {
            "user_id": user_id,
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
        self.chat_summary.update_one({"user_id": user_id}, {"$set": summary_data}, upsert=True)
        logger.info(f"✅ 요약 저장 완료: {user_id} - {summary[:30]}...")

    def get_chat_summary(self, user_id: str) -> str:
        """MongoDB에서 사용자의 대화 요약을 가져옴"""
        summary = self.chat_summary.find_one({"user_id": user_id})
        return summary["summary"] if summary else ""

    def __del__(self):
        """소멸자: MongoDB 연결 종료"""
        if hasattr(self, "client"):
            self.client.close()
