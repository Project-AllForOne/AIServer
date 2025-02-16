from fastapi import APIRouter
from pydantic import BaseModel
import logging
from transformers import pipeline

# 키워드 추출 모델 로드
extractor = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

# 로그 설정
logging.basicConfig(filename='keyword_logs.log', level=logging.INFO)

# FastAPI 라우터 초기화
router = APIRouter()

# 입력 텍스트 모델
class UserInput(BaseModel):
    text: str

# 키워드 추출 함수
def extract_keywords(text: str):
    results = extractor(text)
    keywords = [result['word'] for result in results if result['entity_group'] in ['ORG', 'MISC', 'PER', 'LOC']]
    return keywords

# 키워드 추출 API 엔드포인트
@router.post("/extract_keywords")
async def extract_keywords_api(user_input: UserInput):
    text = user_input.text
    keywords = extract_keywords(text)
    
    # 키워드 로그에 저장
    for keyword in keywords:
        logging.info(f"Extracted Keyword: {keyword}")
    
    return {"keywords": keywords}
