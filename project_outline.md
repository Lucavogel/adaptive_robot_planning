1  Introduction
• Context and motivation
• Problem statement
• Objectives of the project
• Contributions

2  Related Work
Assistive robotics for physical guidance
📄 Tozadore et al. (2023) – Showed how scripted stretching robots improve focus and reduce stress.
📄 Lamsey et al. (2025) – Parkinson rehab robot with adaptive routines.
• Commonsense reasoning and knowledge graphs
📄 Ilievski et al. (2021) – Defined 13 dimensions of commonsense knowledge, structuring robot reasoning.
📄 Ding et al. (2023) – COWP – Coupling a planner with a LLM that fills commonsense-based action gaps.
📄 Zhang et al. (2022) – Generating scene context with LLM + visual knowledge.
📄 ATOMIC, ConceptNet – Core resources for causal and relational commonsense.
• Multimodal interaction in HRI
📄 Kaushik et al. (2025) – Adaptive robot feedback based on user emotion and posture.
📄 Irfan et al. (2020) – Robots adjusting behavior to user fatigue and bio-signals.
• LLM-based planning and reasoning
📄 Ahn et al. (2022) – SayCan – LLM + affordance system to propose feasible robotic plans.
📄 Huang et al. (2022) – Inner monologue helps LLMs revise their own plan in real time.
📄 ACL 2023 Survey – Explores strengths/weaknesses of LLM reasoning.
📄 LLMs Can’t Plan (ICML 2024) – Critiques planning with LLMs, proposes hybrid approaches.
📄 AKR3 (2024) – Knowledge engineering for robot manipulation in daily tasks.

3  System Architecture
• Overview of the pipeline
• Perception modules (voice, posture, emotion, object)
• Reasoning (LLM + Knowledge Graph)
• Planning and adaptation
• Interaction control (robot arm, voice, pointing)

4 Implementation
• Software stack (ROS2, Python, LLM API, etc.)
• Prompt engineering and response format
• Knowledge representation (KG structure and usage)

5  User Evaluation
• Experimental design (scripted vs adaptive)
• Participant demographics
• Evaluation metrics (questionnaire + observation)
• Data collection and analysis

6  Results and Discussion
• Quantitative and qualitative findings
• Comparison of versions
• Strengths and limitations
• Insights from user feedback

7  Conclusion and Perspectives
• Summary of findings
• Implications for assistive robotics
• Future work (posture detection, gesture generation, large-scale testing)

8 Annexes
• Evaluation materials
• Prompts and model outputs
• Diagrams and code snippets
• Video demo links