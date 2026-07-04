# Response to Editor and Reviewers

Dear Editor and Reviewers,

We thank you for the careful reading of our manuscript and for the constructive comments. We have revised the paper substantially. The revised version now frames the work explicitly as a prototype system paper with an exploratory pilot study, adds a clearer architecture and setup description, includes competency questions, adds a prompt-level LLM/KG/verifier ablation, and expands the discussion of limitations, failure modes, and future evaluation needs.

Below we provide a point-by-point response. Section references should be checked once more after the final Overleaf compilation.

## Response to the Editor

**Comment:** The three most important points are: (1) the small sample size and pilot framing, plus failure cases, long-term LLM usage findings if possible, and an LLM baseline comparison; (2) detailed answers to the competency questions; and (3) additional information, including an architecture image and evaluation explanation.

**Response:** We addressed these points in the revised manuscript. First, we strengthened the pilot/prototype framing throughout the paper and now explicitly state that the N=3 user study is exploratory and not intended for statistical generalization. Second, we added competency questions describing the expected reasoning behavior of the system, including fatigue support, pain response, refusal memory, exercise transitions, unavailable objects, invalid commands, unsafe requests, and KG coverage gaps. Third, we replaced the architecture figure with a revised four-stage architecture that also details the KG/LLM/verifier/parser flow inside the Reasoning stage, and we added a physical setup figure. Fourth, we added an evaluation-design rationale explaining why the pilot and custom questionnaire were used. Fifth, we added a prompt-level ablation over 30 scripted scenarios comparing LLM-only, KG+LLM, and KG+LLM+verifier conditions. Finally, we expanded the failure-case and longer-session discussion.

## Reviewer 1

### Small sample size and pilot framing

**Comment:** The pilot study involves only three participants. The paper should clearly remain a prototype/pilot study.

**Response:** We revised the manuscript to consistently frame the human evaluation as an exploratory pilot and feasibility study. The Abstract, Introduction, Evaluation, Results, Discussion, and Conclusion now avoid confirmatory claims. We report the user ratings descriptively and explicitly state that the sample size does not support statistical generalization.

### Failure cases

**Comment:** The paper should report failure cases such as wrong calls, conflicting signals, malicious input, and verifier rejection.

**Response:** We added a dedicated failure-case analysis table. It lists failure modes, examples, potential impact, and mitigation strategies, including object hallucination, invalid action prefixes, premature exercise transition, repeated suggestions after refusal, conflicting input signals, malicious or irrelevant speech input, repeated verifier rejection, latency spikes, pose detection failure, and KG coverage gaps.

### Long-session LLM behavior

**Comment:** The paper does not address whether LLM response quality degrades over longer sessions as context grows.

**Response:** We added a longer-session considerations subsection. It discusses prompt growth, repeated suggestions, loss of earlier refusals, slower response times, and inconsistent user-state interpretation. We also identify context summarization, separate user-state memory, and longer-session evaluations as future work.

### Research questions not revisited

**Comment:** The research questions are posed but not explicitly revisited.

**Response:** We added a subsection titled "Answering the Research Questions". This section directly answers RQ1, RQ2, and RQ3 while keeping the interpretation limited by the pilot nature of the user study.

### Missing hardware/study setup image

**Comment:** The paper contains no image of the hardware or study setup.

**Response:** We added a physical setup figure showing the task-relevant object area, the robotic arm, and the participant/control position. The caption explains each labeled part of the setup.

### KG contribution not tested

**Comment:** The paper does not test the contribution of the KG; an LLM-only baseline would be informative.

**Response:** We added a prompt-level ablation over 30 scripted interaction scenarios. The ablation compares three configurations: LLM-only, KG+LLM, and KG+LLM+verifier. The LLM-only condition selected the expected action in 18/30 scenarios, KG+LLM in 21/30 scenarios, and KG+LLM+verifier in 30/30 scenarios. We explicitly frame this as a diagnostic prompt-level analysis rather than a user-study result. The revised discussion explains that KG retrieval provides moderate grounding benefits, while verifier-supported checking helps enforce executable command structure and object-availability constraints.

### Repetition of adaptivity-versus-smoothness trade-off

**Comment:** The adaptivity-versus-smoothness trade-off is repeated several times.

**Response:** We condensed repeated interpretation across the Results, Discussion, and Conclusion. The revised manuscript reports the descriptive pattern once and then discusses the broader design implication: adaptive guidance should be treated as a design space rather than assumed to be uniformly preferable.

## Reviewer 2

### Small sample and insufficient empirical validation

**Comment:** The evaluation with only three participants cannot support strong conclusions about user perceptions, usability, effectiveness, or acceptance.

**Response:** We agree and revised the paper accordingly. The pilot is now described as a feasibility and user-feedback study. We removed strong claims and now use cautious terms such as "pilot observations", "descriptive pattern", and "exploratory". The Results section reports descriptive statistics without inferential testing.

### Research questions not properly answered

**Comment:** The paper formulates RQ1-RQ3 but does not rigorously answer them.

**Response:** We added a dedicated subsection answering each RQ. RQ1 is answered through the bounded neuro-symbolic architecture. RQ2 is answered through the task-oriented KG representation, prompt integration, and diagnostic ablation. RQ3 is answered through the limited descriptive pilot observations comparing scripted and adaptive guidance.

### Competency questions

**Comment:** The competency questions should be answered explicitly.

**Response:** We added a competency-question section. It lists representative questions and expected behaviors covering fatigue support, pain response, refusal memory, exercise transitions, object availability, command validity, unsafe requests, and KG coverage gaps. These questions make explicit what the KG, prompt, verifier, and parser are expected to support.

### Custom questionnaire lacks validation

**Comment:** The quantitative evaluation relies on a custom questionnaire without validity or reliability evidence.

**Response:** We revised the Evaluation section to explain that the custom questionnaire was used because this prototype targeted specific dimensions such as perceived adaptation and object relevance. We explicitly acknowledge that these items are not validated psychometric scales and state that future studies should include validated instruments such as SUS, Godspeed-style measures, and established trust or acceptance scales.

### Lack of objective metrics

**Comment:** The evaluation relies almost exclusively on subjective self-report measures.

**Response:** We added a subsection on technical and interaction measures, including response latency, verifier edits, command-format issues, object-pointing behavior, and exercise progression events. We present these as diagnostic implementation-level observations rather than as a fully powered objective evaluation.

### Neuro-symbolic framework not compared with simpler alternatives

**Comment:** The manuscript does not demonstrate measurable advantages over simpler alternatives.

**Response:** We added a prompt-level ablation comparing LLM-only, KG+LLM, and KG+LLM+verifier conditions over 30 scripted scenarios. This provides an initial diagnostic comparison with simpler alternatives. The results show higher action-selection correctness for KG+LLM than LLM-only, and perfect executable-action correctness in the tested scenarios when the verifier stage is included. We state clearly that this is not a substitute for a larger embodied evaluation.

### Strong conclusions

**Comment:** The conclusions are too strong relative to the empirical evidence.

**Response:** We weakened the Abstract, Results, Discussion, and Conclusion. The conclusion now states that the results are exploratory evidence from an early prototype rather than statistically validated proof of effectiveness. We also added future-work needs for larger samples, longer sessions, validated HRI measures, objective interaction metrics, and broader comparisons against scripted and LLM-only baselines.

## Additional Revisions

- Harmonized the object list in the setup and evaluation sections to water, coffee, banana, and towel.
- Removed misleading references to a chair as a pilot object where it was not part of the actual setup.
- Replaced "water bottle" wording with water / cup or glass of water where appropriate.
- Replaced the original architecture figure with a revised Figure 1 that keeps the four main stages while adding the detailed KG/LLM/verifier/parser interaction loop inside the Reasoning stage.
- Added Appendix A with an example system prompt.
- Added Appendix B with the verifier prompt used in the prompt-level ablation.
- Added a note after the ablation table explaining that correctness was manually assessed against predefined expected actions.
- Updated the Conclusion to include the 30-scenario ablation while keeping cautious pilot-study language.

## Final Checks Before Submission

- Ensure Overleaf source compiles cleanly.
- Correct DOI entries in the bibliography that contain duplicated DOI URL prefixes.
- Verify that command names in Appendix B preserve underscores, e.g., `NEXT\_EXERCISE`, `POINT\_WATER`, and `STOP\_ROUTINE`.
- Submit editable source files as requested by the editor.
