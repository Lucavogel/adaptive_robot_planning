
* 🔄 In progress
* ✅ Done
* 
Owner convention:

* Mehdi
* Luca

revision split into work packages that can run in parallel:

```text
WP1 Code fixes        || WP3 Figures
WP2 Experiments       || WP4 Paper restructuring
WP5 Tables            || WP6 Manuscript writing
WP7 Rebuttal          after WP6 mostly complete
```

---

# WP0 — Coordination and repository setup

Goal: avoid conflicts between Mehdi and Luca.

| Status | Task                                    | Owner | Notes                                |
| ------ | --------------------------------------- | ----- | ------------------------------------ |
| ⬜      | Create branch `revision-kuin-2026`      |       | `git checkout -b revision-kuin-2026` |
| ⬜      | Create folder `revision_materials/`     |       | figures, logs, experiments, rebuttal |
| ⬜      | Create `experiments/` folder            |       | baseline + long-session scripts      |
| ⬜      | Create `paper_revision/` folder         |       | revised manuscript sections          |
| ⬜      | Create `REBUTTAL_DRAFT.md`              |       | point-by-point response              |
| ⬜      | Assign owners to each WP                |       | Mehdi / Luca                         |
| ⬜      | Agree on naming conventions for objects |       | Water, Banana, Coffee, Towel, Chair  |

Can be done in parallel with: nothing.
Dependency: first step.

---

# WP1 — Minimal code stabilization

Goal: make the system consistent enough to run tests and support paper claims.

Can be done in parallel with: WP3 figures, WP4 paper structure.

## WP1.1 Security and config

| Status | Task                                                | Owner | Notes                  |
| ------ | --------------------------------------------------- | ----- | ---------------------- |
| ⬜      | Revoke leaked OpenRouter API key                    |       | critical               |
| ⬜      | Remove API key from `src/config.py`                 |       | no secret in Git       |
| ⬜      | Load API key with `os.getenv("OPENROUTER_API_KEY")` |       | `.env` or terminal env |
| ⬜      | Add `.env` to `.gitignore`                          |       | prevent future leak    |
| ⬜      | Add `.env.example`                                  |       | fake values only       |
| ⬜      | Test LLM call with local env variable               |       | must work              |

## WP1.2 Imports and launchability

| Status | Task                                                                 | Owner | Notes                      |
| ------ | -------------------------------------------------------------------- | ----- | -------------------------- |
| ⬜      | Fix `from utils.config import API_KEY` in `reasoning.py`             |       | currently broken           |
| ⬜      | Fix `from utils.config import API_KEY` in `Query_knowledge_graph.py` |       | currently broken           |
| ⬜      | Run `python -m compileall src`                                       |       | catch import/syntax errors |
| ⬜      | Add missing `__init__.py` if needed                                  |       | package cleanliness        |
| ⬜      | Test `python src/main.py` until first interaction                    |       | no import crash            |

## WP1.3 Model loading robustness

| Status | Task                                          | Owner | Notes               |
| ------ | --------------------------------------------- | ----- | ------------------- |
| ⬜      | Avoid loading Vosk model at import time       |       | lazy loading        |
| ⬜      | Add clean error if Vosk model missing         |       | avoid obscure crash |
| ⬜      | Avoid loading YOLO at import time if possible |       | lazy loading        |
| ⬜      | Add configurable model paths                  |       | no hardcoded paths  |
| ⬜      | Document model download steps briefly         |       | README or notes     |

## WP1.4 Main loop and verifier

| Status | Task                                            | Owner | Notes                 |
| ------ | ----------------------------------------------- | ----- | --------------------- |
| ⬜      | Remove blocking `input()` problem in `main.py`  |       | queue/timeout/event   |
| ⬜      | Allow routine to continue after task success    |       | no waiting forever    |
| ⬜      | Connect verifier LLM to main loop               |       | paper claims verifier |
| ⬜      | Add fallback if verifier rejects multiple times |       | scripted safe answer  |
| ⬜      | Log verifier corrections                        |       | needed for results    |

## WP1.5 Perception/context consistency

| Status | Task                                                 | Owner | Notes                            |
| ------ | ---------------------------------------------------- | ----- | -------------------------------- |
| ⬜      | Remove hardcoded `user_states = ["InPain"]`          |       | fake adaptation                  |
| ⬜      | Replace with real or explicitly simulated user state |       | must be clear                    |
| ⬜      | Replace or rename `get_environment_context_test()`   |       | avoid pretending real perception |
| ⬜      | Log detected/simulated objects sent to LLM           |       | needed for experiments           |
| ⬜      | Log emotional state sent to LLM                      |       | needed for failure analysis      |

## WP1.6 Object/action consistency

| Status | Task                                                                      | Owner | Notes                                 |
| ------ | ------------------------------------------------------------------------- | ----- | ------------------------------------- |
| ⬜      | Define official object list                                               |       | Water, Banana, Coffee, Towel, Chair   |
| ⬜      | Unify names between YOLO, KG, LLM, C++                                    |       | no `GlassOfWater` vs `glass` mismatch |
| ⬜      | Ensure every `POINT_OBJECT` has either robot execution or verbal fallback |       | no silent failure                     |
| ⬜      | Prevent pointing to absent objects                                        |       | important reviewer issue              |
| ⬜      | Add user confirmation before physical pointing                            |       | collaborative protocol                |
| ⬜      | Store refused suggestions                                                 |       | do not repeat                         |

WP1 acceptance criteria:

* `main.py` launches.
* LLM call works.
* Verifier is called.
* No hardcoded pain state.
* Actions are logged.
* Physical action requires confirmation or is clearly disabled in experiment mode.

---

# WP2 — Reviewer experiments

Goal: generate extra evidence requested by reviewers.

Can start after: WP1.1, WP1.2, and basic reasoning pipeline working.
Can run in parallel with: WP4 manuscript restructuring.

---

## WP2.1 LLM-only vs KG+LLM baseline

Goal: show whether the Knowledge Graph helps.

| Status | Task                                     | Owner | Notes                     |
| ------ | ---------------------------------------- | ----- | ------------------------- |
| ⬜      | Create `experiments/scenarios.json`      |       | 20–30 scenarios           |
| ⬜      | Define expected action for each scenario |       | manual oracle             |
| ⬜      | Implement condition A: LLM-only          |       | raw context only          |
| ⬜      | Implement condition B: KG+LLM            |       | context + KG relations    |
| ⬜      | Implement condition C: KG+LLM+Verifier   |       | if possible               |
| ⬜      | Measure action correctness               |       | expected vs output        |
| ⬜      | Measure object relevance                 |       | selected object relevant? |
| ⬜      | Measure prefix validity                  |       | valid command format      |
| ⬜      | Measure hallucinated object rate         |       | points to absent object   |
| ⬜      | Measure unsafe/incoherent outputs        |       | manual or rule-based      |
| ⬜      | Measure latency                          |       | timestamp start/end       |
| ⬜      | Export `results_baseline.csv`            |       | for paper                 |
| ⬜      | Create final table for manuscript        |       | compact                   |

Acceptance criteria:

* At least 20 scenarios.
* At least 2 compared systems: LLM-only and KG+LLM.
* Table ready for paper.

---

## WP2.2 Long-session analysis

Goal: answer reviewer concern about LLM degradation when context grows.

| Status | Task                                               | Owner | Notes                    |
| ------ | -------------------------------------------------- | ----- | ------------------------ |
| ⬜      | Create long-session script                         |       | 15–20 turns/session      |
| ⬜      | Session A: normal routine                          |       | simple case              |
| ⬜      | Session B: fatigue + refusal of water              |       | memory/refusal test      |
| ⬜      | Session C: pain + interruptions + changing objects |       | robustness               |
| ⬜      | Measure format validity over time                  |       | prefix correctness       |
| ⬜      | Measure repetition rate                            |       | repeated suggestions     |
| ⬜      | Measure context consistency                        |       | respects previous turns  |
| ⬜      | Measure latency growth                             |       | response time over turns |
| ⬜      | Export `results_long_session.csv`                  |       | for paper                |
| ⬜      | Write 1-paragraph interpretation                   |       | for discussion           |

Acceptance criteria:

* 3 long sessions tested.
* Metrics table available.
* Clear conclusion: stable / degrades / needs context summarization.

---

## WP2.3 Failure case collection

Goal: provide explicit failure analysis.

| Status | Task                                      | Owner | Notes                      |
| ------ | ----------------------------------------- | ----- | -------------------------- |
| ⬜      | Collect real observed failures from tests |       | best evidence              |
| ⬜      | Add simulated failures if needed          |       | clearly label as simulated |
| ⬜      | Document wrong emotion detection          |       | mic/camera issue           |
| ⬜      | Document object hallucination             |       | LLM issue                  |
| ⬜      | Document invalid prefix                   |       | parser/verifier issue      |
| ⬜      | Document repeated verifier rejection      |       | fallback issue             |
| ⬜      | Document latency issue                    |       | cloud API                  |
| ⬜      | Document posture detection issue          |       | camera angle               |
| ⬜      | Document conflicting inputs               |       | voice vs face vs posture   |
| ⬜      | Add mitigation for every failure          |       | not only description       |
| ⬜      | Create final failure-case table           |       | for manuscript             |

Acceptance criteria:

* At least 8 failure cases.
* Each has cause, example, impact, mitigation.

---

# WP3 — Figures and visual materials

Goal: answer reviewer request for setup and architecture image.
Can be done in parallel with: WP1 and WP4.

---

## WP3.1 Hardware/setup figure

| Status | Task                            | Owner | Notes                                 |
| ------ | ------------------------------- | ----- | ------------------------------------- |
| ⬜      | Take photo of real setup        |       | robot, camera, user position, objects |
| ⬜      | Add clean labels                |       | Robot arm, camera, objects, user      |
| ⬜      | Hide sensitive/private elements |       | faces, screens, keys                  |
| ⬜      | Export high-res PNG/JPG         |       | paper quality                         |
| ⬜      | Write caption                   |       | concise                               |
| ⬜      | Insert figure in manuscript     |       | Implementation or System              |

Acceptance criteria:

* Reviewer can understand robot/camera/object layout from one figure.

---

## WP3.2 Architecture figure

| Status | Task                          | Owner | Notes                         |
| ------ | ----------------------------- | ----- | ----------------------------- |
| ⬜      | Create clean pipeline diagram |       | not overloaded                |
| ⬜      | Include perception modules    |       | STT, emotion, object, posture |
| ⬜      | Include context package       |       | central block                 |
| ⬜      | Include KG retrieval          |       | key contribution              |
| ⬜      | Include primary LLM           |       | decision                      |
| ⬜      | Include verifier LLM          |       | safety/format                 |
| ⬜      | Include command parser        |       | prefix handling               |
| ⬜      | Include execution layer       |       | TTS + robot pointing          |
| ⬜      | Include logging/feedback loop |       | objective metrics             |
| ⬜      | Insert figure in manuscript   |       | System Architecture           |

Acceptance criteria:

* Diagram clearly explains neuro-symbolic loop.

---

# WP4 — Manuscript restructuring

Goal: prepare paper sections while code/experiments are still running.

Can start immediately.
Can run in parallel with: WP1, WP2, WP3.

---

## WP4.1 Global reframing as pilot study

| Status | Task                                             | Owner | Notes                     |
| ------ | ------------------------------------------------ | ----- | ------------------------- |
| ⬜      | Reframe abstract as pilot/proof-of-concept       |       | very important            |
| ⬜      | Reframe introduction                             |       | no strong empirical claim |
| ⬜      | Reframe evaluation section                       |       | exploratory only          |
| ⬜      | Reframe discussion                               |       | no overclaim              |
| ⬜      | Reframe conclusion                               |       | pilot evidence only       |
| ⬜      | Replace “shows/proves” with “suggests/indicates” |       | cautious language         |

Acceptance criteria:

* N=3 is never presented as strong evidence.
* The paper is clearly a pilot/prototype study.

---

## WP4.2 Research questions and competency questions

| Status | Task                                              | Owner | Notes                        |
| ------ | ------------------------------------------------- | ----- | ---------------------------- |
| ⬜      | Rewrite RQ1–RQ3 clearly                           |       | intro                        |
| ⬜      | Create section `Competency Questions`             |       | before or inside evaluation  |
| ⬜      | Define 8–10 competency questions                  |       | fatigue, pain, refusal, etc. |
| ⬜      | Add expected behavior for each CQ                 |       | table                        |
| ⬜      | Add evidence column                               |       | logs/results                 |
| ⬜      | Create section `Answering the Research Questions` |       | discussion                   |
| ⬜      | Answer RQ1 directly                               |       | architecture/adaptation      |
| ⬜      | Answer RQ2 directly                               |       | KG baseline                  |
| ⬜      | Answer RQ3 directly                               |       | pilot perception             |

Acceptance criteria:

* Reviewer no longer has to reconstruct answers.
* Each RQ has an explicit answer.

---

## WP4.3 Evaluation rationale

| Status | Task                                              | Owner | Notes                                  |
| ------ | ------------------------------------------------- | ----- | -------------------------------------- |
| ⬜      | Rename section to `Exploratory Pilot Evaluation`  |       | clearer                                |
| ⬜      | Justify why N=3                                   |       | prototype feasibility                  |
| ⬜      | Explicitly state no statistical generalization    |       | important                              |
| ⬜      | Justify custom questionnaire                      |       | adapted to object relevance/adaptivity |
| ⬜      | Mention limitation of non-validated questionnaire |       | honest                                 |
| ⬜      | Add future work with SUS/Godspeed/Trust scales    |       | reviewer 2                             |
| ⬜      | Add objective metrics subsection                  |       | from WP2                               |
| ⬜      | Add baseline subsection                           |       | from WP2                               |

Acceptance criteria:

* Methodological weakness is acknowledged and controlled.

---

## WP4.4 Reduce repetition and clean claims

| Status | Task                                           | Owner | Notes                         |
| ------ | ---------------------------------------------- | ----- | ----------------------------- |
| ⬜      | Find repeated adaptivity/smoothness paragraphs |       | results/discussion/conclusion |
| ⬜      | Keep one strong explanation only               |       | avoid repetition              |
| ⬜      | Remove duplicated qualitative interpretation   |       | compact                       |
| ⬜      | Weaken unsupported claims                      |       | especially user preference    |
| ⬜      | Make contribution technical, not statistical   |       | system paper framing          |

Acceptance criteria:

* Reviewer 1 cannot say the same tradeoff is repeated many times.

---

# WP5 — Results tables and final evidence

Goal: convert experiment outputs into paper-ready tables.

Starts after: WP2 has outputs.
Can run in parallel with: WP6 writing.

---

## WP5.1 Baseline results table

| Status | Task                    | Owner | Notes                  |
| ------ | ----------------------- | ----- | ---------------------- |
| ⬜      | Import baseline CSV     |       | from WP2.1             |
| ⬜      | Compute summary metrics |       | averages / percentages |
| ⬜      | Create compact table    |       | LLM-only vs KG+LLM     |
| ⬜      | Write interpretation    |       | cautious               |
| ⬜      | Add to Results          |       | manuscript             |

Example table:

| Metric                   | LLM-only | KG+LLM | KG+LLM+Verifier |
| ------------------------ | -------: | -----: | --------------: |
| Action correctness       |          |        |                 |
| Object relevance         |          |        |                 |
| Valid prefix rate        |          |        |                 |
| Hallucinated object rate |          |        |                 |
| Mean latency             |          |        |                 |

---

## WP5.2 Objective metrics table

| Status | Task                                    | Owner | Notes               |
| ------ | --------------------------------------- | ----- | ------------------- |
| ⬜      | Compute mean LLM latency                |       | seconds             |
| ⬜      | Compute verifier correction rate        |       | %                   |
| ⬜      | Compute invalid output count            |       | count               |
| ⬜      | Compute number of adaptations           |       | count               |
| ⬜      | Compute object pointing success/failure |       | count               |
| ⬜      | Create compact table                    |       | for Results         |
| ⬜      | Write interpretation                    |       | link to limitations |

---

## WP5.3 Failure case table

| Status | Task                                | Owner | Notes               |
| ------ | ----------------------------------- | ----- | ------------------- |
| ⬜      | Select strongest failure cases      |       | 8–10 max            |
| ⬜      | Add cause/example/impact/mitigation |       | table               |
| ⬜      | Mark observed vs simulated          |       | honest              |
| ⬜      | Add to Discussion                   |       | robustness analysis |

---

# WP6 — Final manuscript writing

Goal: integrate all revised content into one coherent manuscript.
Starts after: WP4 draft + WP5 tables + WP3 figures.

---

## WP6.1 Section integration

| Status | Task                            | Owner | Notes                     |
| ------ | ------------------------------- | ----- | ------------------------- |
| ⬜      | Integrate revised abstract      |       | pilot framing             |
| ⬜      | Integrate revised introduction  |       | contributions/RQs         |
| ⬜      | Integrate architecture figure   |       | system section            |
| ⬜      | Integrate setup figure          |       | implementation            |
| ⬜      | Integrate competency questions  |       | implementation/evaluation |
| ⬜      | Integrate evaluation rationale  |       | evaluation                |
| ⬜      | Integrate baseline results      |       | results                   |
| ⬜      | Integrate objective metrics     |       | results                   |
| ⬜      | Integrate RQ answers            |       | discussion                |
| ⬜      | Integrate failure analysis      |       | discussion                |
| ⬜      | Integrate long-session analysis |       | discussion/results        |
| ⬜      | Integrate revised conclusion    |       | cautious                  |

## WP6.2 Final consistency check

| Status | Task                                              | Owner | Notes             |
| ------ | ------------------------------------------------- | ----- | ----------------- |
| ⬜      | Check paper does not claim unimplemented features |       | critical          |
| ⬜      | Check verifier description matches code           |       | critical          |
| ⬜      | Check confirmation protocol matches code          |       | critical          |
| ⬜      | Check perception is described honestly            |       | real vs simulated |
| ⬜      | Check object names are consistent                 |       | KG/LLM/robot      |
| ⬜      | Check all figures are referenced                  |       | no orphan figure  |
| ⬜      | Check references and citations                    |       | no placeholders   |
| ⬜      | Check final file is Word or LaTeX                 |       | no PDF            |

Acceptance criteria:

* Revised manuscript is coherent and ready for Filip’s review.

---

# WP7 — Rebuttal / response to reviewers

Goal: produce the point-by-point response.

Starts after: main manuscript changes are known.
Can draft earlier, finalize after WP6.

---

## WP7.1 Editor response

| Status | Task                             | Owner | Notes                        |
| ------ | -------------------------------- | ----- | ---------------------------- |
| ⬜      | Thank editor                     |       | polite                       |
| ⬜      | Summarize main changes           |       | pilot framing, RQs, baseline |
| ⬜      | Mention editable files submitted |       | Word/LaTeX                   |

## WP7.2 Reviewer 1 response

| Status | Task                                   | Owner | Notes                 |
| ------ | -------------------------------------- | ----- | --------------------- |
| ⬜      | Respond to small sample size           |       | pilot framing         |
| ⬜      | Respond to failure cases               |       | new section/table     |
| ⬜      | Respond to conflicting/malicious input |       | failure analysis      |
| ⬜      | Respond to verifier repeated rejection |       | fallback discussion   |
| ⬜      | Respond to long-session concern        |       | long-session analysis |
| ⬜      | Respond to RQs not revisited           |       | new RQ section        |
| ⬜      | Respond to missing setup image         |       | new figure            |
| ⬜      | Respond to KG contribution not tested  |       | baseline              |
| ⬜      | Respond to repetition issue            |       | condensed discussion  |

## WP7.3 Reviewer 2 response

| Status | Task                                              | Owner | Notes                 |
| ------ | ------------------------------------------------- | ----- | --------------------- |
| ⬜      | Acknowledge N=3 limitation                        |       | do not argue too hard |
| ⬜      | Explain pilot/proof-of-concept framing            |       | throughout manuscript |
| ⬜      | Respond to weak RQ answers                        |       | new RQ section        |
| ⬜      | Respond to KG not demonstrated                    |       | baseline              |
| ⬜      | Respond to custom questionnaire                   |       | evaluation rationale  |
| ⬜      | Respond to lack of objective metrics              |       | new metrics           |
| ⬜      | Respond to no comparison with simpler alternative |       | LLM-only baseline     |
| ⬜      | Respond to strong conclusions                     |       | claims weakened       |

Acceptance criteria:

* Every reviewer point has a polite answer.
* Every answer mentions where the manuscript was changed.

---

# WP8 — Final submission

Goal: prepare final package.

Recommended owner: Both + Filip validation.

| Status | Task                              | Owner | Notes          |
| ------ | --------------------------------- | ----- | -------------- |
| ⬜      | Send revised manuscript to Filip  |       | for validation |
| ⬜      | Send rebuttal to Filip            |       | for validation |
| ⬜      | Apply Filip’s comments            |       | final edits    |
| ⬜      | Check journal format              |       | KI / Springer  |
| ⬜      | Submit editable source files only |       | Word or LaTeX  |
| ⬜      | Submit rebuttal/list of changes   |       | required       |
| ⬜      | Submit before 04 July 2026        |       | deadline       |

---

# Suggested parallel distribution

## Luca focus

1. WP1 — Code stabilization
2. WP2 — Experiments
3. WP3 — Figures
4. WP5 — Raw result tables

## Mehdi focus

1. WP4 — Paper restructuring
2. WP6 — Manuscript integration
3. WP7 — Rebuttal
4. WP8 — Final submission coordination

## Both

1. WP5 — Interpret results
2. WP6.2 — Final consistency check
3. Final meeting before submission

---

# Recommended execution order

## Day 1–2

* WP0 setup
* WP1 code stabilization starts
* WP4 paper reframing starts
* WP3 setup/architecture figures start

## Day 3–4

* WP2 baseline experiments
* WP2 long-session experiments
* WP4 RQ/CQ/evaluation sections

## Day 5

* WP5 results tables
* WP5 failure-case table
* WP6 manuscript integration

## Day 6

* WP7 rebuttal
* WP6 consistency check
* Send to Filip

## Final day

* Apply final comments
* Submit Word/LaTeX + rebuttal
