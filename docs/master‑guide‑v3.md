# **Final Engine Hybrid Master Guide** 

## **📑 Table of Contents**

1.  [[Overview & Goals\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#1)

2.  [[Quick‑Start (Install & CLI)\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#2)

3.  [[System Architecture\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#3)

4.  [[Story Bible Schema\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#4)

5.  [[Quality Guard Layer\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#5)

6.  [[Specification‑Driven Development\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#6)

7.  [[Testing Pyramid & CI\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#7)

8.  [[Runtime Operations\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#8)

9.  [[Deployment & Cost\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#9)

10. [[Appendix A -- CLI Flags\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#A)

11. [[Appendix B -- File Reference\
    > ]{.underline}](https://chatgpt.com/c/68562f08-07b0-8005-8adf-9e9d49370af8?model=o3#B)

## **1. Overview & Goals**

  -----------------------------------------------------------------------
  **Metric**                      **Target**
  ------------------------------- ---------------------------------------
  Episodes                        250--300 in \< 8 h

  OOC / World‑rule conflicts      ≤ 2 %

  Emotion Jump (Δ)                ≤ 0.7

  Foreshadow Resolution           100 % by due ep

  Cost                            ≤ \$0.13 / ep

  Hardware                        8‑core CPU, 16 GB RAM, 50 GB disk
  -----------------------------------------------------------------------

### **1.1 High‑Level Flow**

Outline → Beat → Scene 10 → Draft → Edit → Guard → (Retry) → Publish
(per episode) with sliding memory & KG retrieval.

## **2. Quick‑Start**

### **2.1 Environment**

python -m venv env && source env/bin/activate

pip install -r requirements.txt

### **2.2 Key Packages**

openai · chromadb · typer · httpx · tenacity · pydantic · pytest ·
great_expectations · ruff · pandas · textstat · transformers

### **2.3 Example Commands**

\# Init 6 arcs / 240 episodes\\python -m src.outline_manager init \--eps
240 \--arc 6 \--genre battle

\# One‑Night Finish (313 eps)

python -m src.run_novel run \\

\--episodes 313 \--workers 4 \--max-retries 2 \\

\--use-lexi \--use-emotion \--use-foreshadow \\

\--use-pacing \--use-immut \--use-date \--use-rule \--use-relation \\

\--stop-on-fail foreshadow

## **3. System Architecture (20 Modules)**

  -----------------------------------------------------------------------
  **Layer**    **Module(s)**                          **Purpose**
  ------------ -------------------------------------- -------------------
  **Core       run_novel, outline_manager,            Orchestration, LLM
  (12)**       beat_planner, scene_maker,             calls, embeddings,
               context_builder, draft_generator,      logging
               editor_agent, retry_controller,        
               VectorStore, Logger, core_guard,       
               plugins/\*                             

  **Quality    lexi_guard.py, emotion_guard.py,       Guard checks
  Plugins      schedule_guard.py, pacing_guard.py,    
  (8)**        relation_guard.py, immut_guard.py,     
               date_guard.py, rule_guard.py           
  -----------------------------------------------------------------------

> **Execution Loop:** Draft → Guard_i → (Retry_i) until all pass.

## **4. Story Bible Schema (JSON)**

  -----------------------------------------------------------------------
  **File**                **Key Fields (example)**
  ----------------------- -----------------------------------------------
  arcs.json               {id, goal, start_ep, end_ep}

  beats.json              {id, arc, goal}

  scene_points.json       {id, beat, desc}

  anchors.json            {id, goal, anchor_ep}

  characters.json         {id, role,
                          immutable:\[\"age\",\"birthplace\"\]}

  foreshadow.json         {id, hint, introduced, due, payoff}

  rules.json              {id, pattern, message}

  relation_matrix.json    {mc:{heir:\"ally\", uncle:\"enemy\"}}
  -----------------------------------------------------------------------

## **5. Quality Guard Layer**

  ---------------------------------------------------------------------------
  **Metric**         **Threshold**                           **Guard**
  ------------------ --------------------------------------- ----------------
  OOC / clash        ≤ 2 %                                   core_guard

  Beat Usage         90 ± 10 %                               beat_guard

  TTR                \< 0.17 or 3‑gram dup \> 0.06 → retry   lexi_guard

  Emotion Jump       Δ \> 0.7 → fail                         emotion_guard

  Foreshadow         payoff null @ due → fail                schedule_guard

  Pacing Bias        action/dialog/monolog dev \> 25 % →     pacing_guard
                     retry                                   

  Immutable Breach   any change → fail                       immut_guard

  Date Backstep      new date \< prev → fail                 date_guard

  Rule Violation     regex match → fail                      rule_guard

  Relation Flip      ally/enemy inversion → fail             relation_guard

  Anchor Compliance  anchor_ep [**±1 에** goal **미등장 →    anchor_guard
                     fail**]{.mark}                          
  ---------------------------------------------------------------------------

## **6. Specification‑Driven Development**

1.  **Functional Spec (specs/engine.md)** -- KPI 한 줄 선언.

2.  **Machine Contracts (contracts/\*.yaml)** --
    > KPI→PyTest/Great‑Expectations 매핑.

3.  **Fallback Policy (policies/fallback.md)** -- Guard 3연속 실패 시
    > 롤백·알림.

## **7. Testing Pyramid & CI**

┌──────────────┐ [(주요 기능 개발 완료 후)]{.mark}

│ Long‑run SIM │

├──────────────┤

│ Integration │ [(모듈 간 연동 테스트 시)]{.mark}

├──────────────┤

│ Unit/Guard │ [(코드 수정 시 수시로)]{.mark}

└──────────────┘

-   **Unit/Guard:** 2 000+ snippets.

-   **Integration:** 3‑arc seeds.

-   **Long‑run:** pytest tests/longrun \... ; pass = conflict 0,
    > rating ≥ 3.8/5, cost ≤ 110 %.

## **8. Runtime Operations**

1.  **Checkpoint & Resume** -- state.json 매 에피소드 저장.

2.  **log_watch.py** -- eps/min·비용·ETA 출력, cost \>\$45 경고.

3.  **drift_monitor.py** -- 톤 z‑score 10화마다 체크.

4.  **Human‑in‑loop** -- Guard 3x 실패 시 **[터미널에 알림 후
    > 대기.]{.mark}**

## **9. Deployment & Cost**

  -----------------------------------------------------------------------
  **Cloud**                        **API        **Expected Cost
                                   Scope**      (250 ep)**
  -------------------------------- ------------ -------------------------
  OpenAI GPT‑4o‑2025‑03‑25         90 k ctx     \$32--38

  Gemini 2.5 Pro                   1 Mi ctx     \$25--30

  Rate limit: RPM \< 60;                        
  workers 4.                                    
  -----------------------------------------------------------------------

## **Appendix A -- CLI Flags**

  -----------------------------------------------------------------------
  **Flag**                 **Description**
  ------------------------ ----------------------------------------------
  \--episodes              total episode count

  \--enforce-anchors       Toggles the Anchor Guard on/off

  \--anchors-file          Path to the anchors.json file

  \--workers               concurrent processes

  \--max-retries           tries per Guard fail

  \--stop-on-fail          abort on first fail of guard

  \--use-\*                toggle individual guards
  -----------------------------------------------------------------------

## **Appendix B -- File Reference**

repo/

├ data/ \# Story Bible JSONs

├ specs/engine.md \# KPI statements

├ contracts/ \# KPI → tests

├ policies/ \# runtime fallback rules

├ tests/ \# unit → longrun

├ src/ \# engine code

└ .github/workflows/ \# CI

**10. 다작 지원 모드 (Multi-Project Mode)**

이 엔진은 \--project-id 플래그를 사용하여 여러 개의 독립된 작품을
생성하는 다작 기능을 지원합니다.

이 플래그를 사용하면 엔진은 지정된 프로젝트 ID에 따라 아래의 경로를
동적으로 설정하여 각 작품의 데이터와 결과물을 완벽하게 분리합니다.

-   **입력 데이터(Story Bible):** data/{project_id}/

-   **출력 결과물(Episodes):** outputs/{project_id}/

**실행 예시:**

[Generated bash]{.mark}

[python -m src.run_novel run \--project-id urban_fantasy_A \--episodes
250]{.mark}

### **Change Log**

-   **v3.2‑RF (2025‑06‑21)** -- Roadmap 분리, 본문은 Spec·QA·Ops만 유지.

-   **v3.2 (2025‑06‑21)** -- 최초 Spec·QA 확장판 (로드맵 포함).

-   **v3.1 (2025‑05‑18)** -- Original master guide.
