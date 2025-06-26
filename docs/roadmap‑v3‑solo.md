### **Development Roadmap v3-SOLO 🗺️ (하이브리드 엔진, 21일 완성 코스)**

**목표:** 1인 개발자가 21일 안에 **핵심 사건(앵커)은 고정**시키고 **세부
전개는 AI가 채우는** 하이브리드 방식의 \'Final Engine\'을 완성하고,
240편 분량의 첫 시즌을 생성할 수 있도록 단계별로 안내합니다.

#### **🏁 Week-0 : 준비 & 마인드셋 (D-7 \~ D-1)**

  ---------------------------------------------------------------------------
  Day               목표       해야 할 일                   체크포인트
  ----------------- ---------- ---------------------------- -----------------
  D-7               개발 환경  • VS Code 설치\<br\>• Python python \--version
                    첫 세팅    3.11 설치\<br\>• Git +       = 3.11.x
                               GitHub 계정 생성             

  D-6               리포 포크  • git clone 템플릿           프롬프트에 (env)
                    & 가상환경 저장소\<br\>• python -m venv 표시
                               env\<br\>• source            
                               env/bin/activate             

  D-5               필수       • pip install -r             pip list에 openai
                    패키지     requirements.txt\<br\>• VS   등 확인
                    설치       Code Python 인터프리터 연결  

  D-4               Git 기본   • git commit, push, pull     첫 커밋 init-env
                    익히기     실습\<br\>• .gitignore       
                               업데이트                     

  D-3               Typing     • python - \<\<EOF \... EOF  hello_engine.py
                    기초       로 "Hello Engine"            실행 성공
                               출력\<br\>• f-string, 함수,  
                               클래스 맛보기                

  D-2               LLM API 키 • OpenAI / Gemini 키         터미널에 모델
                    설정       발급\<br\>• .env 파일에      응답 출력
                               저장\<br\>• 간단한 Test 호출 
                               (curl 예제)                  

  D-1               로드맵 &   • 본 문서 한 번 전체         체크리스트 100%
                    툴 숙지    읽기\<br\>• Q&A 메모 작성    읽음
                               (모르는 용어)                

  *Tip: 설치                                                
  오류·용어가                                               
  막히면 "오류                                              
  메시지 + 전체                                             
  스택트레이스" 를                                          
  복사해 GPT에게                                            
  질문하세요.*                                              
  ---------------------------------------------------------------------------

#### **🗂️ Week-1 : Core Skeleton (D1 \~ D7)**

  ---------------------------------------------------------------------------
  Day   목표        상세 작업                           완성 기준
  ----- ----------- ----------------------------------- ---------------------
  D1    Repo        ① src/ 폴더·\_\_init\_\_.py\<br\>②  tree 명령에 구조 출력
        Bootstrap   폴더 구조(data/, tests/ 등) 생성    

  D2    Outline     • outline_manager.py 생성\<br\>•    python -m
        Manager     Typer CLI 등록 init 커맨드\<br\>•   src.outline_manager
                    /data/arcs.json 더미 파일 생성      init \--eps 10 실행
                                                        성공

  D3    Beat        • beat_planner.py 생성\<br\>• 함수  pytest -q 통과
        Planner     make_beats(arc_json) 구현\<br\>•    
                    PyTest 3개 작성                     
                    (tests/unit/test_beat_planner.py)   

  D4    Scene Maker • scene_maker.py 생성\<br\>• 10줄   python -m
                    ScenePoint 템플릿 추가\<br\>• Unit  src.scene_maker run
                    test 3개                            \--beat-id TEST 정상
                                                        출력

  D5    Context     • context_builder.py에서 "임시"     테스트: 1 비트 → 10
        Builder     프롬프트 조립\<br\>• LLM 호출 없이  씬 → ctx 출력
        Stub        문자열만 반환                       

  D6    Draft       • draft_generator.py 에             테스트: Draft 1개
        Generator   "PLACEHOLDER TEXT" 반환 함수\<br\>• 생성
        Stub        CLI run_draft 추가                  

  D7    첫 통합     • Arc 1 → Beat → Scene → Draft      화면에 Draft 10줄
        실행        Stubs 순서 확인                     표시
  ---------------------------------------------------------------------------

#### **🛡️ Week-2 : Guard Phase 1 (D8 \~ D14)**

  ------------------------------------------------------------------------
  Day   Guard           작업                            테스트
  ----- --------------- ------------------------------- ------------------
  D8    Lexi Guard      • lexi_guard.py 코딩\<br\>•     5 샘플 통과/실패
                        textstat 이용, TTR 계산         케이스

  D9    Emotion Guard   • 감정 분류 API(예: GPT         Δ\>0.7 시
                        logit_bias) 호출\<br\>• Δ 계산  RetryException
                                                        발생

  D10   Foreshadow      • foreshadow.json 스키마        Unit test: 2 복선
        Scheduler       정의\<br\>• Scheduler: hint→due 자동 추가
                        회차 기록                       

  D11   Schedule Guard  • due 회차에 payoff 없으면 fail 테스트: 미회수 시
                                                        실패

  D12   Immutable +     • immut_guard.py, date_guard.py 캐릭터 나이 변경 →
        Date Guard      구현                            실패 확인

  D13   Rule Guard      • rules.json 패턴 읽어 Regex    "마법 금지" 패턴
                        검사                            테스트

  D14   **Anchor        • anchor_guard.py 코딩\<br\>•   anchor_ep 불일치
        Guard**         anchors.json 스키마 정의        시 실패 확인
  ------------------------------------------------------------------------

#### **⚙️ Week-3 : Guard Phase 2 & Integration (D15 \~ D21)**

  --------------------------------------------------------------------------
  Day   목표              상세 작업                           체크포인트
  ----- ----------------- ----------------------------------- --------------
  D15   **Anchor-driven   • anchors.json 샘플(5개) 수동       앵커 이벤트
        Test**            작성\<br\>• \--enforce-anchors      5개 모두 통과
                          플래그로 실행                       확인

  D16   Pacing Guard      • action/dialog/monolog 비율 계산   비율 편차 ±25%
                                                              검사 성공

  D17   Relation Guard    • relation_matrix.json 읽어         적군↔동료 반전
                          상호관계 검사                       시 실패

  D18   Retry Controller  • retry_controller.py에서 Guard     실패 → 재시도
                          결과 수집 후 재호출                 2회 → 성공

  D19   VectorStore &     • ChromaDB 세팅, ScenePoint 임베딩  10 쿼리 → 결과
        Embedding         저장                                반환

  D20   Context Builder   • LLM 프롬프트에 KG + 벡터 결과     Draft 길이
        완성              끼워넣기                            5,500자↑ 출력

  D21   Draft Generator + • 실제 LLM 호출 · 텍스트            1 Episode
        Editor            수정\<br\>• **1 Episode, 모든 Guard Guard 전부
                          통과**                              통과
  --------------------------------------------------------------------------

#### **(선택) Week-4 : 다작 지원 기능 추가**

  --------------------------------------------------------------------------
  Day   목표   상세 작업                         체크포인트
  ----- ------ --------------------------------- ---------------------------
  D22   다작   • run_novel.py 등 핵심 CLI에      python -m src.run_novel run
        지원   \--project-id 플래그 추가\<br\>•  \--project-id test_A 실행
        기능   데이터 입력 경로를                시,\<br\>outputs/test_A/
        추가   data/{project_id}로 동적          폴더에 결과물이 생성되는지
               분기\<br\>• 결과물 출력 경로를    확인
               outputs/{project_id}로 동적 분기  

  --------------------------------------------------------------------------

#### **✅ 완료 조건 Recap**

1.  pytest를 실행하여 모든 Unit/Integration 테스트 통과.

2.  240편 분량의 시뮬레이션을 주요 오류(e.g., conflict 0) 없이 1회 이상
    > 완주.

3.  개인적인 작업 로그(CHANGELOG.md 등)에 주요 변경사항을 기록.

#### **도움 받을 때 Quick Prompt 예시**

"GPT야, beat_planner.py 12번째 줄 KeyError: \'goal\'가 떠. beats.json
샘플(아래) 붙일게. 왜 오류 나고, 어떻게 고쳐야 해?"\
*오류 메시지·관련 JSON·코드를 모두 복사해 질문하면 해결이 빠릅니다.*

Happy Coding! 혼자서도 3주면 충분히 핵심 기능을 만들 수 있으니 차근차근
진행해 보세요. 🙌
