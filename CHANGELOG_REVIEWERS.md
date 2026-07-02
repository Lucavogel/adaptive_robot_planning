# Reviewer-Facing Change Log

This file summarizes manuscript changes made during the revision.

## Global Framing

- Reframed the manuscript as a prototype and exploratory pilot study.
- Clarified that the study with three participants is not a confirmatory validation.
- Weakened empirical claims in the Introduction, Evaluation, Results, Discussion, and Conclusion.
- Emphasized the system/architecture contribution over statistical claims.

## Introduction

- Rewrote RQ1-RQ3 to be more precise and answerable.
- Clarified that the empirical study is a pilot intended to assess feasibility and trade-offs.
- Revised contributions to focus on prototype architecture, actionable KG representation, pilot comparison, and system limitations.

## System Architecture

- Added a detailed neuro-symbolic architecture figure.
- Clarified the flow from perception to context package, KG retrieval, primary LLM, verifier, parser/execution, and planning-state update.
- Made optional modules and prototype constraints clearer.
- Softened claims around adaptation and affective sensing.

## Implementation

- Added a hardware/study setup figure with labels for object area, robot, and participant/control position.
- Added a concise caption explaining the setup.
- Clarified that object positions were fixed and predefined in the pilot.
- Clarified low-budget hardware/software setup.

## Pilot Evaluation

- Added an explicit evaluation rationale.
- Explained why the study uses N=3 and why this supports feasibility analysis only.
- Justified the custom questionnaire as prototype-specific.
- Acknowledged the limitation of non-validated questionnaire items.
- Added future-work note about validated instruments such as SUS, Godspeed-style measures, and trust/acceptance scales.

## Results

- Moved the comparative ratings figure to the Results section.
- Reported descriptive means and standard deviations without inferential claims.
- Condensed repeated interpretation of adaptivity versus smoothness.
- Added technical observations about KG/ConceptNet use, verifier effects, latency, and command grounding.

## Discussion

- Added "Answering the Research Questions" subsection.
- Added direct answers to RQ1, RQ2, and RQ3.
- Added "Failure Case Analysis" subsection and table.
- Added discussion of longer-session risks and context growth.
- Added explicit limitation that KG contribution is not isolated from general LLM ability.
- Framed LLM-only vs KG+LLM vs KG+LLM+verifier as future scenario-based ablation rather than completed evidence.

## Figures

- Added detailed architecture figure.
- Added physical hardware/study setup figure.
- Remaining decision: either remove the older compact architecture figure or clearly distinguish it from the detailed architecture figure.

## Remaining Consistency Fixes

- Harmonize object names across manuscript: prefer "water", "coffee", "banana", and "towel".
- Remove "chair" from pilot object lists if it was not part of the actual object setup.
- Avoid "water bottle" if the setup used a cup/glass of water.
- Mark failure-table entries as observed or anticipated, especially object hallucination.
- Final pass on abstract and conclusion to avoid overly strong language.

