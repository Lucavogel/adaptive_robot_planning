# Response to Editor and Reviewers

Dear Editor and Reviewers,

We thank you for the careful reading of our manuscript and for the constructive comments. We have revised the paper to frame the study more clearly as a prototype and exploratory pilot, to reduce unsupported claims, and to make the system architecture, evaluation rationale, failure modes, and research-question answers more explicit.

Below we provide a point-by-point response. Page and section references should be updated after the final Overleaf compilation.

## Response to the Editor

**Comment:** The three most important points are: (1) the small sample size and pilot framing, plus failure cases, long-term LLM usage findings if possible, and an LLM baseline comparison; (2) detailed answers to the competency/research questions; and (3) additional information, including an architecture image and evaluation explanation.

**Response:** We revised the manuscript to address these points. First, we strengthened the pilot/proof-of-concept framing throughout the abstract, introduction, pilot evaluation, results, discussion, and conclusion. We now state explicitly that the study with three participants is exploratory and not intended to support statistical generalization. Second, we added a dedicated discussion section answering the research questions directly. Third, we added visual material and setup information: a detailed architecture figure and a physical setup figure showing the robot, object area, and participant/control position. Fourth, we expanded the evaluation rationale, explaining why the pilot design and custom questionnaire were used and acknowledging the limitation of non-validated measures. Finally, we added a failure-case analysis and discussed longer-session limitations and the need for scenario-based LLM/KG ablations.

## Reviewer 1

### Small sample size and pilot framing

**Comment:** The pilot study involves only three participants. The authors handle this appropriately, but the paper should clearly remain a prototype/pilot study.

**Response:** We revised the manuscript to consistently frame the study as an exploratory pilot and proof-of-concept evaluation. We clarified that the user study is intended to assess feasibility, gather early user feedback, and identify interaction trade-offs rather than provide confirmatory evidence. We removed or softened stronger empirical wording and now report the quantitative results descriptively.

### Failure cases

**Comment:** The paper misses an opportunity to report failure cases: wrong calls, conflicting signals, malicious speech input, verifier rejection, etc.

**Response:** We added a dedicated failure-case analysis in the Discussion. The new table summarizes failure modes, examples, possible impact, and mitigation strategies, including invalid action prefixes, premature exercise transitions, repeated suggestions after refusal, conflicting input signals, irrelevant or malicious speech input, verifier rejection, latency spikes, pose detection failure, and KG coverage gaps. We distinguish participant-facing observations from anticipated deployment risks where appropriate.

### Long-session LLM behavior

**Comment:** The paper does not address whether LLM response quality degrades over longer sessions as context grows.

**Response:** We added a subsection on longer-session considerations. We explicitly discuss risks from growing interaction history, including prompt length, repeated suggestions, loss of earlier refusals, slower response times, and inconsistent interpretation of user state. We also identify context summarization and separate user-state memory as future mechanisms for handling longer sessions.

### Research questions not revisited

**Comment:** The research questions are posed in the introduction but never explicitly revisited.

**Response:** We added a subsection titled "Answering the Research Questions" in the Discussion. This section directly answers RQ1, RQ2, and RQ3, while keeping the interpretation appropriately limited by the pilot nature of the study.

### Missing hardware/study setup image

**Comment:** The paper contains no image of the hardware or study setup.

**Response:** We added a physical setup figure showing the task-relevant object area, the robotic platform, and the participant/control position. The caption explains the role of each labeled component.

### KG contribution not tested

**Comment:** The contribution of the knowledge graph is not tested; an LLM-only baseline would be informative.

**Response:** We now state this limitation explicitly. The revised Discussion explains that the current pilot does not isolate the KG's contribution from the LLM's general commonsense ability. We identify a scenario-based ablation as the natural next evaluation, comparing LLM-only, KG+LLM, and KG+LLM+verifier variants using metrics such as action correctness, valid-prefix rate, object grounding, unsafe/incoherent response rate, and latency.

### Repetition of adaptivity-versus-smoothness trade-off

**Comment:** The paper repeats the same adaptivity-versus-smoothness trade-off in several places.

**Response:** We condensed repeated interpretation across the Results, Discussion, and Conclusion. The revised Results now report the descriptive pattern once, and the Discussion focuses on the broader design implication: adaptive guidance should be treated as a design space rather than assumed to be uniformly preferable.

## Reviewer 2

### Small sample and insufficient empirical validation

**Comment:** The evaluation with only three participants cannot support strong conclusions about user perceptions, usability, effectiveness, or acceptance.

**Response:** We agree. We revised the manuscript to avoid presenting the pilot as empirical validation. The revised Evaluation and Results sections explicitly state that the sample size does not support statistical generalization or strong claims about effectiveness. The study is now presented as a feasibility and user-feedback pilot that informs future evaluation design.

### Research questions not properly answered

**Comment:** The paper formulates RQ1-RQ3 but does not rigorously answer them.

**Response:** We added a dedicated "Answering the Research Questions" subsection in the Discussion. We now answer RQ1 in terms of the proposed bounded neuro-symbolic architecture, RQ2 in terms of task-oriented KG representation and LLM prompt integration, and RQ3 in terms of the limited descriptive pilot observations.

### Custom questionnaire lacks validation

**Comment:** The quantitative evaluation relies on a custom questionnaire without validity or reliability evidence.

**Response:** We revised the Evaluation section to explain why a custom questionnaire was used in this pilot: the study focused on prototype-specific dimensions such as perceived adaptation and object relevance. We also explicitly acknowledge that these are not validated psychometric scales and that future work should use or combine validated instruments such as SUS, Godspeed-style measures, and trust/acceptance scales.

### Lack of objective metrics

**Comment:** The evaluation relies almost exclusively on subjective self-report measures.

**Response:** We added a subsection describing technical and interaction observations, including response latency, verifier edits, command-format issues, object-pointing behavior, and exercise progression events. We present these as diagnostic implementation-level observations rather than a fully powered objective evaluation.

### Neuro-symbolic framework not compared with simpler alternatives

**Comment:** The manuscript does not demonstrate measurable advantages over simpler alternatives.

**Response:** We now state this limitation explicitly. The revised Discussion notes that the current pilot does not prove that KG-grounded reasoning outperforms an LLM-only baseline. We identify a scenario-based ablation as a natural next evaluation.

### Strong conclusions

**Comment:** The conclusions are too strong relative to the empirical evidence.

**Response:** We weakened the language in the abstract, results, discussion, and conclusion. We now use terms such as "pilot observations", "descriptive pattern", and "suggest" rather than stronger causal or confirmatory wording.

## Remaining Final Checks Before Submission

- Update page/section references after final PDF compilation.
- Ensure all object names are consistent: use "water", "coffee", "banana", and "towel"; avoid "chair" and "water bottle" unless actually present.
- If both architecture figures are retained, explain clearly that one is a compact control-loop overview and the other is a detailed implementation pipeline.
- Ensure the failure-case table distinguishes observed issues from anticipated deployment risks.
- Ensure the revised abstract and conclusion use cautious pilot-study language.

