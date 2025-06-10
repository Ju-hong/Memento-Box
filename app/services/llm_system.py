from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from services.image_analyzer import ImageAnalyzer
from services.chat_system import ChatSystem
from services.voice_system import VoiceSystem
from services.story_and_report_system import StoryGenerator
import os
import uuid

from core.config import settings
from db.database import get_db

@dataclass
class SessionData:
    conversation_id: str
    photo_path: Optional[str] = None
    turns: List[dict] = field(default_factory=list)  # {"question": ..., "answer": ..., "timestamp": ...}
    created_at: datetime = field(default_factory=datetime.now)

class OptimizedDementiaSystem:
    """최적화된 치매 진단 시스템"""
    
    def __init__(self):
        self.sessions: dict[str, SessionData] = {}  # 여기 key가 conv_id
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")

        self.image_analyzer = ImageAnalyzer()
        self.chat_system = ChatSystem()
        self.voice_system = VoiceSystem() if self.speech_key else None
        self.story_generator = StoryGenerator(self.chat_system)
    
    def analyze_and_start_conversation(self, image_path):
        """이미지 분석 및 대화 시작"""
        if not os.path.exists(image_path):
            return None
        
        # 1. conversation_id 생성
        conversation_id = str(uuid.uuid4())

        # 이미지 분석
        analysis_result = self.image_analyzer.analyze_image(image_path)
        if not analysis_result:
            return None
        
        # 대화 설정
        self.chat_system.setup_conversation_context(analysis_result)
    
        # 첫 질문 생성
        initial_question = self.chat_system.generate_initial_question()
        
        return conversation_id, initial_question
    
    # def generate_complete_analysis(self, image_path):
    #     """완전한 분석 생성"""
    #     print("\n📊 종합 분석 결과 생성 중...")
        
    #     # 1. 대화 기록 저장 (새로운 폴더 구조)
    #     conversation_file, analysis_file = self.story_generator.save_conversation_to_file(image_path)
        
    #     # 2. 추억 스토리 생성
    #     story, story_file = self.story_generator.generate_story_from_conversation(image_path)
        
    #     # 3. 콘솔에 요약 출력
    #     summary = self.story_generator.save_conversation_summary()
    #     print(summary)
        
    #     # 4. 스토리 출력
    #     if story:
    #         print(f"\n{'='*50}")
    #         print("📖 생성된 추억 이야기")
    #         print(f"{'='*50}")
    #         print(story)
    #         print(f"{'='*50}")
        
    #     return {
    #         'conversation_file': conversation_file,
    #         'analysis_file': analysis_file,
    #         'story_file': story_file,
    #         'story_content': story,
    #         'summary': summary,
    #         'conversation_id': self.story_generator.conversation_id
    #     }

    def generate_complete_analysis_from_turns(self, turns, conversation_id):
        """Turn 데이터로부터 완전한 분석 생성"""
        print("\n📊 Turn 데이터 기반 종합 분석 결과 생성 중...")
        
        # Turn 데이터를 ConversationTurn 형태로 변환
        from services.chat_system import ConversationTurn
        conversation_turns = []
        
        for turn in turns:
            if turn.turn and isinstance(turn.turn, dict):
                question = turn.turn.get('q_text', '')
                answer = turn.turn.get('a_text', '')
                
                # 질문이 있고, 답변이 null이 아닌 경우만 포함 (빈 문자열도 포함)
                if question and answer is not None:
                    conversation_turn = ConversationTurn(
                        question=question,
                        answer=answer,
                        timestamp=turn.recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
                        answer_length=len(answer.strip()) if answer else 0,
                        audio_file=turn.turn.get('a_voice', '') or ''
                    )
                    conversation_turns.append(conversation_turn)
        
        if not conversation_turns:
            return {
                'error': 'No valid conversation turns found',
                'conversation_id': str(conversation_id)
            }
        
        # StoryGenerator의 chat_system에 conversation_turns 설정
        self.story_generator.chat_system.conversation_turns = conversation_turns
        self.story_generator.conversation_id = str(conversation_id)
        
        # 1. 추억 스토리 생성 (Turn 데이터 직접 사용)
        story = self.story_generator.generate_story_from_turns(conversation_turns)
        
        # 2. 대화 기록 저장
        conversation_file, analysis_file = self.story_generator.save_conversation_to_file_from_turns(conversation_turns, str(conversation_id))
        
        # 3. 스토리 파일 저장
        story_file = None
        if story:
            story_dir = "story_telling"
            os.makedirs(story_dir, exist_ok=True)
            story_file = os.path.join(story_dir, f"{conversation_id}_story.txt")
            
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(story)
        
        # 4. 요약 생성
        summary = self.story_generator.save_conversation_summary()
        print(summary)
        
        # 5. 스토리 출력
        if story:
            print(f"\n{'='*50}")
            print("📖 생성된 추억 이야기")
            print(f"{'='*50}")
            print(story)
            print(f"{'='*50}")
        
        return {
            'conversation_file': conversation_file,
            'analysis_file': analysis_file,
            'story_file': story_file,
            'story_content': story,
            'summary': summary,
            'conversation_id': str(conversation_id),
            'turns_processed': len(conversation_turns)
        }
    
    def _run_conversation(self, initial_question, is_voice=False):
        """대화 루프 실행 (음성/텍스트 공통)"""
        
        # if is_voice and self.voice_system:
        #     welcome_msg = "안녕하세요. 사진을 보며 대화해요."
        #     print(f"🤖 {welcome_msg}")
        #     self.voice_system.synthesize_speech(welcome_msg)
            
        #     print(f"🤖 {initial_question}")
        #     self.voice_system.synthesize_speech(initial_question)
        # else:
        #     print(f"🤖 {initial_question}")
        
        # conversation_type = "음성" if is_voice else "텍스트"
        # print(f"\n" + "="*40)
        # print(f"{'🎙️' if is_voice else '💬'} {conversation_type} 대화 시작!")
        # print(f"💡 {'종료라고 말하면' if is_voice else 'exit 또는 종료를 입력하면'} 끝납니다")
        # print("="*40)
        
        # 대답
        should_end = False
        if is_voice and self.voice_system:
            print("🎙️ 말씀해 주세요...")
            # 음성 녹음 시작
            self.chat_system.start_recording()
            user_input = self.voice_system.transcribe_speech()
            # 음성 녹음 중지
            audio_path = self.chat_system.stop_recording()
            
            if user_input == "종료":
                end_msg = "대화를 마치겠습니다. 감사합니다."
                print(f"🤖 {end_msg}")
                self.voice_system.synthesize_speech(end_msg)
                should_end = True
        else:
            user_input = input("\n👤 답변: ").strip()
            if user_input.lower() in ['exit', '종료', 'quit', '그만']:
                print("대화를 종료합니다.")
                should_end = True

        return user_input, audio_path, should_end

    def check_end_keywords(self, user_answer):
        """사용자 답변에서 종료 키워드 확인"""
        if not user_answer:
            return False
            
        # 종료 키워드 목록
        end_keywords = ['종료', 'exit', 'quit', 'q', '그만', '끝', '종료해줘', '그만해', '멈춰']
        
        user_answer_lower = user_answer.lower().strip()
        
        # 정확한 매칭 또는 포함 여부 확인
        for keyword in end_keywords:
            if keyword in user_answer_lower:
                print(f"🔚 종료 키워드 감지: '{keyword}' in '{user_answer}'")
                return True
        
        return False
    
    def generate_next_question(self, previous_question, user_answer):
        """사용자 답변을 바탕으로 다음 질문 생성"""
        try:
            # 대화 컨텍스트에 사용자 답변 추가
            self.chat_system.conversation_history.append({
                "role": "user", 
                "content": user_answer
            })
            
            # 다음 질문 생성을 위한 프롬프트
            next_question_prompt = """이전 질문에 대한 어르신의 답변을 듣고, 자연스럽게 대화를 이어갈 다음 질문을 생성해주세요. 
다음 원칙을 지켜주세요:
1. 50자 이내로 간결하게
2. 어르신의 답변에 공감하는 표현 포함
3. 사진과 관련된 추가 질문
4. 따뜻하고 친근한 어조
5. 한 번에 하나의 질문만

어르신의 답변에 맞춰 자연스럽게 대화를 이어가는 질문을 해주세요."""

            response = self.chat_system.client.chat.completions.create(
                model=self.chat_system.deployment,
                messages=self.chat_system.conversation_history + [
                    {"role": "user", "content": next_question_prompt}
                ],
                max_tokens=512,
                temperature=0.8
            )
            
            next_question = response.choices[0].message.content.strip()
            
            # 생성된 질문을 대화 히스토리에 추가
            self.chat_system.conversation_history.append({
                "role": "assistant", 
                "content": next_question
            })
            
            # 토큰 수 업데이트
            user_tokens = len(self.chat_system.tokenizer.encode(user_answer))
            question_tokens = len(self.chat_system.tokenizer.encode(next_question))
            self.chat_system.token_count += user_tokens + question_tokens
            
            # 토큰 제한 확인
            if self.chat_system.token_count > int(self.chat_system.max_tokens):
                return "대화 시간이 다 되었어요. 오늘도 즐거운 시간이었습니다. 감사합니다."
            
            return next_question
            
        except Exception as e:
            print(f"❌ 다음 질문 생성 중 오류: {str(e)}")
            return "계속해서 이야기를 나눠볼까요?"

    def one_chat_about_image(self, user_query, with_audio=False):
        """대화 처리"""
        user_tokens = len(self.tokenizer.encode(user_query))
        
        # 음성 녹음 시작 (if requested)
        audio_file = None
        if with_audio:
            self.start_recording()
        
        # 대화 턴 저장
        if self.last_question:
            # 음성 녹음 중지 및 파일 저장 (if recording)
            if with_audio:
                audio_file = self.stop_recording()
            
            # conversation_turn = ConversationTurn(
            #     question=self.last_question,
            #     answer=user_query,
            #     timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            #     answer_length=len(user_query.strip()),
            #     audio_file=audio_file if audio_file else ""
            # )
            # self.conversation_turns.append(conversation_turn)
            
        
        self.conversation_history.append({"role": "user", "content": user_query})
        self.token_count += user_tokens
        
        # 토큰 제한 확인
        if self.token_count > self.max_tokens:
            answer = "대화 시간이 다 되었어요. 수고하셨습니다."
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer, True
        
        # AI 응답 생성
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=self.conversation_history,
            max_tokens=1024,
            temperature=0.7
        )
        answer = response.choices[0].message.content
        
        self.conversation_history.append({"role": "assistant", "content": answer})
        self.token_count += len(self.tokenizer.encode(answer))
        self.last_question = answer
        
        if self.token_count > self.max_tokens:
            return answer, True
        
        return answer, False
    
    def voice_conversation(self, image_path):
        """음성 대화 실행"""
        if not self.voice_system:
            return None
        return self._run_conversation_loop(image_path, is_voice=True)
    
    # def text_conversation(self, image_path):
    #     """텍스트 대화 실행"""
    #     return self._run_conversation_loop(image_path, is_voice=False)