import os
from dotenv import load_dotenv
from datetime import datetime
from langgraph.graph import StateGraph
from langgraph.pregel import Channel
from typing import TypedDict, Annotated, Optional
from services.llm_service import LLMService
from services.db_service import DBService
from services.image_generation_service import ImageGenerationService
from services.llm_img_service import LLMImageService
from services.prompt_loader import PromptLoader
from models.img_llm_client import GPTClient
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class PerfumeState(TypedDict):
    user_input: Annotated[str, Channel()]
    processed_input: str  
    next_node: str
    recommendations: Optional[list]
    spices: Optional[list]
    image_path: Optional[str]
    image_description: Optional[str]
    response: Optional[str]
    line_id: Optional[int]
    translated_input: Optional[str]
    error: Optional[str]

class PerfumeService:
    def __init__(self):
        self.graph = StateGraph(state_schema=PerfumeState)

        db_config = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
        }

        self.db_service = DBService(db_config)
        self.prompt_loader = PromptLoader("models/chat_prompt_template.json")
        self.gpt_client = GPTClient(self.prompt_loader)
        self.llm_service = LLMService(self.gpt_client, self.db_service, self.prompt_loader)
        self.image_service = ImageGenerationService()
        self.llm_img_service = LLMImageService(self.gpt_client)

        self.define_nodes()
        self.graph.set_entry_point("input_processor")

    def define_nodes(self):
        # Add nodes
        self.graph.add_node("input_processor", self.input_processor)
        self.graph.add_node("process_input", self.process_input)
        self.graph.add_node("recommendation_generator", self.recommendation_generator)
        self.graph.add_node("fashion_recommendation_generator", self.fashion_recommendation_generator)
        self.graph.add_node("chat_handler", self.chat_handler)
        self.graph.add_node("error_handler", self.error_handler)
        self.graph.add_node("end", lambda x: x)  

        # Define routing function
        def route_based_on_intent(state: PerfumeState) -> str:
            if state.get("error"):
                return "error_handler"
            if state.get("processed_input") == "chat":
                return "chat_handler"
            if state.get("processed_input") == "fashion_recommendation":
                return "fashion_recommendation_generator"
            return "recommendation_generator"

        # Add conditional edges
        self.graph.add_conditional_edges(
            "process_input",
            route_based_on_intent,
            {
                "error_handler": "error_handler",
                "chat_handler": "chat_handler",
                "fashion_recommendation_generator": "fashion_recommendation_generator",
                "recommendation_generator": "recommendation_generator"
            }
        )

        # Add regular edges
        self.graph.add_edge("input_processor", "process_input")
        self.graph.add_edge("recommendation_generator", "end")  
        self.graph.add_edge("fashion_recommendation_generator", "end")  
        self.graph.add_edge("error_handler", "end")  
        self.graph.add_edge("chat_handler", "end")  

    def process_input(self, state: PerfumeState) -> PerfumeState:
        """사용자 입력을 분석하여 의도를 분류"""
        try:
            user_input = state["user_input"]  # ✅ 원본 유지
            logger.info(f"Received user input: {user_input}")

            intent_prompt = (
                f"입력: {user_input}\n"
                "다음 사용자의 의도를 분류하세요.\n"
                "의도 분류:\n"
                "(1) 향수 추천\n"
                "(2) 일반 대화\n"
                "(3) 패션 기반 향수 추천"
            )

            intent = self.gpt_client.generate_response(intent_prompt).strip()
            logger.info(f"Detected intent: {intent}")

            if "1" in intent:
                logger.info("💡 향수 추천 실행")
                state["processed_input"] = "recommendation"  
                state["next_node"] = "recommendation_generator"
            elif "3" in intent:
                logger.info("👕 패션 기반 향수 추천 실행")
                state["processed_input"] = "fashion_recommendation"
                state["next_node"] = "fashion_recommendation_generator"
            else:
                logger.info("💬 일반 대화 실행")
                state["processed_input"] = "chat"
                state["next_node"] = "chat_handler"

        except Exception as e:
            logger.error(f"Error processing input '{user_input}': {e}")
            state["processed_input"] = "chat"
            state["next_node"] = "chat_handler"

        return state
    
    def error_handler(self, state: PerfumeState) -> PerfumeState:
        """에러 상태를 처리하고 적절한 응답을 생성하는 핸들러"""
        try:
            error_msg = state.get("error", "알 수 없는 오류가 발생했습니다")
            logger.error(f"❌ 오류 처리: {error_msg}")

            # 에러 유형에 따른 사용자 친화적 메시지 생성
            user_message = (
                "죄송합니다. "
                + (
                    "추천을 생성할 수 없습니다." if "추천" in error_msg
                    else "요청을 처리할 수 없습니다." if "처리" in error_msg
                    else "일시적인 오류가 발생했습니다."
                )
                + " 다시 시도해 주세요."
            )

            # 상태 업데이트
            state["response"] = {
                "status": "error",
                "message": user_message,
                "recommendations": [],
                "debug_info": {
                    "original_error": error_msg,
                    "timestamp": datetime.now().isoformat()
                }
            }
            state["next_node"] = None  # 종료 노드로 설정

            logger.info("✅ 오류 처리 완료")
            return state

        except Exception as e:
            logger.error(f"❌ 오류 처리 중 추가 오류 발생: {e}")
            state["response"] = {
                "status": "error",
                "message": "시스템 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                "recommendations": []
            }
            state["next_node"] = None
            return state
    
    def input_processor(self, state: PerfumeState) -> PerfumeState:
        user_input = state["user_input"]
        logger.info(f"🔍 Input: {user_input}")
        state["next_node"] = "keyword_extractor"
        return state

    def keyword_extractor(self, state: PerfumeState) -> PerfumeState:
        extracted_data = self.llm_service.extract_keywords_from_input(state["user_input"])
        logger.info(f"🔍 추출된 데이터: {extracted_data}")

        state["line_id"] = extracted_data.get("line_id", 1)
        state["next_node"] = "database_query"
        return state

    def database_query(self, state: PerfumeState) -> PerfumeState:
        line_id = state["line_id"]
        logger.info(f"✅ DB 조회 - line_id: {line_id}")

        state["spices"] = self.db_service.fetch_spices_by_line(line_id)
        state["next_node"] = "recommendation_generator"
        return state

    def recommendation_generator(self, state: PerfumeState) -> PerfumeState:
        """향수 추천 생성"""
        try:
            logger.info("🔄 향수 추천 시작")

            # LLM 서비스를 통한 직접 추천 생성
            try:
                response = self.llm_service.generate_recommendation_response(state["user_input"])

                if response and isinstance(response, dict):
                    recommendations = response.get("recommendations", [])
                    content = response.get("content", "")
                    line_id = response.get("line_id")

                    logger.info("✅ LLM 추천 생성 완료")

                    state["response"] = {
                        "status": "success",
                        "mode": "recommendation",
                        "recommendation": recommendations,
                        "content": content,
                        "line_id": line_id
                    }

                    # 이미지 생성 시도
                    try:
                        image_state = self.image_generator(state)
                        state["image_path"] = image_state.get("image_path")
                        if state["image_path"]:
                            logger.info(f"✅ 이미지 생성 성공: {state['image_path']}")
                            state["response"]["image_path"] = state["image_path"]
                        else:
                            logger.warning("⚠️ 이미지 생성 실패")
                    except Exception as img_err:
                        logger.error(f"❌ 이미지 생성 오류: {img_err}")
                        state["image_path"] = None

                    state["next_node"] = "end"
                    return state

            except Exception as e:
                logger.error(f"❌ LLM 추천 생성 실패: {e}")

            # DB 기반 추천 시도
            try:
                if state.get("spices"):
                    spice_ids = [spice["id"] for spice in state["spices"]]
                    filtered_perfumes = self.db_service.get_perfumes_by_middel_notes(spice_ids)

                    if filtered_perfumes:
                        logger.info(f"✅ DB 기반 추천 완료: {len(filtered_perfumes)}개 찾음")

                        state["response"] = {
                            "status": "success",
                            "mode": "recommendation",
                            "recommendation": filtered_perfumes,
                            "content": "향료 기반으로 추천된 향수입니다.",
                            "line_id": state.get("line_id", 1)
                        }

                        # 이미지 생성 시도
                        try:
                            image_state = self.image_generator(state)
                            state["image_path"] = image_state.get("image_path")
                            if state["image_path"]:
                                logger.info(f"✅ 이미지 생성 성공: {state['image_path']}")
                                state["response"]["image_path"] = state["image_path"]
                            else:
                                logger.warning("⚠️ 이미지 생성 실패")
                        except Exception as img_err:
                            logger.error(f"❌ 이미지 생성 오류: {img_err}")
                            state["image_path"] = None

                        state["next_node"] = "end"
                        return state

            except Exception as e:
                logger.error(f"❌ DB 기반 추천 실패: {e}")

            # 모든 추천 방식 실패 시
            raise ValueError("적절한 향수를 찾을 수 없습니다")

        except Exception as e:
            logger.error(f"❌ 추천 생성 오류: {e}")
            state["error"] = str(e)
            state["next_node"] = "error_handler"
            return state

    def fashion_recommendation_generator(self, state: PerfumeState) -> PerfumeState:
        """패션 기반 향수 추천 생성"""
        try:
            logger.info("🔄 패션 기반 향수 추천 시작")
            
            # LLM 서비스를 통한 직접 추천 생성
            try:
                response = self.llm_service.fashion_based_generate_recommendation_response(state["user_input"])

                if response and isinstance(response, dict):
                    recommendations = response.get("recommendations", [])
                    content = response.get("content", "")
                    line_id = response.get("line_id")

                    logger.info("✅ LLM 추천 생성 완료")

                    # ✅ 최상위 recommendations 제거, response와 image_path만 유지
                    state["response"] = {
                        "status": "success",
                        "mode": "recommendation",
                        "recommendation": recommendations,
                        "content": content,
                        "line_id": line_id
                    }
                    state["image_path"] = None  # 이미지 생성 기능 제거
                    state["next_node"] = "end"
                    return state

            except Exception as e:
                logger.error(f"❌ LLM 추천 생성 실패: {e}")

            # DB 기반 추천 시도
            try:
                if state.get("spices"):
                    spice_ids = [spice["id"] for spice in state["spices"]]
                    filtered_perfumes = self.db_service.get_perfumes_by_middel_notes(spice_ids)

                    if filtered_perfumes:
                        logger.info(f"✅ DB 기반 추천 완료: {len(filtered_perfumes)}개 찾음")

                        state["response"] = {
                            "status": "success",
                            "mode": "recommendation",
                            "recommendation": recommendations,
                            "content": "향료 기반으로 추천된 향수입니다.",
                            "line_id": state.get("line_id", 1)
                        }
                        state["image_path"] = None
                        state["next_node"] = "end"
                        return state

            except Exception as e:
                logger.error(f"❌ DB 기반 추천 실패: {e}")

            # 모든 추천 방식 실패 시
            raise ValueError("적절한 향수를 찾을 수 없습니다")

        except Exception as e:
            logger.error(f"❌ 추천 생성 오류: {e}")
            state["error"] = str(e)
            state["next_node"] = "error_handler"
            return state
        
    def text_translation(self, state: PerfumeState) -> PerfumeState:
        user_input = state["user_input"]

        try:
            logger.info(f"🔄 텍스트 번역 시작: {user_input}")

            translation_prompt = (
                "Translate the following Korean text to English. "
                "Ensure it is a natural and descriptive translation suitable for image generation.\n\n"
                f"Input: {user_input}\n"
                "Output:"
            )

            translated_text = self.gpt_client.generate_response(translation_prompt).strip()
            logger.info(f"✅ 번역된 텍스트: {translated_text}")

            state["translated_input"] = translated_text
            state["next_node"] = "generate_image_description"

        except Exception as e:
            logger.error(f"🚨 번역 실패: {e}")
            state["translated_input"] = "Aesthetic abstract perfume-inspired image."
            state["next_node"] = "generate_image_description"

        return state

    def image_generator(self, state: PerfumeState) -> PerfumeState:
        """추천된 향수 기반으로 이미지 생성"""
        try:
            response = state.get("response") or {}
            recommendations = response.get("recommendations") or []  

            if not recommendations:
                logger.warning("⚠️ response 객체 내 추천 결과가 없어 이미지를 생성할 수 없습니다")
                state["response"]["image_path"] = None
                state["next_node"] = "end"
                return state

            # 이미지 프롬프트 생성
            prompt_parts = []

            # 향수 이름과 브랜드 정보 추가
            perfume_info = [f"{rec.get('name', '')} by {rec.get('brand', '')}" for rec in recommendations[:3]]
            if perfume_info:
                prompt_parts.append("Luxury perfume bottles of " + ", ".join(perfume_info))

            # 향수 특징과 상황 정보 추가
            for rec in recommendations[:3]:
                if rec.get("reason"):
                    prompt_parts.append(rec["reason"])
                if rec.get("situation"):
                    atmosphere = rec["situation"].split(',')[0]  # 첫 번째 상황만 사용
                    prompt_parts.append(atmosphere)

            # 이미지 프롬프트 구성
            image_prompt = (
                "Create a professional perfume advertisement featuring:\n"
                f"{'. '.join(prompt_parts)}.\n"
                "Requirements:\n"
                "- Elegant and luxurious composition\n"
                "- Soft, diffused lighting\n"
                "- High-end product photography style\n"
                "- Crystal clear perfume bottles\n"
                "- Premium background with subtle textures\n"
                "- Professional color grading\n"
            )

            logger.info(f"📸 이미지 생성 시작\n프롬프트: {image_prompt}")

            # ✅ 이미지 저장 경로 지정 (generated_images 폴더)
            save_directory = "generated_images"
            os.makedirs(save_directory, exist_ok=True)  # 폴더가 없으면 생성

            try:
                image_result = self.image_service.generate_image(image_prompt)

                if not image_result:
                    raise ValueError("❌ 이미지 생성 결과가 비어있습니다")

                if not isinstance(image_result, dict):
                    raise ValueError(f"❌ 잘못된 이미지 결과 형식: {type(image_result)}")

                raw_output_path = image_result.get("output_path")
                if not raw_output_path:
                    raise ValueError("❌ 이미지 경로가 없습니다")

                filename = os.path.basename(raw_output_path)
                output_path = os.path.join(save_directory, filename)

                if os.path.exists(raw_output_path):
                    os.rename(raw_output_path, output_path)

                # ✅ `response["image_path"]`에 최종 경로 설정
                state["response"]["image_path"] = output_path
                logger.info(f"✅ 이미지 생성 완료: {output_path}")

            except Exception as img_err:
                logger.error(f"🚨 이미지 생성 실패: {img_err}")
                state["response"]["image_path"] = None

            state["next_node"] = "end"
            return state

        except Exception as e:
            logger.error(f"❌ 이미지 생성 오류: {e}")
            state["error"] = str(e)
            state["next_node"] = "error_handler"
            return state

    def chat_handler(self, state: PerfumeState) -> PerfumeState:
        try:
            user_input = state["user_input"]
            logger.info(f"💬 대화 응답 생성 시작 - 입력: {user_input}")

            state["response"] = self.llm_service.generate_chat_response(user_input)
            logger.info(f"✅ 대화 응답 생성 완료: {state['response']}")

        except Exception as e:
            logger.error(f"🚨 대화 응답 생성 실패: {e}")
            state["response"] = "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다."

        return state
    
    def image_generator(self, state: PerfumeState) -> PerfumeState:
        """추천된 향수 기반으로 이미지 생성"""
        try:
            recommendations = state.get("recommendations", [])
            if not recommendations:
                logger.warning("⚠️ 추천 결과가 없어 이미지를 생성할 수 없습니다")
                state["image_path"] = None
                state["next_node"] = "end"
                return state

            # 1. Translate Korean text to English
            try:
                translated_parts = []
                for rec in recommendations[:3]:
                    # Translate name and brand
                    name = rec.get('name', '')
                    brand = rec.get('brand', '')
                    perfume_info = f"{name} by {brand}" if brand else name

                    # Translate reason and situation
                    reason = rec.get('reason', '')
                    situation = rec.get('situation', '').split(',')[0] if rec.get('situation') else ''

                    translation_prompt = (
                        "Translate the following Korean text to English, keeping perfume names unchanged:\n"
                        f"1. {perfume_info}\n"
                        f"2. {reason}\n"
                        f"3. {situation}"
                    )
                    
                    translated_text = self.gpt_client.generate_response(translation_prompt).strip()
                    translated_lines = translated_text.split('\n')
                    
                    if len(translated_lines) >= 3:
                        translated_parts.extend(translated_lines[1:])  # Skip perfume name translation

                logger.info("✅ 텍스트 번역 완료")

                # 2. Generate image prompt
                image_prompt = (
                    "Create a professional perfume advertisement featuring:\n"
                    f"{'. '.join(translated_parts)}.\n"
                    "Requirements:\n"
                    "- Elegant and luxurious composition\n"
                    "- Soft, diffused lighting\n"
                    "- High-end product photography style\n"
                    "- Crystal clear perfume bottles\n"
                    "- Premium background with subtle textures\n"
                    "- Professional color grading"
                )

                logger.info(f"📸 이미지 생성 시작\n프롬프트: {image_prompt}")

                # 3. Generate image
                save_directory = "generated_images"
                os.makedirs(save_directory, exist_ok=True)

                image_result = self.image_service.generate_image(image_prompt)
                if not image_result or not isinstance(image_result, dict):
                    raise ValueError("이미지 생성 결과가 유효하지 않습니다")

                output_path = image_result.get("output_path")
                if not output_path:
                    raise ValueError("이미지 경로가 없습니다")

                # 4. Save and update state
                filename = os.path.basename(output_path)
                final_path = os.path.join(save_directory, filename)

                if os.path.exists(output_path):
                    os.rename(output_path, final_path)

                state["image_path"] = final_path
                logger.info(f"✅ 이미지 생성 완료: {final_path}")

                if isinstance(state.get("response"), dict):
                    state["response"]["image_path"] = final_path

            except Exception as img_err:
                logger.error(f"🚨 이미지 생성 상세 오류: {img_err}")
                state["image_path"] = None

            state["next_node"] = "end"
            return state

        except Exception as e:
            logger.error(f"❌ 이미지 생성 처리 실패: {str(e)}")
            state["image_path"] = None
            state["next_node"] = "end"
            return state

    def generate_chat_response(self, state: PerfumeState) -> PerfumeState:
        try:
            user_input = state["user_input"]
            logger.info(f"💬 대화 응답 생성 시작 - 입력: {user_input}")

            chat_prompt = (
                "당신은 향수 전문가입니다. 다음 요청에 친절하고 전문적으로 답변해주세요.\n"
                "반드시 한국어로 답변하세요.\n\n"
                f"사용자: {user_input}"
            )

            response = self.gpt_client.generate_response(chat_prompt)
            state["response"] = response.strip()
            state["next_node"] = None  # ✅ 대화 종료

        except Exception as e:
            logger.error(f"🚨 대화 응답 생성 실패: {e}")
            state["response"] = "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다."
            state["next_node"] = None

        return state

    
    def run(self, user_input: str) -> dict:
        """그래프 실행 및 결과 반환"""
        try:
            logger.info(f"🔄 서비스 실행 시작 - 입력: {user_input}")
            
            # 초기 상태 설정
            initial_state = {
                "user_input": user_input,
                "processed_input": None,
                "next_node": None,
                "recommendations": None,
                "spices": None,
                "image_path": None,
                "image_description": None,
                "response": None,
                "line_id": None,
                "translated_input": None,
                "error": None
            }

            # 그래프 컴파일 및 실행
            compiled_graph = self.graph.compile()
            result = compiled_graph.invoke(initial_state)
            
            # 결과 검증 및 반환
            if result.get("error"):
                logger.error(f"❌ 오류 발생: {result['error']}")
                return {
                    "status": "error",
                    "message": result["error"],
                    "recommendations": []
                }
                
            logger.info("✅ 서비스 실행 완료")
            return {
                "status": "success",
                "recommendations": result.get("recommendations", []),
                "response": result.get("response"),
                "image_path": result.get("image_path")
            }

        except Exception as e:
            logger.error(f"❌ 서비스 실행 오류: {e}")
            return {
                "status": "error",
                "message": "서비스 실행 중 오류가 발생했습니다",
                "recommendations": []
            }
