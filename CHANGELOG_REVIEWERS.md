# Reviewer-Facing Change Log

This document summarizes the main revisions made to the manuscript in response to the editor and reviewer comments.

## Global Framing

- Reframed the manuscript as a prototype system paper with an exploratory pilot study, not a confirmatory user evaluation.
- Clarified throughout the Abstract, Introduction, Evaluation, Results, Discussion, and Conclusion that the participant study has a small sample size (N=3) and should not be used for statistical generalization.
- Softened empirical claims by using cautious language such as "pilot observations", "descriptive", "exploratory", and "diagnostic".
- Emphasized the main contribution as the neuro-symbolic architecture and actionable knowledge representation, with the user study serving as a feasibility and interaction-tradeoff assessment.

## Abstract and Conclusion

- Replaced stronger wording about improvement/evidence with cautious pilot-study wording.
- Added a brief statement that adaptive guidance was rated higher for contextual relevance in this small sample, while scripted guidance remained competitive for smoothness and predictability.
- Added the new 30-scenario prompt-level ablation result to the conclusion.
- Clarified that the system remains an early prototype requiring larger, longer-term evaluations.

## Introduction

- Rewrote the research questions to better match the contribution and evaluation scope.
- Clarified that the work studies a bounded adaptive architecture rather than proving general assistive-robot effectiveness.
- Revised the contribution list to include:
  - prototype adaptive stretching robot framework,
  - task-oriented actionable KG representation,
  - exploratory pilot comparison,
  - limitations and failure-mode analysis.

## System Architecture

- Replaced the original architecture figure with a revised four-stage architecture figure organized around Perception, Reasoning, Action Execution, and Planning and Adaptation.
- Integrated the detailed per-turn KG/LLM/verifier/parser flow inside the Reasoning stage of the new Figure 1, so the figure now preserves the manuscript's original four-stage structure while adding the reviewer-requested implementation detail.
- Added a dashed feedback arrow to show how execution feedback updates the context, routine state, and interaction history for the next interaction turn.
- Clarified the information flow from perception to context construction, KG retrieval, primary LLM reasoning, verifier, command parser/execution, and planning-state update.
- Clarified the verifier as a safeguard for command-format checking, object-availability filtering, and safety-related corrections.
- Made optional/prototype components clearer, especially affective sensing and verifier use.

## Implementation and Setup

- Added a real physical setup figure showing:
  - task-relevant object area,
  - robot arm,
  - participant/control position.
- Clarified that object positions were fixed and predefined in the pilot.
- Harmonized object naming to use water, coffee, banana, and towel.
- Removed misleading references to a chair as a pilot object where it was not part of the setup.
- Clarified low-budget hardware and software dependencies.

## Competency Questions

- Added a dedicated competency-question section.
- Defined expected reasoning behaviors for:
  - fatigue support,
  - pain response,
  - refusal memory,
  - exercise transition,
  - object availability,
  - command validity,
  - unsafe request handling,
  - KG coverage gaps.
- Linked these competency questions to the KG, prompt, verifier, command parser, and fallback behavior.

## Pilot Evaluation

- Added an explicit evaluation-design rationale.
- Explained that the N=3 pilot is intended for feasibility and early feedback only.
- Clarified that the custom questionnaire is prototype-specific and not a validated psychometric instrument.
- Added future-work notes about using validated HRI/usability instruments such as SUS, Godspeed-style measures, and trust/acceptance scales.
- Added implementation-level observations as diagnostic measures, including response latency, verifier edits, command-format issues, object-pointing behavior, and exercise progression.

## Results

- Reported descriptive means and standard deviations without inferential testing.
- Kept the interpretation of adaptive-vs-scripted guidance cautious.
- Added a new subsection on prompt-level ablation of KG and verifier contributions.
- Added a compact ablation table over 30 scripted scenarios:
  - LLM-only: 18/30 correct actions,
  - KG+LLM: 21/30 correct actions,
  - KG+LLM+Verifier: 30/30 correct actions.
- Added a methodological note that correctness was manually assessed against predefined expected actions.
- Clarified that the scenario ablation is diagnostic and separate from the human pilot study.

## Discussion

- Added a direct "Answering the Research Questions" subsection.
- Updated RQ2 to mention the completed prompt-level ablation rather than treating it as only future work.
- Added a "Knowledge Graph and Verifier Contribution" subsection.
- Clarified that KG retrieval alone provided moderate grounding benefits, while verifier-supported checking was needed to eliminate invalid executable actions and unavailable-object commands.
- Added a failure-case analysis table covering:
  - object hallucination,
  - invalid action prefixes,
  - premature exercise transitions,
  - repeated suggestions after refusal,
  - conflicting signals,
  - malicious or irrelevant speech input,
  - repeated verifier rejection,
  - latency spikes,
  - pose detection failure,
  - KG coverage gaps.
- Added longer-session considerations, including prompt growth, repeated suggestions, loss of refusals, latency, and consistency of user-state interpretation.

## Appendix

- Added Appendix A with an example system prompt.
- Added Appendix B with the verifier prompt used in the prompt-level ablation.
- Formatted prompt appendices consistently.

## References and Consistency Fixes

- Checked object naming consistency across the text.
- Identified DOI formatting issues where references contained duplicated DOI URL prefixes; these should be corrected in the bibliography source before final submission.
- Verified that Figure 1 now serves as both the system-level overview and the detailed KG/LLM/verifier interaction pipeline, avoiding duplicate architecture figures.

## Submission Notes

- The revised manuscript should be submitted as editable source files, not PDF only.
- The final response letter should be submitted together with this change log or incorporated into it.
