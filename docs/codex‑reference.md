### **📝 OpenAI Codex 한눈에 보기 (2025 년 6 월 기준)**

  ----------------------------------------------------------------------------------------------------------------------------------------------
  **구분**         **핵심 요약**
  ---------------- -----------------------------------------------------------------------------------------------------------------------------
  **정체**         ChatGPT 사이드바에서 실행되는 **클라우드형 소프트웨어 엔지니어링 에이전트**. 한꺼번에 여러 작업(기능 개발, 버그 수정, 테스트,
                   PR 제안)을 병렬 처리한다. ([[openai.com]{.underline}](https://openai.com/research/index/?utm_source=chatgpt.com))

  **엔진**         **codex-1 모델** --- OpenAI o3를 소프트웨어 전용 RL로 미세조정한 버전. 최대 192 k 토큰 컨텍스트, 테스트 재시도 루프 내장.
                   ([[openai.com]{.underline}](https://openai.com/research/index/release/?utm_source=chatgpt.com))

  **접근**         ChatGPT **Pro·Team·Enterprise** 사용자는 즉시 이용 가능. 2025-06-03 업데이트 후 **Plus** 사용자도 지원. 추가 요금 없이 넉넉한
                   쿼터 제공 뒤 사용량 기반 과금 예정. ([[openai.com]{.underline}](https://openai.com/research/index/?utm_source=chatgpt.com),
                   [[wsj.com]{.underline}](https://www.wsj.com/articles/openai-launches-new-ai-coding-agent-c8dabc60?utm_source=chatgpt.com))

  **작동 방식**    각 작업이 **인터넷이 차단된 독립 컨테이너**에서 실행된다. 컨테이너에는 연결한 GitHub 리포지토리와 사용자가 정의한 개발
                   환경(의존성, 테스트 스크립트 등)이 사전 탑재된다.
                   ([[openai.com]{.underline}](https://openai.com/index/introducing-codex/?utm_source=chatgpt.com),
                   [[openai.com]{.underline}](https://openai.com/index/o3-o4-mini-codex-system-card-addendum/?utm_source=chatgpt.com))

  **인터페이스**   ● **Code** 버튼 → 기능 구현·리팩터·버그픽스 등 수행● **Ask** 버튼 → 코드베이스 Q&A완료 후 커밋·터미널 로그·테스트 결과가 함께
                   제시되어 추적 가능. ([[openai.com]{.underline}](https://openai.com/index/introducing-codex/?utm_source=chatgpt.com))

  **작업 시간**    문제 난이도에 따라 **1 -- 30 분**. 여러 에이전트를 동시에 돌려 병렬 처리할 수 있다.
                   ([[wsj.com]{.underline}](https://www.wsj.com/articles/openai-launches-new-ai-coding-agent-c8dabc60?utm_source=chatgpt.com))

  **AGENTS.md**    리포 내부 안내서(README 비슷).테스트 명령·코딩 규칙·PR 메시지 형식 등을 기재해 두면 Codex 정확도가 크게 향상한다.
                   ([[openai.com]{.underline}](https://openai.com/index/introducing-codex/?utm_source=chatgpt.com))

  **CLI &          로컬 터미널용 **Codex CLI**(오픈소스) 제공. 기본 모델은 **codex-mini-latest** (o4-mini 특화). 저지연 코드 Q&A·편집에 적합하며
  codex-mini**     API 가격은 입력 \$1.50 / 출력 \$6 (100 만 토큰당).
                   ([[openai.com]{.underline}](https://openai.com/research/index/?utm_source=chatgpt.com))

  **안전 장치**    모든 출력에 테스트·로그 인용 포함 → 검증 용이. 악성 코드 요청은 정책에 따라 명확히 거부. 컨테이너 외부 인터넷 접근 기본 차단.
                   ([[openai.com]{.underline}](https://openai.com/index/o3-o4-mini-codex-system-card-addendum/?utm_source=chatgpt.com))

  **제한 사항**    • 이미지·프런트엔드 빌드 아직 미지원• 대규모 리포 초기 클론 시간 소요• 원격 작업 특성상 즉각적 상호 편집보다는 '과제 → 검토'
                   흐름에 최적화. ([[openai.com]{.underline}](https://openai.com/research/index/?utm_source=chatgpt.com))
  ----------------------------------------------------------------------------------------------------------------------------------------------

#### **🔧 빠른 활용 팁 (개발 파이프라인에 Codex 붙이기)**

1.  **GitHub 리포 준비** → 최소 src/, tests/, AGENTS.md 생성.

2.  **ChatGPT 사이드바 » Codex 연결** → OAuth로 리포 선택, 필요 시
    > setup.sh로 의존성 명세.

**첫 과제 예시\
\
** Code: \"src/outline_manager.py 함수별 pytest 작성 후 통과하게 수정\"

3.  

4.  **결과 검토 후 PR 병합** → CI에 codex-check 스텝을 추가해 자동 검증
    > 파이프라인 완성.

#### **📚 REFERENCE**

-   OpenAI Blog "Introducing Codex" (2025-05-16)
    > ([[openai.com]{.underline}](https://openai.com/research/index/?utm_source=chatgpt.com))

-   OpenAI System Card Addendum "Codex" (2025-05)
    > ([[openai.com]{.underline}](https://openai.com/index/o3-o4-mini-codex-system-card-addendum/?utm_source=chatgpt.com))

-   WSJ Tech Coverage (2025-05)
    > ([[wsj.com]{.underline}](https://www.wsj.com/articles/openai-launches-new-ai-coding-agent-c8dabc60?utm_source=chatgpt.com))

-   ChatGPT Enterprise Feature Page (2025-05)
    > ([[openai.com]{.underline}](https://openai.com/chatgpt/enterprise/?utm_source=chatgpt.com))

-   OpenAI Academy "Getting Set Up with Codex" Guide (2025-05)
    > ([[academy.openai.com]{.underline}](https://academy.openai.com/public/blogs/getting-set-up-with-codex-for-chatgpt-enterprise?utm_source=chatgpt.com))
