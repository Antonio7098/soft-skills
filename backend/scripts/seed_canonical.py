"""Seed canonical data from ops/resources/ into a fresh database."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime


def _uid() -> str:
    return uuid.uuid4().hex[:32]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
SKILLS = [
    (
        "active-listening",
        "Active Listening",
        "Fully concentrating on what someone is saying, reflecting, paraphrasing, and summarising to ensure understanding.",
    ),
    (
        "structured-thinking",
        "Structured Thinking",
        "Breaking down complex problems into logical components using frameworks and mental models.",
    ),
    (
        "professional-scepticism",
        "Professional Scepticism",
        "Challenging assumptions politely and verifying information without cynicism.",
    ),
    (
        "asking-the-right-questions",
        "Asking the Right Questions",
        "Using open, probing, and closed questions to uncover requirements and hidden concerns.",
    ),
    (
        "translating-business-tech",
        "Translating Business & Tech",
        "Explaining technical possibilities to non-technical stakeholders and business constraints to technical teams.",
    ),
    (
        "stakeholder-analysis",
        "Stakeholder Analysis",
        "Identifying stakeholders, mapping their power/interest, and understanding their needs.",
    ),
    (
        "stakeholder-engagement",
        "Stakeholder Engagement",
        "Tailoring communication, frequency, and involvement to different stakeholder groups.",
    ),
    (
        "conflict-facilitation",
        "Conflict Facilitation",
        "Making conflicts visible, facilitating resolution without taking sides, and escalating when needed.",
    ),
    (
        "rasci-clarity",
        "RASCI Clarity",
        "Defining roles and responsibilities using the RASCI model, ensuring one accountable per task.",
    ),
    (
        "interview-structuring",
        "Interview Structuring",
        "Planning, conducting, and following up on interviews with a clear agenda and active listening.",
    ),
    (
        "active-questioning",
        "Active Questioning",
        "Applying open, probing, and closed questions appropriately in conversations.",
    ),
    (
        "paraphrasing-reflecting",
        "Paraphrasing & Reflecting",
        "Restating what was said and acknowledging emotions to confirm understanding.",
    ),
    (
        "note-taking-validation",
        "Note-Taking & Validation",
        "Recording accurate notes and validating them with the interviewee.",
    ),
    (
        "starr-framework",
        "STARR Framework",
        "Structuring answers with Situation, Task, Action, Result, Reflection.",
    ),
    ("storytelling", "Storytelling", "Crafting compelling narratives that engage and persuade."),
    (
        "self-reflection",
        "Self-Reflection",
        "Analysing one's own experiences to extract lessons and growth opportunities.",
    ),
    (
        "growth-mindset",
        "Growth Mindset",
        "Embracing challenges, viewing failure as learning, and seeking feedback.",
    ),
    (
        "proactivity",
        "Proactivity",
        "Taking initiative beyond the explicit task, thinking one step ahead.",
    ),
    (
        "curiosity",
        "Curiosity",
        "Asking questions, seeking to understand, and learning continuously.",
    ),
    (
        "ambiguity-navigation",
        "Navigating Ambiguity",
        "Making progress with incomplete information, asking clarifying questions, and documenting assumptions.",
    ),
    (
        "prioritisation",
        "Prioritisation",
        "Using frameworks (e.g., Eisenhower) to sort tasks and focus on what matters.",
    ),
    (
        "yes-with-conditions",
        "Yes, With Conditions",
        "Negotiating workload by setting clear boundaries, deadlines, and trade-offs.",
    ),
    (
        "escalation",
        "Escalation",
        "Raising issues with evidence and a clear call to action when options are exhausted.",
    ),
    (
        "professionalism-under-pressure",
        "Professionalism Under Pressure",
        "Staying calm, managing emotions, and responding constructively in tense situations.",
    ),
    (
        "feedback-receiving",
        "Receiving Feedback",
        "Responding to feedback without defensiveness, using frameworks (ARCA, 3R, CARE).",
    ),
    (
        "feedback-asking",
        "Asking for Feedback",
        "Proactively seeking specific, forward-looking feedback.",
    ),
    (
        "emotional-regulation",
        "Emotional Regulation",
        "Recognising and managing one's emotional reactions (fight/flight/freeze).",
    ),
    (
        "change-management",
        "Change Management",
        "Supporting people through transitions, addressing resistance, and enabling adoption.",
    ),
    (
        "business-case-development",
        "Business Case Development",
        "Justifying investments with cost-benefit analysis, risks, and benefits.",
    ),
    (
        "requirements-engineering",
        "Requirements Engineering",
        "Capturing, modelling, and managing requirements throughout a project.",
    ),
    (
        "presentation-facilitation",
        "Presentation & Facilitation",
        "Delivering clear, engaging presentations and facilitating group discussions.",
    ),
    (
        "concise-explanation",
        "Concise Explanation",
        "Communicating complex ideas clearly and briefly, with key takeaways.",
    ),
    (
        "empathy",
        "Empathy",
        "Understanding and acknowledging others' perspectives, emotions, and motivations.",
    ),
    (
        "expectation-setting",
        "Expectation Setting",
        "Agreeing on scope, deliverables, and timelines upfront to avoid surprises.",
    ),
    (
        "negotiation",
        "Negotiation",
        "Finding mutually acceptable solutions while maintaining relationships.",
    ),
    (
        "executive-summary",
        "Executive Summary",
        "Distilling information into a high-level summary suitable for senior stakeholders.",
    ),
    (
        "decision-justification",
        "Decision Justification",
        "Explaining the rationale behind decisions with evidence and trade-offs.",
    ),
    (
        "stakeholder-management",
        "Stakeholder Management",
        "Identifying, analysing, engaging, and managing stakeholders throughout a project lifecycle.",
    ),
]

# ---------------------------------------------------------------------------
# Competencies
# ---------------------------------------------------------------------------
COMPETENCIES = [
    (
        "consulting-mindset",
        "Consulting Mindset",
        "Applying objectivity, structured thinking, and a gap-based approach to help others make better decisions.",
    ),
    (
        "stakeholder-management",
        "Stakeholder Management",
        "Identifying, analysing, engaging, and managing stakeholders throughout a project lifecycle.",
    ),
    (
        "effective-communication",
        "Effective Communication",
        "Conveying information clearly and persuasively through writing, speaking, and listening.",
    ),
    (
        "client-site-professionalism",
        "Client Site Professionalism",
        "Navigating the client environment with confidence, handling ambiguity, and maintaining trust.",
    ),
    (
        "feedback-receptivity",
        "Feedback Receptivity",
        "Actively seeking, receiving, and applying feedback to grow professionally.",
    ),
    (
        "problem-solving-under-ambiguity",
        "Problem Solving Under Ambiguity",
        "Analysing complex, poorly defined problems and moving forward with incomplete information.",
    ),
    (
        "project-delivery",
        "Project Delivery",
        "Contributing to successful project outcomes through requirements, change, and business case skills.",
    ),
    (
        "professional-growth",
        "Professional Growth",
        "Demonstrating curiosity, proactivity, and a commitment to continuous learning.",
    ),
]

# ---------------------------------------------------------------------------
# Competency -> Skill mappings (competency_slug, skill_slug, weight)
# ---------------------------------------------------------------------------
COMPETENCY_SKILL_MAP = [
    # consulting-mindset
    ("consulting-mindset", "structured-thinking", 0.3),
    ("consulting-mindset", "professional-scepticism", 0.2),
    ("consulting-mindset", "asking-the-right-questions", 0.2),
    ("consulting-mindset", "translating-business-tech", 0.2),
    ("consulting-mindset", "change-management", 0.1),
    # stakeholder-management
    ("stakeholder-management", "stakeholder-analysis", 0.2),
    ("stakeholder-management", "stakeholder-engagement", 0.2),
    ("stakeholder-management", "active-listening", 0.15),
    ("stakeholder-management", "empathy", 0.15),
    ("stakeholder-management", "expectation-setting", 0.1),
    ("stakeholder-management", "conflict-facilitation", 0.1),
    ("stakeholder-management", "rasci-clarity", 0.1),
    # effective-communication
    ("effective-communication", "structured-thinking", 0.15),
    ("effective-communication", "concise-explanation", 0.15),
    ("effective-communication", "executive-summary", 0.1),
    ("effective-communication", "storytelling", 0.1),
    ("effective-communication", "active-listening", 0.1),
    ("effective-communication", "paraphrasing-reflecting", 0.1),
    ("effective-communication", "interview-structuring", 0.1),
    ("effective-communication", "active-questioning", 0.1),
    ("effective-communication", "presentation-facilitation", 0.1),
    # client-site-professionalism
    ("client-site-professionalism", "ambiguity-navigation", 0.2),
    ("client-site-professionalism", "prioritisation", 0.2),
    ("client-site-professionalism", "yes-with-conditions", 0.2),
    ("client-site-professionalism", "escalation", 0.15),
    ("client-site-professionalism", "professionalism-under-pressure", 0.15),
    ("client-site-professionalism", "emotional-regulation", 0.1),
    # feedback-receptivity
    ("feedback-receptivity", "feedback-receiving", 0.3),
    ("feedback-receptivity", "feedback-asking", 0.25),
    ("feedback-receptivity", "growth-mindset", 0.25),
    ("feedback-receptivity", "self-reflection", 0.2),
    # problem-solving-under-ambiguity
    ("problem-solving-under-ambiguity", "ambiguity-navigation", 0.25),
    ("problem-solving-under-ambiguity", "structured-thinking", 0.25),
    ("problem-solving-under-ambiguity", "starr-framework", 0.2),
    ("problem-solving-under-ambiguity", "asking-the-right-questions", 0.2),
    ("problem-solving-under-ambiguity", "decision-justification", 0.1),
    # project-delivery
    ("project-delivery", "requirements-engineering", 0.25),
    ("project-delivery", "change-management", 0.2),
    ("project-delivery", "business-case-development", 0.2),
    ("project-delivery", "stakeholder-management", 0.2),
    ("project-delivery", "presentation-facilitation", 0.15),
    # professional-growth
    ("professional-growth", "curiosity", 0.3),
    ("professional-growth", "proactivity", 0.3),
    ("professional-growth", "growth-mindset", 0.2),
    ("professional-growth", "self-reflection", 0.2),
]


# ---------------------------------------------------------------------------
# Rubrics (id, skill_slug, name, content_type, schema_version, criteria)
# ---------------------------------------------------------------------------
RUBRICS = [
    {
        "id": "active-listening@v1",
        "skill_slug": "active-listening",
        "name": "Active Listening in a Consulting Conversation",
        "content_type": "quick_practice_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "active-listening-reflect",
                "skill_slug": "active-listening",
                "title": "Reflecting stakeholder signals",
                "description": "The learner demonstrates they have heard and understood what the stakeholder said, including emotional tone.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Does not reflect stakeholder concerns; may ignore or misinterpret.",
                            "examples": [
                                "I think the main issue is the timeline. We should just move forward."
                            ],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Shows limited reflection, mostly repeating facts without acknowledging deeper meaning.",
                            "examples": ["So you said the data team is busy, got it."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Partially reflects concerns but misses subtle signals or emotions.",
                            "examples": [
                                "So what I'm hearing is you're worried about the handoff, but we'll manage it."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Accurately reflects key points and acknowledges emotions.",
                            "examples": [
                                "It sounds like the handoff is causing frustration because it slows things down and adds extra work. Is that right?"
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Clearly reflects both content and emotional signals, demonstrating deep understanding.",
                            "examples": [
                                "Let me make sure I understand. The handoff to compliance is taking three days, which is delaying your KYC process. It feels like a bottleneck, and you're concerned it's affecting customer satisfaction. Is that the core challenge?"
                            ],
                        }
                    },
                ],
            },
            {
                "criterion_ref": "active-listening-paraphrase",
                "skill_slug": "paraphrasing-reflecting",
                "title": "Paraphrasing and summarising",
                "description": "The learner restates what the stakeholder said in their own words to confirm understanding.",
                "weight": 1.0,
                "required": True,
                "position": 2,
                "levels": [
                    {
                        "level_1": {
                            "description": "Does not paraphrase or summarise; moves on without confirmation.",
                            "examples": ["Okay, next question."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Attempts to summarise but misses key details or introduces inaccuracies.",
                            "examples": ["So you want better reporting tools."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Summarises the main point, but omits nuance.",
                            "examples": [
                                "So you're saying the current tools are inconsistent across departments."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Summarises accurately and checks for understanding.",
                            "examples": [
                                "So to recap, each department currently uses different reporting tools, and that's making it hard to share data and collaborate. Is that correct?"
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Summarises comprehensively and invites confirmation or correction.",
                            "examples": [
                                "Let me summarise what I've heard so far. You have 80 data specialists spread across eight departments, each using their own tools, and you've seen issues with knowledge sharing and talent retention. You're hoping that centralisation will give you standardised practices, clearer career paths, and a competitive edge. Have I captured that correctly?"
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "structured-thinking@v1",
        "skill_slug": "structured-thinking",
        "name": "Applying Structured Thinking to a Problem",
        "content_type": "scenario_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "structured-thinking-framework",
                "skill_slug": "structured-thinking",
                "title": "Uses a framework to decompose the problem",
                "description": "The learner applies a mental model (e.g., As-Is -> Gap -> To-Be, SWOT, PESTLE) to break down the problem logically.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "No framework; jumps to solutions without analysis.",
                            "examples": ["We should just hire more data specialists."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Mentions a framework superficially but does not apply it consistently.",
                            "examples": ["We could look at the current state and then decide."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Uses a framework but misses some key components.",
                            "examples": [
                                "The current situation is that data is scattered. We want centralisation. The gap is we need to move people and tools."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Applies a framework with clear structure, covering all main elements.",
                            "examples": [
                                "Let's map this using As-Is / Gap / To-Be. As-Is: data specialists are decentralised, using different tools, with no standardisation. To-Be: a centralised hub with common tools and career paths. The gap includes physical relocation, tool migration, and cultural change."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Applies a framework with nuance, identifies multiple dimensions, and uses it to guide next steps.",
                            "examples": [
                                "I'd approach this using a structured framework. First, I'd document the As-Is: people, processes, tools, and culture across departments. Then I'd define the To-Be based on business objectives: a centralised hub that improves collaboration and retention. The gap analysis would break down into four areas: organisational design, technology standardisation, change management, and talent development. For each, I'd identify specific tasks and risks."
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "asking-the-right-questions@v1",
        "skill_slug": "asking-the-right-questions",
        "name": "Asking the Right Questions to Uncover Requirements",
        "content_type": "scenario_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "question-types",
                "skill_slug": "active-questioning",
                "title": "Uses a mix of open, probing, and closed questions",
                "description": "The learner chooses question types appropriate to the situation to gather information effectively.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Uses mostly closed or leading questions; fails to explore.",
                            "examples": ["Don't you think the system is too slow?"],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Uses some open questions but does not probe deeper.",
                            "examples": ["Tell me about your role. Do you like it?"],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Uses open questions and some probing, but misses follow-up opportunities.",
                            "examples": [
                                "How do you currently process data requests? ... What tools do you use?"
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Effectively sequences open, probing, and closed questions to gather detailed information.",
                            "examples": [
                                "Tell me about how you handle data requests today. (Open) ... You mentioned the handoff to compliance is slow. Can you walk me through what happens at that point? (Probing) ... So does the delay typically happen before or after the KYC check? (Closed)"
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Exemplary questioning: uses silence, builds on previous answers, and uncovers hidden issues.",
                            "examples": [
                                "Tell me about a typical day when a data request comes in. (Open) ... You mentioned you have to chase compliance. How do you usually follow up? (Probing) ... (Pause) ... You're nodding, but it sounds like that process frustrates your team. What would make it smoother? (Empathetic probe)"
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "ambiguity-navigation@v1",
        "skill_slug": "ambiguity-navigation",
        "name": "Navigating Ambiguous Requests",
        "content_type": "quick_practice_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "clarifying-questions",
                "skill_slug": "asking-the-right-questions",
                "title": "Asks clarifying questions when direction is unclear",
                "description": "The learner identifies what is ambiguous and asks specific questions to reduce uncertainty.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Does not ask clarifying questions; proceeds with guesswork.",
                            "examples": ["Okay, I'll get you something by tomorrow."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Asks a very broad question that doesn't narrow ambiguity.",
                            "examples": ["What exactly do you need?"],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Asks one or two relevant clarifying questions but misses important details.",
                            "examples": ["What format would you like the numbers in?"],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Asks a set of targeted questions to clarify purpose, scope, and format.",
                            "examples": [
                                "To make sure I give you something useful, could you tell me: (1) What metrics would be most helpful for the steering meeting? (2) Is a one-page summary enough, or would you prefer a slide deck? (3) When do you need it by?"
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Clarifies not just what but why, and proposes next steps to align.",
                            "examples": [
                                "I want to make sure this meets your needs for the steering meeting. Could you help me understand what the key discussion points will be, so I can tailor the numbers accordingly? Also, what's the most helpful format - a slide with key trends, or a more detailed dashboard? I can have a draft by 2pm tomorrow; if you need it earlier, I can prioritise a high-level summary by end of day - which would work better?"
                            ],
                        }
                    },
                ],
            },
            {
                "criterion_ref": "progress-with-info",
                "skill_slug": "ambiguity-navigation",
                "title": "Makes progress with incomplete information",
                "description": "The learner moves forward despite ambiguity, documenting assumptions and iterating.",
                "weight": 1.0,
                "required": True,
                "position": 2,
                "levels": [
                    {
                        "level_1": {
                            "description": "Stops working until ambiguity is resolved.",
                            "examples": ["I can't start until I get more details."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Makes assumptions but does not document or communicate them.",
                            "examples": ["I'll assume they want last month's figures."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Makes assumptions and mentions them in passing.",
                            "examples": [
                                "I'm going to assume we're looking at Q2 numbers. Let me know if that's not right."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Documents assumptions clearly and shares them for alignment.",
                            "examples": [
                                "To move forward, I've assumed we'll focus on digital sales performance, using Q2 data. I've documented this in the shared folder. If those assumptions are wrong, let me know and I'll adjust."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Proactively manages ambiguity by proposing a plan, documenting assumptions, and setting up a review.",
                            "examples": [
                                "Given the limited brief, I'll start by pulling digital sales numbers for Q2 and create a one-pager with top-line trends. I'll assume we want this for the steering meeting tomorrow. I'll note my assumptions in the document and share a draft by 10am. If you could give it a quick look before I finalise, that'll ensure we're aligned. Does that work for you?"
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "feedback-receiving@v1",
        "skill_slug": "feedback-receiving",
        "name": "Receiving Feedback Professionally",
        "content_type": "scenario_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "response-to-feedback",
                "skill_slug": "feedback-receiving",
                "title": "Responds without defensiveness",
                "description": "The learner acknowledges feedback, regulates emotional reaction, and asks clarifying questions.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Defends, justifies, or argues with the feedback.",
                            "examples": ["But I did what you asked! No one told me that."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Shuts down or disengages; says nothing or gives a minimal acknowledgment.",
                            "examples": ["Okay."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Acknowledges the feedback but does not seek clarification or commit to change.",
                            "examples": ["Thanks, I'll keep that in mind."],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Thanks the giver, asks a clarifying question, and commits to action.",
                            "examples": [
                                "Thank you for that feedback. Could you give me an example of where I could have been more proactive? I'll make sure to incorporate that next time."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Demonstrates emotional regulation, uses a structured framework (ARCA, 3R), and turns feedback into a concrete plan.",
                            "examples": [
                                "Thank you - that's helpful. (Acknowledge) Let me reflect on that for a moment. (Pause) So I hear you saying that in the stakeholder meeting, I could have provided more context before jumping into the data. (Reflect) Could you help me understand what level of context would be most useful - a one-line summary, or a few bullet points? (Clarify) I'll prepare a brief context slide for our next meeting and run it by you beforehand. (Act)"
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "prioritisation@v1",
        "skill_slug": "prioritisation",
        "name": "Prioritising Work Under Pressure",
        "content_type": "scenario_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "identify-priorities",
                "skill_slug": "prioritisation",
                "title": "Identifies urgent vs important tasks",
                "description": "The learner distinguishes between what is time-sensitive and what has high impact, using a framework (e.g., Eisenhower).",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Treats all tasks as equally urgent; no prioritisation.",
                            "examples": ["I'll just do whatever comes in first."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Prioritises based on urgency only, ignoring importance.",
                            "examples": ["The one with the earliest deadline goes first."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Considers both urgency and importance but applies inconsistently.",
                            "examples": [
                                "The stakeholder meeting is tomorrow, so that's urgent, but I also need to finish the dashboard."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Uses a framework (e.g., Eisenhower) to explicitly categorise tasks and decide order.",
                            "examples": [
                                "I'm using the Eisenhower matrix. The steering meeting slides are urgent and important - I'll do those now. The data cleanup is important but not urgent - I'll schedule it for after lunch. The optional knowledge share is neither - I'll park it for now."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Applies prioritisation with nuance, negotiates with stakeholders, and adjusts as new information arrives.",
                            "examples": [
                                "I've mapped all tasks to the Eisenhower grid. The urgent/important ones are the steering deck and the risk assessment. I'll start with those. For the less critical tasks, I'll send a quick update to stakeholders to confirm deadlines and see if any can be shifted. If a new urgent request comes in, I'll reassess and escalate if needed."
                            ],
                        }
                    },
                ],
            },
            {
                "criterion_ref": "negotiate-workload",
                "skill_slug": "yes-with-conditions",
                "title": "Negotiates workload using 'yes, with conditions'",
                "description": "The learner commits to work but sets clear boundaries and trade-offs.",
                "weight": 1.0,
                "required": True,
                "position": 2,
                "levels": [
                    {
                        "level_1": {
                            "description": "Says 'yes' without negotiating, leading to overload or missed deadlines.",
                            "examples": ["Sure, I'll get that done too."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Says 'no' outright without offering alternatives.",
                            "examples": ["I can't do that."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Tries to negotiate but in a vague way.",
                            "examples": ["I'll try to fit it in."],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Uses 'yes, with conditions' clearly, specifying trade-offs.",
                            "examples": [
                                "I can take that on. To make sure I deliver both, I'd need to push the dashboard deadline to Friday. Would that work for you?"
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Negotiates proactively, offers options, and aligns on priorities with stakeholders.",
                            "examples": [
                                "I'm happy to help with the user metrics for the 9am meeting. Currently I have two other tasks due Friday. If I prioritise your request, I can have a high-level summary by 5pm today, but the detailed dashboard would then slip to Monday. Alternatively, I could deliver a robust dashboard by Friday if you can share the specific metrics you need by 3pm. Which approach would work best for you?"
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "quick_practice_reset_timeline@v1",
        "skill_slug": "expectation-setting",
        "name": "Reset the Timeline",
        "content_type": "quick_practice_prompt",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "yes-with-conditions-response",
                "skill_slug": "yes-with-conditions",
                "title": "Uses 'yes, with conditions' to reset expectations",
                "description": "The learner acknowledges the request, proposes a realistic deliverable, and sets a clear timeline.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Does not negotiate; either says 'yes' unconditionally or 'no' without alternatives.",
                            "examples": ["Sure, I'll have it ready by Monday."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Uses 'yes, with conditions': acknowledges request, states a realistic deliverable, proposes a timeline, and asks for confirmation.",
                            "examples": [
                                "Hi Elena, I'm happy to support the board meeting. To give you something robust, I can prepare a high-level summary of the top three campaign metrics by Monday 9am. For the full dashboard, I'd need until Wednesday - would that work? If you'd prefer the full version, I could prioritise it if we shift my current tasks; let me know your preference."
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "interview_text@v1",
        "skill_slug": "interview-structuring",
        "name": "Interview Assessment Rubric",
        "content_type": "interview_prompt",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "starr-framework",
                "skill_slug": "starr-framework",
                "title": "Situation & Task Clarity",
                "description": "The learner sets context and defines the problem clearly.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Lacks structure; minimal detail; no reflection; outcome unclear.",
                            "examples": ["I had a difficult stakeholder once. It was hard."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Basic structure but missing key elements; actions vague; limited reflection.",
                            "examples": [
                                "There was a stakeholder who was unhappy. I talked to them and it got better."
                            ],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Clear STARR structure; describes reasonable actions; some reflection; outcome stated.",
                            "examples": [
                                "The situation was that a project sponsor was pushing back on our timeline. I scheduled a meeting to understand their concerns and we agreed on a revised plan."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Strong STARR; specific actions showing empathy and negotiation; clear outcome; good reflection.",
                            "examples": [
                                "During a CRM implementation, the VP of Sales was blocking our requirements sessions. I met with her 1:1 to understand her concerns - she felt her team's input was being ignored. I restructured the sessions to include her team leads, and she became our biggest champion. I learned that early stakeholder buy-in saves weeks of rework."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Exemplary STARR; demonstrates advanced stakeholder skills; quantifiable outcome; deep reflection connecting to professional growth.",
                            "examples": [
                                "On a data migration project, the Head of Finance refused to attend our workshops, saying his team was too busy. I set up a 15-minute coffee chat to understand his real concern: he'd been burned by a previous project that promised minimal disruption but caused a 3-week reporting gap. I created a detailed transition plan with parallel running, which reduced his risk perception. He attended the next workshop and we delivered the migration with zero reporting downtime. This taught me that resistance often masks past trauma, and addressing the underlying fear is more effective than pushing for compliance."
                            ],
                        }
                    },
                ],
            },
            {
                "criterion_ref": "active-listening",
                "skill_slug": "empathy",
                "title": "Action: Communication & Empathy",
                "description": "The learner describes how they listened, empathised, and engaged with the stakeholder.",
                "weight": 1.0,
                "required": True,
                "position": 2,
                "levels": [
                    {
                        "level_1": {
                            "description": "No evidence of empathy or listening; actions are purely transactional.",
                            "examples": ["I told them what they needed to do."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Mentions communication but without specifics on empathy.",
                            "examples": ["I had a meeting with them."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Shows some empathetic behaviour; describes listening.",
                            "examples": ["I listened to their concerns and tried to address them."],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Demonstrates active listening and empathy with specific examples.",
                            "examples": [
                                "I scheduled a 1:1 meeting and used active listening techniques. I acknowledged that their concerns about timeline were valid and reflected back what I heard."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Exemplary empathy; shows nuanced understanding of stakeholder emotions and motivations.",
                            "examples": [
                                "I noticed her body language in the group meeting - arms crossed, minimal eye contact. I requested a private conversation and started by acknowledging that I understood her team was under pressure. She opened up about a previous project failure that had damaged her credibility with the board. I validated that concern and we worked together on a plan that protected her team's priorities."
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "scenario_text@v1",
        "skill_slug": "storytelling",
        "name": "Scenario Assessment Rubric",
        "content_type": "scenario_step",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "stakeholder-analysis",
                "skill_slug": "stakeholder-analysis",
                "title": "Stakeholder Analysis & Engagement",
                "description": "Correct identification, power/interest mapping, tailored engagement strategies, evidence of empathy.",
                "weight": 0.35,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Misses key stakeholders; mapping is absent or incorrect.",
                            "examples": ["The CEO is the main stakeholder."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Identifies some stakeholders but mapping is superficial.",
                            "examples": ["There are several stakeholders involved in the project."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Adequate stakeholder analysis with some correct grid placement.",
                            "examples": [
                                "I identified six stakeholders and mapped them on a power/interest grid. The CEO is high power, high interest."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Good stakeholder analysis with correct grid placement; effective engagement strategies.",
                            "examples": [
                                "I mapped eight stakeholder groups on Mendelow's grid. Cristina (CEO) is high power/high interest - manage closely with weekly updates. Samir (Head of Lending) is high power/medium interest - keep satisfied with targeted communication about transition safeguards."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Excellent stakeholder analysis with nuanced mapping; compelling engagement strategies with evidence of empathy.",
                            "examples": [
                                "I identified eight stakeholder groups and mapped them on a refined power/interest grid, accounting for informal influence. Key insight: Samir's resistance isn't just about his team - it's about his identity as a leader who built those models. My engagement strategy includes a 'knowledge transfer' programme that positions his team as mentors, turning the threat into a legacy opportunity."
                            ],
                        }
                    },
                ],
            },
            {
                "criterion_ref": "asking-the-right-questions",
                "skill_slug": "active-questioning",
                "title": "Interviewing & Questioning",
                "description": "Use of open/probing questions, active listening signals, ability to uncover hidden concerns.",
                "weight": 0.35,
                "required": True,
                "position": 2,
                "levels": [
                    {
                        "level_1": {
                            "description": "Questions are leading or irrelevant; no evidence of active listening.",
                            "examples": ["Don't you think centralisation is a good idea?"],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Questions are mostly closed; limited probing.",
                            "examples": [
                                "Are you worried about the move? How many people are on your team?"
                            ],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Uses open questions with some probing; reasonable structure.",
                            "examples": [
                                "What are your main concerns about the centralisation? Can you tell me more about how your team currently works?"
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Effective questioning sequence; shows empathy; uncovers some hidden concerns.",
                            "examples": [
                                "Tell me about your experience with previous changes in the department. (Open) You mentioned your models rely on the current setup. Can you walk me through what would happen if we had to migrate them? (Probing) It sounds like the real concern is continuity of service to your lending clients. Is that right? (Empathetic)"
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Exemplary questioning that uncovers hidden issues; demonstrates deep listening and empathy.",
                            "examples": [
                                "Tell me about your team's proudest achievement this year. (Open, rapport-building) You mentioned the lending models. What makes them special? (Probing deeper motivation) ... (Pause, active listening) I hear pride in your voice when you talk about those models. It sounds like centralisation might feel like it diminishes that achievement. Am I reading that right? (Empathetic probe that names the hidden fear)"
                            ],
                        }
                    },
                ],
            },
            {
                "criterion_ref": "presentation-facilitation",
                "skill_slug": "executive-summary",
                "title": "Structured Communication & Recommendation",
                "description": "Clear use of As-Is / Gap / To-Be framework, logical options, concise executive summary, actionable next steps.",
                "weight": 0.30,
                "required": True,
                "position": 3,
                "levels": [
                    {
                        "level_1": {
                            "description": "Communication lacks structure; recommendation is missing or unclear.",
                            "examples": ["We should centralise everything."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Some structure but recommendation is vague.",
                            "examples": [
                                "The current state is fragmented. We should centralise. Here are some ideas."
                            ],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Structured recommendation with some gaps; options presented but not compared.",
                            "examples": [
                                "As-Is: data teams are spread across departments. To-Be: centralised hub. We could do a phased approach or big-bang. I recommend phased."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Clear, well-structured recommendation with logical options and pros/cons.",
                            "examples": [
                                "Executive Summary: As-Is - 80 specialists across 8 depts, fragmented tools. To-Be - centralised Data Hub. Gap - relocation, tool migration, cultural change. Option A (Phased): 12 months, lower risk, slower ROI. Option B (Big-bang): 6 months, higher risk, faster ROI. Recommendation: Option A with a 3-month pilot in two departments first."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Compelling, business-focused recommendation with nuanced analysis and concrete next steps.",
                            "examples": [
                                "Executive Summary for Steering Committee: Our analysis shows centralisation will deliver 23% faster model deployment and 15% cost reduction over 3 years. Key risk: talent attrition (est. 12-18% without mitigation). We recommend a hybrid approach: Phase 1 (months 1-3) - pilot with Lending and Digital teams, proving value before full rollout. Phase 2 (months 4-9) - migrate remaining teams with dedicated change support. Critical success factor: position Samir's team as 'migration champions' to convert resistance into advocacy. Next steps: (1) Approve pilot budget by Friday, (2) Appoint change lead by next week, (3) Pilot kickoff in 2 weeks."
                            ],
                        }
                    },
                ],
            },
        ],
    },
    {
        "id": "quick_practice_text@v1",
        "skill_slug": "note-taking-validation",
        "name": "Quick Practice Text Rubric",
        "content_type": "quick_practice_text",
        "schema_version": "1.0",
        "criteria": [
            {
                "criterion_ref": "clarify-and-respond",
                "skill_slug": "asking-the-right-questions",
                "title": "Clarifies and responds effectively",
                "description": "The learner asks targeted clarifying questions and proposes a clear response.",
                "weight": 1.0,
                "required": True,
                "position": 1,
                "levels": [
                    {
                        "level_1": {
                            "description": "Does not ask clarifying questions; proceeds without understanding.",
                            "examples": ["Okay, I'll send something over."],
                        }
                    },
                    {
                        "level_2": {
                            "description": "Asks one vague question; response is generic.",
                            "examples": ["What do you need exactly? I'll try to get it done."],
                        }
                    },
                    {
                        "level_3": {
                            "description": "Asks relevant questions and proposes a reasonable response.",
                            "examples": [
                                "What metrics are you looking for? I can put together a summary by tomorrow."
                            ],
                        }
                    },
                    {
                        "level_4": {
                            "description": "Asks targeted questions covering scope, format, and deadline; proposes a concrete plan.",
                            "examples": [
                                "To make sure this is useful: (1) What metrics matter most? (2) Is a one-page summary enough? (3) What time do you need it? I'll prepare a draft and share by 10am."
                            ],
                        }
                    },
                    {
                        "level_5": {
                            "description": "Asks insightful questions, proposes options, and shows proactive thinking.",
                            "examples": [
                                "Happy to help. To tailor this for the steering meeting, could you clarify: (1) What are the key discussion points - conversion rates, revenue trends, or channel performance? (2) Would a one-pager with top-line trends work, or do you need a detailed breakdown? (3) What time tomorrow? I can have a draft by 5pm today for your review, or a polished version by 8am tomorrow. Which works better?"
                            ],
                        }
                    },
                ],
            },
        ],
    },
]


def seed(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    now = _utcnow()

    # -----------------------------------------------------------------------
    # System user
    # -----------------------------------------------------------------------
    system_user_id = _uid()
    conn.execute(
        "INSERT INTO user_accounts (id, email, display_name, auth_provider, auth_subject, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (system_user_id, "system@softskills.local", "System", "local", "system", True, now),
    )

    # -----------------------------------------------------------------------
    # Skills
    # -----------------------------------------------------------------------
    for slug, name, desc in SKILLS:
        conn.execute(
            "INSERT OR IGNORE INTO skills (slug, name, description, organisation_id) VALUES (?, ?, ?, NULL)",
            (slug, name, desc),
        )

    # -----------------------------------------------------------------------
    # Competencies
    # -----------------------------------------------------------------------
    for slug, name, desc in COMPETENCIES:
        conn.execute(
            "INSERT OR IGNORE INTO competencies (slug, name, description, organisation_id) VALUES (?, ?, ?, NULL)",
            (slug, name, desc),
        )

    # -----------------------------------------------------------------------
    # Competency -> Skill map
    # -----------------------------------------------------------------------
    for comp_slug, skill_slug, weight in COMPETENCY_SKILL_MAP:
        conn.execute(
            "INSERT OR IGNORE INTO competency_skill_map (competency_slug, skill_slug, weight) VALUES (?, ?, ?)",
            (comp_slug, skill_slug, weight),
        )

    # -----------------------------------------------------------------------
    # Rubrics + Rubric versions
    # -----------------------------------------------------------------------
    for rubric in RUBRICS:
        conn.execute(
            "INSERT INTO rubrics (id, skill_slug, organisation_id, name, description, content_type, schema_version, created_at, updated_at) "
            "VALUES (?, ?, NULL, ?, NULL, ?, ?, ?, ?)",
            (
                rubric["id"],
                rubric["skill_slug"],
                rubric["name"],
                rubric["content_type"],
                rubric["schema_version"],
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO rubric_versions (rubric_id, version, criteria, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (rubric["id"], "v2", json.dumps(rubric["criteria"]), "published", now, now),
        )

    # -----------------------------------------------------------------------
    # Collection: Consultancy Fundamentals
    # -----------------------------------------------------------------------
    collection_id = _uid()
    conn.execute(
        "INSERT INTO collections (id, author_user_id, organisation_id, title, summary, target_audience, difficulty, "
        "lifecycle_state, verification_state, source_type, content_format_mix, target_skill_slugs, "
        "target_competency_slugs, rubric_ids, rating_count, featured, created_at, updated_at) "
        "VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            collection_id,
            system_user_id,
            "Consultancy Fundamentals",
            "A collection of exercises to build core consulting skills: stakeholder management, structured thinking, asking the right questions, navigating ambiguity, client-site professionalism, and effective communication.",
            "junior consultants",
            "intermediate",
            "published_public",
            "verified",
            "manual",
            json.dumps(["quick_practice_prompt", "interview_prompt", "scenario_step"]),
            json.dumps(
                [
                    "active-listening",
                    "expectation-setting",
                    "yes-with-conditions",
                    "professionalism-under-pressure",
                    "asking-the-right-questions",
                    "ambiguity-navigation",
                    "empathy",
                    "conflict-facilitation",
                    "expectation-setting",
                    "structured-thinking",
                    "stakeholder-analysis",
                    "stakeholder-engagement",
                    "presentation-facilitation",
                ]
            ),
            json.dumps(
                [
                    "stakeholder-management",
                    "consulting-mindset",
                    "client-site-professionalism",
                    "effective-communication",
                ]
            ),
            json.dumps(
                [
                    "quick_practice_reset_timeline@v1",
                    "quick_practice_text@v1",
                    "interview_text@v1",
                    "scenario_text@v1",
                ]
            ),
            0,
            False,
            now,
            now,
        ),
    )

    # -----------------------------------------------------------------------
    # Prompt items
    # -----------------------------------------------------------------------
    # Item 1: Quick Practice - "Client Asks for Impossible Deadline"
    item1_id = _uid()
    conn.execute(
        "INSERT INTO prompt_items (id, collection_id, author_user_id, organisation_id, prompt_type, title, "
        "prompt_text, difficulty, lifecycle_state, target_skill_slugs, rubric_id, created_at, updated_at) "
        "VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            item1_id,
            collection_id,
            system_user_id,
            "quick_practice_prompt",
            "Client Asks for Impossible Deadline",
            (
                "Scenario: You are a consultant working on a data migration project. "
                "A senior stakeholder, Elena (Head of Marketing), sends you an email at 4:30pm on Friday: "
                "\"I need a full dashboard of last quarter's campaign performance by Monday 9am for the board meeting. "
                "I know it's tight, but you can pull it together, right?\"\n\n"
                "You estimate the task would normally take two days, and you already have planned work for the weekend. "
                "You cannot deliver a complete dashboard by Monday without sacrificing quality or your personal commitments.\n\n"
                "Your Task: Write a short reply (3-5 sentences) to Elena. "
                "Use the 'yes, with conditions' framework to reset expectations while maintaining a professional relationship."
            ),
            "intermediate",
            "published_public",
            json.dumps(
                ["expectation-setting", "yes-with-conditions", "professionalism-under-pressure"]
            ),
            "quick_practice_reset_timeline@v1",
            now,
            now,
        ),
    )

    # Item 2: Quick Practice - "Clarifying an Ambiguous Request"
    item2_id = _uid()
    conn.execute(
        "INSERT INTO prompt_items (id, collection_id, author_user_id, organisation_id, prompt_type, title, "
        "prompt_text, difficulty, lifecycle_state, target_skill_slugs, rubric_id, created_at, updated_at) "
        "VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            item2_id,
            collection_id,
            system_user_id,
            "quick_practice_prompt",
            "Clarifying an Ambiguous Request",
            (
                "Scenario: It's your second week on client site. Your manager, Sarah, sends you a Teams message: "
                '"Can you pull some numbers on our digital sales performance and send me something '
                "before tomorrow's steering meeting? Just something I can talk to.\"\n\n"
                "You have no clear brief, and you're not sure what 'digital sales performance' means "
                "or what format is expected.\n\n"
                "Your Task: Write a short Teams reply (3-6 sentences) that acknowledges the request "
                "and asks specific clarifying questions to reduce ambiguity. Use the 5Ws/1H framework (who, what, when, where, why, how)."
            ),
            "intermediate",
            "published_public",
            json.dumps(["asking-the-right-questions", "ambiguity-navigation"]),
            "quick_practice_text@v1",
            now,
            now,
        ),
    )

    # Item 3: Interview Prompt - "Managing a Difficult Stakeholder"
    item3_id = _uid()
    conn.execute(
        "INSERT INTO prompt_items (id, collection_id, author_user_id, organisation_id, prompt_type, title, "
        "prompt_text, difficulty, lifecycle_state, target_skill_slugs, rubric_id, created_at, updated_at) "
        "VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            item3_id,
            collection_id,
            system_user_id,
            "interview_prompt",
            "Managing a Difficult Stakeholder",
            (
                "Competency Interview Question:\n"
                '"Tell me about a time when you had to manage a difficult stakeholder. '
                'What was the situation, what actions did you take, and what was the result?"\n\n'
                "Guidance: Use the STARR framework (Situation, Task, Action, Result, Reflection). "
                "Focus on your specific behaviours, the challenges you faced, and what you learned."
            ),
            "intermediate",
            "published_public",
            json.dumps(
                ["empathy", "conflict-facilitation", "expectation-setting", "active-listening"]
            ),
            "interview_text@v1",
            now,
            now,
        ),
    )

    # -----------------------------------------------------------------------
    # Scenario: MoneyCraft Data Centralisation
    # -----------------------------------------------------------------------
    scenario_id = _uid()
    conn.execute(
        "INSERT INTO scenarios (id, collection_id, author_user_id, organisation_id, title, "
        "business_context, learner_objective, constraints, stakeholder_tensions, lifecycle_state, "
        "target_skill_slugs, rubric_id, created_at, updated_at) "
        "VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            scenario_id,
            collection_id,
            system_user_id,
            "MoneyCraft Data Centralisation",
            (
                "MoneyCraft is a mid-sized digital bank in the UK. It has grown rapidly over five years, "
                "acquiring several smaller fintechs. As a result, its data function is fragmented: "
                "80 data specialists are spread across eight departments, each using different tools and practices. "
                "The CEO wants to centralise these teams into a new Data Hub in Canary Wharf to improve "
                "collaboration, retention, and competitive edge."
            ),
            "Navigate stakeholder tensions, conduct interviews, and present a structured recommendation for the data centralisation project.",
            json.dumps(
                [
                    "Board presentation is in 2 weeks",
                    "Budget is capped at 10M GBP",
                    "Relocation packages must comply with HR policy",
                ]
            ),
            json.dumps(
                [
                    "Lending team wants to keep their dedicated data specialists",
                    "Some specialists have young children and resist relocation",
                    "HR needs to manage union relations during the transition",
                ]
            ),
            "published_public",
            json.dumps(
                [
                    "structured-thinking",
                    "stakeholder-analysis",
                    "stakeholder-engagement",
                    "ambiguity-navigation",
                    "asking-the-right-questions",
                    "presentation-facilitation",
                ]
            ),
            "scenario_text@v1",
            now,
            now,
        ),
    )

    # Mock company
    mock_company_id = _uid()
    conn.execute(
        "INSERT INTO mock_companies (id, scenario_id, name, industry, operating_context) VALUES (?, ?, ?, ?, ?)",
        (
            mock_company_id,
            scenario_id,
            "MoneyCraft Bank",
            "Fintech / Retail Banking",
            "MoneyCraft is a mid-sized digital bank in the UK. It has grown rapidly over five years, "
            "acquiring several smaller fintechs. As a result, its data function is fragmented: "
            "80 data specialists are spread across eight departments, each using different tools and practices. "
            "The CEO wants to centralise these teams into a new Data Hub in Canary Wharf to improve "
            "collaboration, retention, and competitive edge.",
        ),
    )

    # Mock people
    people = [
        (
            "Cristina Yang",
            "CEO",
            [
                "Centralise data to accelerate innovation",
                "Retain top talent",
                "Get board approval for the 10M GBP investment",
            ],
            "Visionary, impatient, expects concise summaries",
        ),
        (
            "Samir Hicks",
            "Head of Lending",
            [
                "Keep his dedicated data team to maintain lending model updates",
                "Worries centralisation will slow his department",
            ],
            "Protective of his team; uses technical jargon; can be defensive",
        ),
        (
            "Sarah Chen",
            "Senior Data Specialist",
            [
                "Wants career growth and modern tools",
                "Open to centralisation but worried about relocation (young children)",
            ],
            "Analytical, reserved, values evidence",
        ),
        (
            "James Okonkwo",
            "Head of HR",
            ["Ensure smooth transition", "Manage relocation logistics", "Avoid union issues"],
            "Process-oriented, collaborative",
        ),
    ]
    for name, role, goals, style in people:
        conn.execute(
            "INSERT INTO mock_people (id, scenario_id, mock_company_id, name, role, goals, communication_style, relationship_to_scenario) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _uid(),
                scenario_id,
                mock_company_id,
                name,
                role,
                json.dumps(goals),
                style,
                "Key stakeholder in the MoneyCraft data centralisation scenario",
            ),
        )

    # Supporting artifacts
    artifacts = [
        (
            "email",
            "CEO Announcement Email",
            "Subject: Project Insight 2025 - Data Centralisation\n\nDear colleagues, as we discussed in the leadership offsite, we will be centralising our data teams into a new hub in Canary Wharf. This will give us standardised tools, clearer career paths, and a competitive edge. I will appoint a project lead shortly. Please prepare to support this transition. - Cristina",
        ),
        (
            "slack_thread",
            "Slack Exchange: Samir and Cristina",
            "Samir Hicks: Cristina, my team has built proprietary models that rely on our current setup. Moving them will disrupt our lending pipeline.\n\nCristina Yang: Samir, I appreciate the concern, but we need to think long-term. The hub will include all departments - we'll ensure transition plans are robust.",
        ),
        (
            "document",
            "Current Data Landscape",
            "Current Data Landscape:\n- Lending: uses SAS, 20 specialists\n- Digital Banking: uses Python + Tableau, 15 specialists\n- Risk: uses R + Power BI, 10 specialists\n- Compliance: uses SQL + Excel, 8 specialists\n- Marketing: uses Python + Looker, 7 specialists\n- Operations: uses Excel + Power BI, 6 specialists\n- Finance: uses SAS + Excel, 8 specialists\n- HR: uses Excel, 6 specialists",
        ),
    ]
    for artifact_type, title, body in artifacts:
        conn.execute(
            "INSERT INTO scenario_supporting_artifacts (id, scenario_id, artifact_type, title, body, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (_uid(), scenario_id, artifact_type, title, body, now),
        )

    conn.commit()
    conn.close()
    print(f"Seeded database at {db_path}")


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "fresh.db"
    seed(db_path)
