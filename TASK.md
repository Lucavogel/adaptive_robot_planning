# TODO_REVISION.md — StretchBot KI Revision

## Status convention
| 🔄     | In progress |
| ✅      | Done        |
## Owner convention

| Owner | Meaning                      |
| ----- | ---------------------------- |
| Mehdi | Mehdi handles it             |
| Luca  | Luca handles it              |
| Both  | Both should review / discuss |

---

# Global priority order

```text
[CRITICAL]  Must be done first
[HIGH]      Strongly needed to satisfy reviewers
[MEDIUM]    Useful if time allows
[FINAL]     Depends on previous work
```

## Parallel workflow

```text
Sprint 1:
Luca  → WP1 Code stabilization
Mehdi → WP2 Manuscript restructuring
Both  → WP3 Figures / setup material

Sprint 2:
Luca  → WP4 Reviewer experiments
Mehdi → WP5 Draft rebuttal + paper sections

Sprint 3:
Both  → WP6 Results tables + interpretation
Mehdi → WP7 Final manuscript integration
Both  → WP8 Final checks + submission
```

---

# WP0 — [CRITICAL] Coordination and repository setup

Goal: avoid conflicts and prepare clean revision material.

| Status | Task                                | Owner | Notes                                |
| ------ | ----------------------------------- | ----- | ------------------------------------ |
| ✅      | Create branch `revision-kuin-2026`  |       | current branch                       |
| ✅      | Create folder `revision_materials/` |       | figures, logs, experiments, rebuttal |
| ✅      | Create folder `experiments/`        |       | baseline + long-session scripts      |
| ✅      | Create folder `paper_revision/`     |       | rewritten sections                   |
| ✅      | Create `REBUTTAL_DRAFT.md`          |       | point-by-point response              |
| ✅      | Create `CHANGELOG_REVIEWERS.md`     |       | list of manuscript changes           |
| ✅      | Assign owners for each WP           | Both  | Mehdi / Luca                         |
| 🔄      | Agree on official object names      | Both  | remove chair; harmonize water naming |

Acceptance criteria:

* Revision branch exists.
* Owners are assigned.
* Folder structure is ready.
* Object naming convention is fixed.

---

# WP1 — [CRITICAL] Code stabilization

Goal: make the repo coherent enough to support the revised paper and reviewer experiments.

Recommended owner: Luca
Can run in parallel with: WP2, WP3

---

## WP1.1 — [CRITICAL] Security and config

| Status | Task                                                | Owner | Notes                   |
| ------ | --------------------------------------------------- | ----- | ----------------------- |
| ⬜      | Revoke leaked OpenRouter API key                    | Luca  | critical security issue |
| ✅      | Remove API key from `src/config.py`                 | Luca  | no secret in Git        |
| ✅      | Load API key with `os.getenv("OPENROUTER_API_KEY")` | Luca  | use env variable        |
| ✅      | Add `.env` to `.gitignore`                          | Luca  | avoid future leak       |
| ✅      | Add `.env.example`                                  | Luca  | fake values only        |
| ✅      | Test LLM call with local env variable               | Luca  | must work               |

Acceptance criteria:

* No real API key in the repo.
* LLM call works through environment variable.

---

## WP1.2 — [CRITICAL] Imports and launchability

| Status | Task                                                                 | Owner | Notes                      |
| ------ | -------------------------------------------------------------------- | ----- | -------------------------- |
| ✅      | Fix `from utils.config import API_KEY` in `reasoning.py`             | Luca  | currently broken           |
| ✅      | Fix `from utils.config import API_KEY` in `Query_knowledge_graph.py` | Luca  | currently broken           |
| ✅      | Run `python -m compileall src`                                       | Luca  | catch syntax/import errors |
| ✅      | Add missing `__init__.py` if needed                                  | Luca  | package cleanliness        |
| ✅      | Test `python src/main.py` until first interaction                    | Luca  | no import crash            |

Acceptance criteria:

* `src/` compiles.
* `main.py` starts without import crash.

---

## WP1.3 — [HIGH] Model loading robustness

| Status | Task                                                | Owner | Notes                |
| ------ | --------------------------------------------------- | ----- | -------------------- |
| ✅      | Avoid loading Vosk model at import time             | Luca  | lazy loading         |
| ✅      | Add clean error if Vosk model is missing            | Luca  | avoid obscure crash  |
| ✅      | Avoid loading YOLO model at import time if possible | Luca  | lazy loading         |
| ✅      | Add configurable model paths                        | Luca  | no hardcoded paths   |
| ✅      | Document model download steps                       | Luca  | short README section |

Acceptance criteria:

* Missing models do not crash the whole project at import time.
* User gets clear setup instructions.

---

## WP1.4 — [CRITICAL] Main loop and verifier

| Status | Task                                            | Owner | Notes                        |
| ------ | ----------------------------------------------- | ----- | ---------------------------- |
| ✅      | Remove blocking `input()` issue in `main.py`    | Luca  | queue / timeout / event      |
| ✅      | Allow routine to continue after task success    | Luca  | no infinite waiting          |
| ✅      | Connect verifier LLM to main loop               | Luca  | paper claims verifier        |
| ✅      | Add fallback if verifier rejects multiple times | Luca  | safe scripted answer         |
| ✅      | Log verifier corrections                        | Luca  | needed for objective metrics |

Acceptance criteria:

* Routine can continue without being stuck.
* Verifier is actually called.
* Verifier failures are logged.

---

## WP1.5 — [CRITICAL] Perception and context consistency

| Status | Task                                                 | Owner | Notes                            |
| ------ | ---------------------------------------------------- | ----- | -------------------------------- |
| ✅      | Remove hardcoded `user_states = ["InPain"]`          | Luca  | fake adaptation                  |
| ✅      | Replace with real or explicitly simulated user state | Luca  | must be honest                   |
| ✅      | Replace or rename `get_environment_context_test()`   | Luca  | avoid pretending real perception |
| ✅      | Log objects sent to the LLM                          | Luca  | needed for experiments           |
| ✅      | Log emotional state sent to the LLM                  | Luca  | needed for failure analysis      |
| ✅      | Log user utterance / STT input                       | Luca  | needed for traceability          |

Acceptance criteria:

* No fake hardcoded pain state.
* Context sent to LLM is logged.
* Simulated perception is clearly named if used.

---

## WP1.6 — [CRITICAL] Object/action consistency

| Status | Task                                                         | Owner | Notes                               |
| ------ | ------------------------------------------------------------ | ----- | ----------------------------------- |
| ⬜      | Define official object list                                  | Both  | Water, Banana, Coffee, Towel, Chair |
| ⬜      | Unify names between YOLO, KG, LLM, and C++                   | Luca  | avoid `GlassOfWater` vs `glass`     |
| ⬜      | Ensure every `POINT_OBJECT` has execution or verbal fallback | Luca  | no silent failure                   |
| ⬜      | Prevent pointing to absent objects                           | Luca  | reviewer issue                      |
| ⬜      | Add user confirmation before physical pointing               | Luca  | collaborative protocol              |
| ⬜      | Store refused suggestions                                    | Luca  | do not repeat rejected offers       |

Acceptance criteria:

* No unsupported object is silently executed.
* Robot only points to detected/supported objects.
* Physical action requires confirmation or is disabled in experiment mode.

---

# WP2 — [CRITICAL] Manuscript restructuring

Goal: fix the main methodological and framing issues while Luca stabilizes the code.

Recommended owner: Mehdi
Can start immediately.
Can run in parallel with: WP1, WP3, WP4

---

## WP2.1 — [CRITICAL] Reframe as pilot / proof-of-concept

| Status | Task                                             | Owner | Notes                     |
| ------ | ------------------------------------------------ | ----- | ------------------------- |
| 🔄      | Reframe abstract as pilot/proof-of-concept       | Mehdi | needs final weaker wording |
| ✅      | Reframe introduction                             | Mehdi | no strong empirical claim |
| ✅      | Reframe evaluation section                       | Mehdi | exploratory only          |
| ✅      | Reframe discussion                               | Mehdi | no overclaim              |
| 🔄      | Reframe conclusion                               | Mehdi | needs final weaker wording |
| 🔄      | Replace “shows/proves” with “suggests/indicates” | Mehdi | mostly done; final pass needed |

Acceptance criteria:

* N=3 is never presented as strong evidence.
* The paper clearly says this is a pilot/prototype study.

---

## WP2.2 — [CRITICAL] Research questions and competency questions

| Status | Task                                              | Owner | Notes                                    |
| ------ | ------------------------------------------------- | ----- | ---------------------------------------- |
| ✅      | Rewrite RQ1–RQ3 clearly                           | Mehdi | introduction                             |
| ⬜      | Create section `Competency Questions`             | Mehdi | before/in evaluation                     |
| ⬜      | Define 8–10 competency questions                  | Mehdi | fatigue, pain, refusal, object relevance |
| ⬜      | Add expected behavior for each CQ                 | Mehdi | table                                    |
| ⬜      | Add evidence column                               | Mehdi | logs/results                             |
| ✅      | Create section `Answering the Research Questions` | Mehdi | discussion                               |
| ✅      | Answer RQ1 directly                               | Mehdi | architecture/adaptation                  |
| ✅      | Answer RQ2 directly                               | Mehdi | KG baseline limitation stated            |
| ✅      | Answer RQ3 directly                               | Mehdi | pilot perception                         |

Acceptance criteria:

* Each RQ has a direct answer.
* Reviewer does not need to reconstruct the answers.

---

## WP2.3 — [CRITICAL] Evaluation rationale

| Status | Task                                              | Owner | Notes                       |
| ------ | ------------------------------------------------- | ----- | --------------------------- |
| ✅      | Rename section to `Exploratory Pilot Evaluation`  | Mehdi | pilot framing made explicit |
| ✅      | Justify why N=3                                   | Mehdi | prototype feasibility       |
| ✅      | State no statistical generalization               | Mehdi | important                   |
| ✅      | Justify custom questionnaire                      | Mehdi | adaptivity/object relevance |
| ✅      | Mention limitation of non-validated questionnaire | Mehdi | honest                      |
| ✅      | Add future work with SUS/Godspeed/Trust scales    | Mehdi | reviewer 2                  |
| ✅      | Add objective metrics subsection placeholder      | Mehdi | diagnostic technical measures |
| ✅      | Add baseline subsection placeholder               | Mehdi | baseline framed as future ablation |

Acceptance criteria:

* Evaluation weakness is acknowledged.
* The paper explains why the evaluation still has value as a pilot.

---

## WP2.4 — [HIGH] Reduce repetition and clean claims

| Status | Task                                           | Owner | Notes                         |
| ------ | ---------------------------------------------- | ----- | ----------------------------- |
| ✅      | Find repeated adaptivity/smoothness paragraphs | Mehdi | results/discussion cleaned    |
| ✅      | Keep one clear explanation only                | Mehdi | avoid repetition              |
| ✅      | Remove duplicated qualitative interpretation   | Mehdi | compact                       |
| ✅      | Weaken unsupported claims                      | Mehdi | especially user preference    |
| ✅      | Make contribution technical, not statistical   | Mehdi | system paper framing          |

Acceptance criteria:

* Reviewer 1 cannot say the same tradeoff is repeated many times.

---

# WP3 — [HIGH] Figures and visual material

Goal: answer the request for setup and architecture images.

Recommended owner: Luca
Can run in parallel with: WP1, WP2

---

## WP3.1 — [HIGH] Hardware/setup figure

| Status | Task                            | Owner | Notes                                 |
| ------ | ------------------------------- | ----- | ------------------------------------- |
| ✅      | Take photo of real setup        | Luca  | robot, camera, objects, user position |
| ✅      | Add clean labels                | Luca  | robot, camera, objects, user          |
| ✅      | Hide sensitive/private elements | Luca  | no faces; setup labels visible        |
| ✅      | Export high-resolution PNG/JPG  | Luca  | paper quality                         |
| ✅      | Write concise caption           | Mehdi | for manuscript                        |
| ✅      | Insert figure in manuscript     | Mehdi | implementation section                |

Acceptance criteria:

* Reviewer can understand robot/camera/object layout from one figure.

---

## WP3.2 — [HIGH] Architecture figure

| Status | Task                          | Owner | Notes                         |
| ------ | ----------------------------- | ----- | ----------------------------- |
| ✅      | Create clean pipeline diagram | Luca  | not overloaded                |
| ✅      | Include perception modules    | Luca  | STT, emotion, object, posture |
| ✅      | Include context package       | Luca  | central block                 |
| ✅      | Include KG retrieval          | Luca  | key contribution              |
| ✅      | Include primary LLM           | Luca  | decision                      |
| ✅      | Include verifier LLM          | Luca  | safety/format                 |
| ✅      | Include command parser        | Luca  | prefix handling               |
| ✅      | Include execution layer       | Luca  | TTS + robot pointing          |
| ✅      | Include logging/feedback loop | Luca  | feedback loop shown           |
| ✅      | Write caption                 | Mehdi | for manuscript                |
| ✅      | Insert figure in manuscript   | Mehdi | system architecture           |

Acceptance criteria:

* Diagram clearly explains the neuro-symbolic closed loop.

---

# WP4 — [CRITICAL] Reviewer experiments

Goal: generate the additional evidence requested by reviewers.

Recommended owner: Luca
Can start after: WP1.1, WP1.2, basic LLM pipeline working
Can run in parallel with: WP2

---

## WP4.1 — [CRITICAL] LLM-only vs KG+LLM baseline

Goal: show whether the Knowledge Graph contributes anything.

| Status | Task                                     | Owner | Notes                     |
| ------ | ---------------------------------------- | ----- | ------------------------- |
| ⬜      | Create `experiments/scenarios.json`      | Luca  | 20–30 scenarios           |
| ⬜      | Define expected action for each scenario | Both  | manual oracle             |
| ⬜      | Implement condition A: LLM-only          | Luca  | raw context only          |
| ⬜      | Implement condition B: KG+LLM            | Luca  | context + KG relations    |
| ⬜      | Implement condition C: KG+LLM+Verifier   | Luca  | if possible               |
| ⬜      | Measure action correctness               | Luca  | expected vs output        |
| ⬜      | Measure object relevance                 | Luca  | selected object relevant? |
| ⬜      | Measure prefix validity                  | Luca  | valid command format      |
| ⬜      | Measure hallucinated object rate         | Luca  | points to absent object   |
| ⬜      | Measure unsafe/incoherent outputs        | Both  | manual or rule-based      |
| ⬜      | Measure latency                          | Luca  | timestamp start/end       |
| ⬜      | Export `results_baseline.csv`            | Luca  | for paper                 |
| ⬜      | Create final baseline table              | Both  | for manuscript            |

Acceptance criteria:

* At least 20 scenarios.
* At least LLM-only and KG+LLM are compared.
* Paper has a table showing KG contribution.

---

## WP4.2 — [HIGH] Failure case collection

Goal: provide explicit failure analysis.

| Status | Task                                      | Owner | Notes                      |
| ------ | ----------------------------------------- | ----- | -------------------------- |
| ⬜      | Collect real observed failures from tests | Luca  | best evidence              |
| 🔄      | Add simulated failures if needed          | Both  | label observed/anticipated |
| ✅      | Document wrong emotion detection          | Luca  | affect treated as optional |
| 🔄      | Document object hallucination             | Luca  | anticipated risk only      |
| ✅      | Document invalid prefix                   | Luca  | parser/verifier issue      |
| ✅      | Document repeated verifier rejection      | Luca  | fallback issue             |
| ✅      | Document latency issue                    | Luca  | cloud API                  |
| ✅      | Document posture detection issue          | Luca  | camera angle               |
| ✅      | Document conflicting inputs               | Both  | voice vs face vs posture   |
| ✅      | Add mitigation for every failure          | Both  | not only description       |
| 🔄      | Create final failure-case table           | Both  | needs observed/anticipated column |

Acceptance criteria:

* At least 8 failure cases.
* Each has cause, example, impact, mitigation.

---

## WP4.3 — [MEDIUM] Long-session analysis

Goal: answer reviewer concern about LLM degradation when context grows.

| Status | Task                                               | Owner | Notes                    |
| ------ | -------------------------------------------------- | ----- | ------------------------ |
| ⬜      | Create long-session script                         | Luca  | 15–20 turns/session      |
| ⬜      | Session A: normal routine                          | Luca  | simple case              |
| ⬜      | Session B: fatigue + refusal of water              | Luca  | memory/refusal test      |
| ⬜      | Session C: pain + interruptions + changing objects | Luca  | robustness               |
| ⬜      | Measure format validity over time                  | Luca  | prefix correctness       |
| ⬜      | Measure repetition rate                            | Luca  | repeated suggestions     |
| ⬜      | Measure context consistency                        | Both  | respects previous turns  |
| ⬜      | Measure latency growth                             | Luca  | response time over turns |
| ⬜      | Export `results_long_session.csv`                  | Luca  | for paper                |
| ✅      | Write 1-paragraph interpretation                   | Mehdi | discussion limitation    |

Acceptance criteria:

* 3 long sessions tested.
* Metrics table available.
* Clear conclusion: stable / degrades / needs context summarization.

---

# WP5 — [FINAL] Results tables and paper-ready evidence

Goal: turn raw experiment outputs into compact manuscript tables.

Recommended owner: Both
Starts after: WP4 outputs
Can run in parallel with: WP6

---

## WP5.1 — [FINAL] Baseline results table

| Status | Task                          | Owner | Notes                  |
| ------ | ----------------------------- | ----- | ---------------------- |
| ⬜      | Import baseline CSV           | Luca  | from WP4.1             |
| ⬜      | Compute summary metrics       | Luca  | averages / percentages |
| ⬜      | Create compact table          | Both  | LLM-only vs KG+LLM     |
| ⬜      | Write cautious interpretation | Mehdi | no overclaim           |
| ⬜      | Add to Results                | Mehdi | manuscript             |

Example table:

| Metric                   | LLM-only | KG+LLM | KG+LLM+Verifier |
| ------------------------ | -------: | -----: | --------------: |
| Action correctness       |          |        |                 |
| Object relevance         |          |        |                 |
| Valid prefix rate        |          |        |                 |
| Hallucinated object rate |          |        |                 |
| Mean latency             |          |        |                 |

---

## WP5.2 — [FINAL] Objective metrics table

| Status | Task                                    | Owner | Notes               |
| ------ | --------------------------------------- | ----- | ------------------- |
| ⬜      | Compute mean LLM latency                | Luca  | seconds             |
| ⬜      | Compute verifier correction rate        | Luca  | percentage          |
| ⬜      | Compute invalid output count            | Luca  | count               |
| ⬜      | Compute number of adaptations           | Luca  | count               |
| ⬜      | Compute object pointing success/failure | Luca  | count               |
| ⬜      | Create compact table                    | Both  | for Results         |
| ⬜      | Write interpretation                    | Mehdi | link to limitations |

---

## WP5.3 — [FINAL] Failure case table

| Status | Task                                | Owner | Notes               |
| ------ | ----------------------------------- | ----- | ------------------- |
| ✅      | Select strongest failure cases      | Both  | 8–10 max            |
| ✅      | Add cause/example/impact/mitigation | Both  | table               |
| 🔄      | Mark observed vs simulated          | Both  | needs status column |
| ✅      | Add to Discussion                   | Mehdi | robustness analysis |

---

# WP6 — [FINAL] Final manuscript integration

Goal: integrate all revised material into one coherent manuscript.

Recommended owner: Mehdi
Starts after: WP2 draft + WP3 figures + WP5 tables

---

## WP6.1 — [FINAL] Section integration

| Status | Task                            | Owner | Notes                     |
| ------ | ------------------------------- | ----- | ------------------------- |
| 🔄      | Integrate revised abstract      | Mehdi | needs final weaker wording |
| ✅      | Integrate revised introduction  | Mehdi | contributions/RQs         |
| ✅      | Integrate architecture figure   | Mehdi | system section            |
| ✅      | Integrate setup figure          | Mehdi | implementation            |
| ⬜      | Integrate competency questions  | Mehdi | implementation/evaluation |
| ✅      | Integrate evaluation rationale  | Mehdi | evaluation                |
| ⬜      | Integrate baseline results      | Mehdi | results                   |
| ✅      | Integrate objective metrics     | Mehdi | diagnostic observations   |
| ✅      | Integrate RQ answers            | Mehdi | discussion                |
| 🔄      | Integrate failure analysis      | Mehdi | needs observed/anticipated cleanup |
| ✅      | Integrate long-session analysis | Mehdi | discussion/results        |
| 🔄      | Integrate revised conclusion    | Mehdi | needs final weaker wording |

Acceptance criteria:

* Manuscript contains all reviewer-requested additions.
* Claims are cautious and consistent.

---

## WP6.2 — [FINAL] Consistency check

| Status | Task                                              | Owner | Notes             |
| ------ | ------------------------------------------------- | ----- | ----------------- |
| 🔄      | Check paper does not claim unimplemented features | Both  | chair/water + baseline wording |
| ⬜      | Check verifier description matches code           | Both  | critical          |
| ⬜      | Check confirmation protocol matches code          | Both  | critical          |
| 🔄      | Check perception is described honestly            | Both  | affect optional; final pass needed |
| 🔄      | Check object names are consistent                 | Both  | remove chair/water bottle inconsistency |
| 🔄      | Check all figures are referenced                  | Mehdi | duplicate architecture figures remain |
| ⬜      | Check references and citations                    | Mehdi | no placeholders   |
| ⬜      | Check final file is Word or LaTeX                 | Mehdi | no PDF            |

Acceptance criteria:

* Paper, code, and experiments tell the same story.
* Manuscript is ready for Filip’s review.

---

# WP7 — [FINAL] Rebuttal / response to reviewers

Goal: produce the point-by-point response.

Recommended owner: Mehdi
Can draft early, but finalize after WP6

---

## WP7.1 — [FINAL] Editor response

| Status | Task                             | Owner | Notes                         |
| ------ | -------------------------------- | ----- | ----------------------------- |
| ✅      | Thank editor                     | Mehdi | polite                        |
| ✅      | Summarize main changes           | Mehdi | pilot, RQs, baseline, figures |
| 🔄      | Mention editable files submitted | Mehdi | finalize at submission        |

---

## WP7.2 — [FINAL] Reviewer 1 response

| Status | Task                                   | Owner | Notes                 |
| ------ | -------------------------------------- | ----- | --------------------- |
| 🔄      | Respond to small sample size           | Mehdi | drafted; update page refs |
| 🔄      | Respond to failure cases               | Mehdi | drafted; status column pending |
| 🔄      | Respond to conflicting/malicious input | Mehdi | drafted; update page refs |
| 🔄      | Respond to verifier repeated rejection | Mehdi | drafted; update page refs |
| 🔄      | Respond to long-session concern        | Mehdi | drafted; update page refs |
| 🔄      | Respond to RQs not revisited           | Mehdi | drafted; update page refs |
| 🔄      | Respond to missing setup image         | Mehdi | drafted; update page refs |
| 🔄      | Respond to KG contribution not tested  | Mehdi | drafted as limitation/future ablation |
| 🔄      | Respond to repetition issue            | Mehdi | drafted; update page refs |

Acceptance criteria:

* Every Reviewer 1 point is answered.
* Each answer says where the manuscript changed.

---

## WP7.3 — [FINAL] Reviewer 2 response

| Status | Task                                              | Owner | Notes                 |
| ------ | ------------------------------------------------- | ----- | --------------------- |
| 🔄      | Acknowledge N=3 limitation                        | Mehdi | drafted; update page refs |
| 🔄      | Explain pilot/proof-of-concept framing            | Mehdi | drafted; update page refs |
| 🔄      | Respond to weak RQ answers                        | Mehdi | drafted; update page refs |
| 🔄      | Respond to KG not demonstrated                    | Mehdi | drafted as limitation/future ablation |
| 🔄      | Respond to custom questionnaire                   | Mehdi | drafted; update page refs |
| 🔄      | Respond to lack of objective metrics              | Mehdi | drafted as diagnostic observations |
| 🔄      | Respond to no comparison with simpler alternative | Mehdi | drafted as future ablation |
| 🔄      | Respond to strong conclusions                     | Mehdi | drafted; final abstract/conclusion pass |

Acceptance criteria:

* Every Reviewer 2 point is answered.
* Tone is polite and non-defensive.

---

# WP8 — [FINAL] Submission

Goal: prepare and submit the final revision package.

Recommended owner: Both + Filip validation

| Status | Task                              | Owner | Notes          |
| ------ | --------------------------------- | ----- | -------------- |
| ⬜      | Send revised manuscript to Filip  | Mehdi | for validation |
| ⬜      | Send rebuttal to Filip            | Mehdi | for validation |
| ⬜      | Apply Filip’s comments            | Both  | final edits    |
| ⬜      | Check KI / Springer format        | Mehdi | journal format |
| ⬜      | Submit editable source files only | Mehdi | Word or LaTeX  |
| ⬜      | Submit rebuttal/list of changes   | Mehdi | required       |
| ⬜      | Submit before 04 July 2026        | Mehdi | deadline       |

Acceptance criteria:

* Manuscript submitted as editable source.
* Rebuttal/list of changes submitted.
* Submission completed before deadline.

---

# Priority summary

## Must start immediately

| Priority   | WP                           | Owner |
| ---------- | ---------------------------- | ----- |
| [CRITICAL] | WP0 Coordination             | Both  |
| [CRITICAL] | WP1 Code stabilization       | Luca  |
| [CRITICAL] | WP2 Manuscript restructuring | Mehdi |

## Next priority

| Priority   | WP                            | Owner        |
| ---------- | ----------------------------- | ------------ |
| [HIGH]     | WP3 Figures                   | Luca + Mehdi |
| [CRITICAL] | WP4.1 LLM-only vs KG baseline | Luca         |
| [HIGH]     | WP4.2 Failure cases           | Both         |

## If time allows

| Priority | WP                          | Owner |
| -------- | --------------------------- | ----- |
| [MEDIUM] | WP4.3 Long-session analysis | Luca  |
| [FINAL]  | WP5 Tables                  | Both  |

## Finalization

| Priority | WP                         | Owner         |
| -------- | -------------------------- | ------------- |
| [FINAL]  | WP6 Manuscript integration | Mehdi         |
| [FINAL]  | WP7 Rebuttal               | Mehdi         |
| [FINAL]  | WP8 Submission             | Mehdi + Filip |

---

# Recommended timeline

## Day 1–2

| Owner | Tasks                                |
| ----- | ------------------------------------ |
| Luca  | WP1.1, WP1.2, WP1.4                  |
| Mehdi | WP2.1, WP2.2, WP2.3                  |
| Both  | WP0, object naming convention        |
| Luca  | Start WP3 figures if setup available |

## Day 3–4

| Owner | Tasks                         |
| ----- | ----------------------------- |
| Luca  | WP4.1 baseline experiments    |
| Luca  | WP4.2 failure case collection |
| Mehdi | Draft RQ/CQ sections          |
| Mehdi | Draft evaluation rationale    |
| Both  | Review first baseline results |

## Day 5

| Owner | Tasks                        |
| ----- | ---------------------------- |
| Luca  | Export experiment CSVs       |
| Both  | WP5 results tables           |
| Mehdi | Integrate figures and tables |
| Mehdi | Start rebuttal draft         |

## Day 6

| Owner | Tasks                            |
| ----- | -------------------------------- |
| Mehdi | WP6 final manuscript integration |
| Both  | WP6.2 consistency check          |
| Mehdi | WP7 rebuttal finalization        |
| Mehdi | Send to Filip                    |

## Final day

| Owner | Tasks                        |
| ----- | ---------------------------- |
| Both  | Apply Filip’s comments       |
| Mehdi | Final format check           |
| Mehdi | Submit Word/LaTeX + rebuttal |
