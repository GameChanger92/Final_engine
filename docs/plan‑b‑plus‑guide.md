## **Plan B+ Implementation Guide**

### **"GitHub Codespaces + Copilot Workspace"로 Final Engine 200‑편 자동 제작하기**

### **0. 개요**

  ---------------------------------------------------------------------------
  **항목**   **내용**
  ---------- ----------------------------------------------------------------
  **목적**   코딩 지식 없이도 *Final Engine*을 완전 구축‑운영하여 200 편 이상
             웹소설을 안정적으로 생성

  **핵심     **GitHub Codespaces** ― 브라우저‑IDE·클라우드 VM**GitHub
  툴**       Copilot Workspace (코딩 Agent)** ― Issue 지시만으로 PR·테스트
             자동 수행

  **사용     "템플릿 포크 → Codespace 1‑클릭 → Issue 한 줄 작성 → PR Merge
  방식**     버튼"만 반복
  ---------------------------------------------------------------------------

### **1. 사전 준비**

  --------------------------------------------------------------------------------------------------------------------------------------------------------------
  **준비물**     **설명**
  -------------- -----------------------------------------------------------------------------------------------------------------------------------------------
  GitHub 개인    Free 플랜이면 **월 120 core‑hour, 15 GB** Codespaces 무료 사용 가능
  계정           ([[docs.github.com]{.underline}](https://docs.github.com/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces))

  Copilot        Copilot coding agent(Workspace) 기능이 Pro+/Enterprise에서 활성화
  Pro 이상       ([[docs.github.com]{.underline}](https://docs.github.com/en/copilot/using-github-copilot/coding-agent/about-assigning-tasks-to-copilot))

  LLM API 키     .env → OPENAI_API_KEY 또는 GEMINI_API_KEY 입력
  --------------------------------------------------------------------------------------------------------------------------------------------------------------

### **2. 템플릿 리포지토리 구조**

📦 final‑engine‑template/

├─ docs/ \<\-- 기본 문서 4종 (Master Guide·Roadmap·Day‑Guide·Report)

├─ src/ \<\-- Final Engine 파이썬 패키지

├─ tests/ \<\-- Guard 8종 + long‑run SIM 테스트

├─ .github/

│ ├─ workflows/ \<\-- pytest, 200‑ep SIM, cron KPI 체크

│ └─ copilot.yml \<\-- Copilot Workspace Action

├─ .devcontainer/ \<\-- dev‑container 설정 (Python 3.11, Poetry 등)

└─ requirements.txt

> **TIP** : dev‑container가 포함돼 있으므로 Codespaces가 VM을 즉시
> 구성해 준다.

### **3. 최초 셋업 (클릭 ≒ 3 회)**

1.  **템플릿 포크**\
    > GitHub에서 Use this template 클릭 → 새 리포 생성.
    > ([[docs.github.com]{.underline}](https://docs.github.com/codespaces/getting-started/quickstart))

2.  **Codespace 열기**\
    > Code ▸ Create Codespace 클릭 → 4‑core/8 GB VM이 자동 부팅.

3.  **Copilot Agent 켜기** (처음 1회)\
    > 리포 설정 ▸ Settings ▸ Integrations ▸ Copilot coding agent 활성화.

4.  **[Tip: 프로젝트 초기화 예시 (터미널)]{.mark}**

> [소설의 뼈대가 되는 \'앵커\'를 먼저 로드하여 프로젝트를
> 시작합니다.]{.mark}
>
> \# 하이브리드 방식 초기화
>
> python -m src.outline_manager init \--eps 240 \--arc 0 \--load-anchors
> data/my_novel/anchors.json

### **4. 일일 개발 루프**

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **단계**       **당신이 할 일**            **Copilot / CI 자동 작업**
  -------------- --------------------------- ------------------------------------------------------------------------------------------------------------------------------------------
  **① Day Guide  새 Issue 템플릿 선택, 제목: --
  Issue 작성**   Day 07 -- \"장면 추출기     
                 개선\" 한 줄 기입, 라벨     
                 ai-task 지정                

  **② Issue ↔ PR --                          Copilot agent가 코드를 작성하고 **PR 생성 + unit test 포함**
  자동화**                                   ([[docs.github.com]{.underline}](https://docs.github.com/en/copilot/using-github-copilot/coding-agent/about-assigning-tasks-to-copilot))

  **③ PR 검토**  Checks green 확인 후        GitHub Actions가 pytest + **200 ep long‑run SIM** 실행
                 **Merge** 버튼 클릭         

  **④            Codespace 상단              최신 main 브랜치를 즉시 호스팅
  배포/실행**    Open in Browser 클릭 → REST 
                 Demo 페이지 확인            

  **⑤ Day        (선택) 결과·비용 요약 3줄   PR 자동 코멘트에 로그·통계 첨부
  Report**       작성                        
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> **총 타이핑** : Issue 제목 1줄.\
> **총 클릭** : PR Merge, Open in Browser = 2회.

### **5. 대규모 시뮬레이션 실행**

Codespace 터미널에서 단 한 줄:

python -m src.run_novel run \--project-id novel_A \--episodes 240
\--workers 4 \--max-retries 2

-   dev‑container에 Python·Poetry·GPU 없는 CPU 최적화 패키지 사전 설치.

-   **Note:** \--project-id novel_A 플래그는 생성할 작품을 지정합니다.
    > 다른 작품을 생성하려면 이 ID만 변경하면 됩니다.

-   실패 시 \--max-retries 로 최대 2회 재시도 후 로그 저장.

### **6. 품질 보증 & 자동 복구**

-   **Guard 8종** (문체 일관성, 금지어, 길이, 비용 등) + **long‑run
    > SIM** 스위트가 CI 파이프라인에 내장.

-   테스트 실패 시 Copilot agent가 **수정 PR**을 자동 제출 → 당신은 다시
    > Merge만.
    > ([[docs.github.com]{.underline}](https://docs.github.com/en/copilot/using-github-copilot/coding-agent/about-assigning-tasks-to-copilot))

### **7. 비용·쿼터 관리**

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **항목**        **무료 할당량**     **초과 시 요금 (2025‑06 기준)**
  --------------- ------------------- -----------------------------------------------------------------------------------------------------------------------------------------------
  Codespaces      **120 core‑h/월**   2‑core: \$0.18/h, 4‑core: \$0.36/h ...
  컴퓨트          (Free)              ([[docs.github.com]{.underline}](https://docs.github.com/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces))

  Codespaces      15 GB‑month (Free)  \$0.07/GB‑month
  저장소                              

  Copilot Agent   Copilot Pro 월 \$10 GitHub Actions 분당 무료 (Public)
                  (개인)              
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

-   Settings ▸ Codespaces ▸ Idle timeout을 30→10 분으로 줄여 불필요한
    > core‑h 절감 가능
    > ([[docs.github.com]{.underline}](https://docs.github.com/enterprise-cloud%40latest/codespaces/troubleshooting/troubleshooting-included-usage?utm_source=chatgpt.com)).

### **8. 확장 & 운영 팁**

  -----------------------------------------------------------------------
  **필요**       **간단한 방법**
  -------------- --------------------------------------------------------
  **리소스       Codespace 메뉴 ▸ **Machine type 4‑core → 8‑core** 전환
  부족**         

  **야간 KPI     .github/workflows/nightly.yml -- cron(1:00 UTC)으로
  모니터링**     300 ep SIM 실행

  **비용 한도**  Settings ▸ Codespaces ▸ Spending limits = \$0 설정 (초과
                 사용 차단)

  **RAG 메모리   /vector_db/ 폴더와 supabase.yml 추가 후 Copilot Issue:
  추가**         *"임베딩 캐시 기능 넣어줘"*
  -----------------------------------------------------------------------

### **9. 자주 묻는 질문**

  -----------------------------------------------------------------------
  **Q**              **A**
  ------------------ ----------------------------------------------------
  **Codespaces       리포 Public 전환 → Actions·Codespaces 무료 할당 두
  시간이 모자라요**  배.

  **Copilot이 PR을   \(1\) Issue에 ai-task 라벨 확인, (2) Copilot Agent
  안 올려요**        활성화 상태 점검, (3) Repo가 Private+Free라면 Pro
                     플랜 필요.

  **테스트 로그가    pytest -q 옵션으로 요약 출력, 자세한 로그는
  너무 길어요**      \--log-level=INFO 로 별도 파일 보관.
  -----------------------------------------------------------------------

## **한눈에 보는 Plan B+ 장점**

  -----------------------------------------------------------------------
  **✔ 버튼 3개만 누르면 완전       **✔ 4‑core/8 GB VM으로 200 ep
  자동화**                         시뮬레이션 안정 통과**
  -------------------------------- --------------------------------------
  ✔ 문서 4종 =                     ✔ 실패 시 Copilot이 스스로 수정 PR
  사양·계획·가이드·보고서 올‑인‑원 제출

  -----------------------------------------------------------------------

**→ 위 절차 그대로 따르면, 개발 지식 없이도 Final Engine이 완성·배포되고
200‑편 이상을 오류 없이 생산합니다. Happy publishing!**
