# Canonical Skills, Competencies, and Rubrics

This document defines the canonical set of soft‑skills taxonomies for the platform. All items are platform‑owned (`organisation_id = NULL`) and serve as the foundation for organisation‑specific overrides.

---

## 1. Skills

A skill is a specific, observable ability. Skills are the atomic building blocks of competencies.

| Slug | Name | Description |
|------|------|-------------|
| `active-listening` | Active Listening | Fully concentrating on what someone is saying, reflecting, paraphrasing, and summarising to ensure understanding. |
| `structured-thinking` | Structured Thinking | Breaking down complex problems into logical components using frameworks and mental models. |
| `professional-scepticism` | Professional Scepticism | Challenging assumptions politely and verifying information without cynicism. |
| `asking-the-right-questions` | Asking the Right Questions | Using open, probing, and closed questions to uncover requirements and hidden concerns. |
| `translating-business-tech` | Translating Business & Tech | Explaining technical possibilities to non‑technical stakeholders and business constraints to technical teams. |
| `stakeholder-analysis` | Stakeholder Analysis | Identifying stakeholders, mapping their power/interest, and understanding their needs. |
| `stakeholder-engagement` | Stakeholder Engagement | Tailoring communication, frequency, and involvement to different stakeholder groups. |
| `conflict-facilitation` | Conflict Facilitation | Making conflicts visible, facilitating resolution without taking sides, and escalating when needed. |
| `rasci-clarity` | RASCI Clarity | Defining roles and responsibilities using the RASCI model, ensuring one accountable per task. |
| `interview-structuring` | Interview Structuring | Planning, conducting, and following up on interviews with a clear agenda and active listening. |
| `active-questioning` | Active Questioning | Applying open, probing, and closed questions appropriately in conversations. |
| `paraphrasing-reflecting` | Paraphrasing & Reflecting | Restating what was said and acknowledging emotions to confirm understanding. |
| `note-taking-validation` | Note‑Taking & Validation | Recording accurate notes and validating them with the interviewee. |
| `starr-framework` | STARR Framework | Structuring answers with Situation, Task, Action, Result, Reflection. |
| `storytelling` | Storytelling | Crafting compelling narratives that engage and persuade. |
| `self-reflection` | Self‑Reflection | Analysing one’s own experiences to extract lessons and growth opportunities. |
| `growth-mindset` | Growth Mindset | Embracing challenges, viewing failure as learning, and seeking feedback. |
| `proactivity` | Proactivity | Taking initiative beyond the explicit task, thinking one step ahead. |
| `curiosity` | Curiosity | Asking questions, seeking to understand, and learning continuously. |
| `ambiguity-navigation` | Navigating Ambiguity | Making progress with incomplete information, asking clarifying questions, and documenting assumptions. |
| `prioritisation` | Prioritisation | Using frameworks (e.g., Eisenhower) to sort tasks and focus on what matters. |
| `yes-with-conditions` | Yes, With Conditions | Negotiating workload by setting clear boundaries, deadlines, and trade‑offs. |
| `escalation` | Escalation | Raising issues with evidence and a clear call to action when options are exhausted. |
| `professionalism-under-pressure` | Professionalism Under Pressure | Staying calm, managing emotions, and responding constructively in tense situations. |
| `feedback-receiving` | Receiving Feedback | Responding to feedback without defensiveness, using frameworks (ARCA, 3R, CARE). |
| `feedback-asking` | Asking for Feedback | Proactively seeking specific, forward‑looking feedback. |
| `emotional-regulation` | Emotional Regulation | Recognising and managing one’s emotional reactions (fight/flight/freeze). |
| `change-management` | Change Management | Supporting people through transitions, addressing resistance, and enabling adoption. |
| `business-case-development` | Business Case Development | Justifying investments with cost‑benefit analysis, risks, and benefits. |
| `requirements-engineering` | Requirements Engineering | Capturing, modelling, and managing requirements throughout a project. |
| `presentation-facilitation` | Presentation & Facilitation | Delivering clear, engaging presentations and facilitating group discussions. |
| `concise-explanation` | Concise Explanation | Communicating complex ideas clearly and briefly, with key takeaways. |
| `empathy` | Empathy | Understanding and acknowledging others’ perspectives, emotions, and motivations. |
| `expectation-setting` | Expectation Setting | Agreeing on scope, deliverables, and timelines upfront to avoid surprises. |
| `negotiation` | Negotiation | Finding mutually acceptable solutions while maintaining relationships. |
| `executive-summary` | Executive Summary | Distilling information into a high‑level summary suitable for senior stakeholders. |
| `decision-justification` | Decision Justification | Explaining the rationale behind decisions with evidence and trade‑offs. |

---

## 2. Competencies

A competency groups multiple skills into a higher‑level capability. Each competency maps to a set of skills with **weights** (normalised to sum to 1.0).

| Slug | Name | Description | Skill Slugs (with weight) |
|------|------|-------------|---------------------------|
| `consulting-mindset` | Consulting Mindset | Applying objectivity, structured thinking, and a gap‑based approach to help others make better decisions. | `structured-thinking` (0.3), `professional-scepticism` (0.2), `asking-the-right-questions` (0.2), `translating-business-tech` (0.2), `change-management` (0.1) |
| `stakeholder-management` | Stakeholder Management | Identifying, analysing, engaging, and managing stakeholders throughout a project lifecycle. | `stakeholder-analysis` (0.2), `stakeholder-engagement` (0.2), `active-listening` (0.15), `empathy` (0.15), `expectation-setting` (0.1), `conflict-facilitation` (0.1), `rasci-clarity` (0.1) |
| `effective-communication` | Effective Communication | Conveying information clearly and persuasively through writing, speaking, and listening. | `structured-thinking` (0.15), `concise-explanation` (0.15), `executive-summary` (0.1), `storytelling` (0.1), `active-listening` (0.1), `paraphrasing-reflecting` (0.1), `interview-structuring` (0.1), `active-questioning` (0.1), `presentation-facilitation` (0.1) |
| `client-site-professionalism` | Client Site Professionalism | Navigating the client environment with confidence, handling ambiguity, and maintaining trust. | `ambiguity-navigation` (0.2), `prioritisation` (0.2), `yes-with-conditions` (0.2), `escalation` (0.15), `professionalism-under-pressure` (0.15), `emotional-regulation` (0.1) |
| `feedback-receptivity` | Feedback Receptivity | Actively seeking, receiving, and applying feedback to grow professionally. | `feedback-receiving` (0.3), `feedback-asking` (0.25), `growth-mindset` (0.25), `self-reflection` (0.2) |
| `problem-solving-under-ambiguity` | Problem Solving Under Ambiguity | Analysing complex, poorly defined problems and moving forward with incomplete information. | `ambiguity-navigation` (0.25), `structured-thinking` (0.25), `starr-framework` (0.2), `asking-the-right-questions` (0.2), `decision-justification` (0.1) |
| `project-delivery` | Project Delivery | Contributing to successful project outcomes through requirements, change, and business case skills. | `requirements-engineering` (0.25), `change-management` (0.2), `business-case-development` (0.2), `stakeholder-management` (0.2), `presentation-facilitation` (0.15) |
| `professional-growth` | Professional Growth | Demonstrating curiosity, proactivity, and a commitment to continuous learning. | `curiosity` (0.3), `proactivity` (0.3), `growth-mindset` (0.2), `self-reflection` (0.2) |

---

## 3. Rubrics

Each skill can have one or more rubrics (different content types). Below are canonical rubrics for the most critical skills. Each rubric contains a set of criteria (one per sub‑skill) with level‑based descriptions and **concrete examples of learner responses**.

Rubrics are stored in the database with a `content_type` and `schema_version`. The `criteria` field is a JSON array where each criterion has:

- `criterion_ref` – unique identifier within the rubric
- `skill_slug` – the skill this criterion assesses (may be the same as the rubric’s skill, or a sub‑skill)
- `title` – short title
- `description` – what the criterion measures
- `weight` – importance relative to other criteria (normally 1.0 for all, or 0 if optional)
- `required` – boolean
- `position` – order in the rubric
- `levels` – array of objects with keys `level_1` through `level_5` (or fewer if binary), each with:
  - `description` – qualitative description of that level
  - `examples` – array of strings that are **actual learner responses** illustrating that level

### 3.1 Rubric for `active-listening`

**Rubric ID:** `active-listening@v1`  
**Content Type:** `quick_practice_text`  
**Schema Version:** `1.0`  
**Name:** Active Listening in a Consulting Conversation  

```json
[
  {
    "criterion_ref": "active-listening-reflect",
    "skill_slug": "active-listening",
    "title": "Reflecting stakeholder signals",
    "description": "The learner demonstrates they have heard and understood what the stakeholder said, including emotional tone.",
    "weight": 1.0,
    "required": true,
    "position": 1,
    "levels": [
      {
        "level_1": {
          "description": "Does not reflect stakeholder concerns; may ignore or misinterpret.",
          "examples": [
            "I think the main issue is the timeline. We should just move forward."
          ]
        }
      },
      {
        "level_2": {
          "description": "Shows limited reflection, mostly repeating facts without acknowledging deeper meaning.",
          "examples": [
            "So you said the data team is busy, got it."
          ]
        }
      },
      {
        "level_3": {
          "description": "Partially reflects concerns but misses subtle signals or emotions.",
          "examples": [
            "So what I'm hearing is you're worried about the handoff, but we'll manage it."
          ]
        }
      },
      {
        "level_4": {
          "description": "Accurately reflects key points and acknowledges emotions.",
          "examples": [
            "It sounds like the handoff is causing frustration because it slows things down and adds extra work. Is that right?"
          ]
        }
      },
      {
        "level_5": {
          "description": "Clearly reflects both content and emotional signals, demonstrating deep understanding.",
          "examples": [
            "Let me make sure I understand. The handoff to compliance is taking three days, which is delaying your KYC process. It feels like a bottleneck, and you're concerned it's affecting customer satisfaction. Is that the core challenge?"
          ]
        }
      }
    ]
  },
  {
    "criterion_ref": "active-listening-paraphrase",
    "skill_slug": "paraphrasing-reflecting",
    "title": "Paraphrasing and summarising",
    "description": "The learner restates what the stakeholder said in their own words to confirm understanding.",
    "weight": 1.0,
    "required": true,
    "position": 2,
    "levels": [
      {
        "level_1": {
          "description": "Does not paraphrase or summarise; moves on without confirmation.",
          "examples": [
            "Okay, next question."
          ]
        }
      },
      {
        "level_2": {
          "description": "Attempts to summarise but misses key details or introduces inaccuracies.",
          "examples": [
            "So you want better reporting tools."
          ]
        }
      },
      {
        "level_3": {
          "description": "Summarises the main point, but omits nuance.",
          "examples": [
            "So you're saying the current tools are inconsistent across departments."
          ]
        }
      },
      {
        "level_4": {
          "description": "Summarises accurately and checks for understanding.",
          "examples": [
            "So to recap, each department currently uses different reporting tools, and that's making it hard to share data and collaborate. Is that correct?"
          ]
        }
      },
      {
        "level_5": {
          "description": "Summarises comprehensively and invites confirmation or correction.",
          "examples": [
            "Let me summarise what I've heard so far. You have 80 data specialists spread across eight departments, each using their own tools, and you've seen issues with knowledge sharing and talent retention. You're hoping that centralisation will give you standardised practices, clearer career paths, and a competitive edge. Have I captured that correctly?"
          ]
        }
      }
    ]
  }
]
```

### 3.2 Rubric for `structured-thinking`

**Rubric ID:** `structured-thinking@v1`  
**Content Type:** `scenario_text`  
**Schema Version:** `1.0`  
**Name:** Applying Structured Thinking to a Problem  

```json
[
  {
    "criterion_ref": "structured-thinking-framework",
    "skill_slug": "structured-thinking",
    "title": "Uses a framework to decompose the problem",
    "description": "The learner applies a mental model (e.g., As-Is → Gap → To‑Be, SWOT, PESTLE) to break down the problem logically.",
    "weight": 1.0,
    "required": true,
    "position": 1,
    "levels": [
      {
        "level_1": {
          "description": "No framework; jumps to solutions without analysis.",
          "examples": [
            "We should just hire more data specialists."
          ]
        }
      },
      {
        "level_2": {
          "description": "Mentions a framework superficially but does not apply it consistently.",
          "examples": [
            "We could look at the current state and then decide."
          ]
        }
      },
      {
        "level_3": {
          "description": "Uses a framework but misses some key components.",
          "examples": [
            "The current situation is that data is scattered. We want centralisation. The gap is we need to move people and tools."
          ]
        }
      },
      {
        "level_4": {
          "description": "Applies a framework with clear structure, covering all main elements.",
          "examples": [
            "Let's map this using As-Is / Gap / To‑Be. As‑Is: data specialists are decentralised, using different tools, with no standardisation. To‑Be: a centralised hub with common tools and career paths. The gap includes physical relocation, tool migration, and cultural change."
          ]
        }
      },
      {
        "level_5": {
          "description": "Applies a framework with nuance, identifies multiple dimensions, and uses it to guide next steps.",
          "examples": [
            "I'd approach this using a structured framework. First, I'd document the As‑Is: people, processes, tools, and culture across departments. Then I'd define the To‑Be based on business objectives: a centralised hub that improves collaboration and retention. The gap analysis would break down into four areas: organisational design, technology standardisation, change management, and talent development. For each, I'd identify specific tasks and risks."
          ]
        }
      }
    ]
  }
]
```

### 3.3 Rubric for `asking-the-right-questions`

**Rubric ID:** `asking-the-right-questions@v1`  
**Content Type:** `scenario_text`  
**Schema Version:** `1.0`  
**Name:** Asking the Right Questions to Uncover Requirements  

```json
[
  {
    "criterion_ref": "question-types",
    "skill_slug": "active-questioning",
    "title": "Uses a mix of open, probing, and closed questions",
    "description": "The learner chooses question types appropriate to the situation to gather information effectively.",
    "weight": 1.0,
    "required": true,
    "position": 1,
    "levels": [
      {
        "level_1": {
          "description": "Uses mostly closed or leading questions; fails to explore.",
          "examples": [
            "Don't you think the system is too slow?"
          ]
        }
      },
      {
        "level_2": {
          "description": "Uses some open questions but does not probe deeper.",
          "examples": [
            "Tell me about your role. Do you like it?"
          ]
        }
      },
      {
        "level_3": {
          "description": "Uses open questions and some probing, but misses follow-up opportunities.",
          "examples": [
            "How do you currently process data requests? ... What tools do you use?"
          ]
        }
      },
      {
        "level_4": {
          "description": "Effectively sequences open, probing, and closed questions to gather detailed information.",
          "examples": [
            "Tell me about how you handle data requests today. (Open) ... You mentioned the handoff to compliance is slow. Can you walk me through what happens at that point? (Probing) ... So does the delay typically happen before or after the KYC check? (Closed)"
          ]
        }
      },
      {
        "level_5": {
          "description": "Exemplary questioning: uses silence, builds on previous answers, and uncovers hidden issues.",
          "examples": [
            "Tell me about a typical day when a data request comes in. (Open) ... You mentioned you have to chase compliance. How do you usually follow up? (Probing) ... (Pause) ... You're nodding, but it sounds like that process frustrates your team. What would make it smoother? (Empathetic probe)"
          ]
        }
      }
    ]
  }
]
```

### 3.4 Rubric for `ambiguity-navigation`

**Rubric ID:** `ambiguity-navigation@v1`  
**Content Type:** `quick_practice_text`  
**Schema Version:** `1.0`  
**Name:** Navigating Ambiguous Requests  

```json
[
  {
    "criterion_ref": "clarifying-questions",
    "skill_slug": "asking-the-right-questions",
    "title": "Asks clarifying questions when direction is unclear",
    "description": "The learner identifies what is ambiguous and asks specific questions to reduce uncertainty.",
    "weight": 1.0,
    "required": true,
    "position": 1,
    "levels": [
      {
        "level_1": {
          "description": "Does not ask clarifying questions; proceeds with guesswork.",
          "examples": [
            "Okay, I'll get you something by tomorrow."
          ]
        }
      },
      {
        "level_2": {
          "description": "Asks a very broad question that doesn't narrow ambiguity.",
          "examples": [
            "What exactly do you need?"
          ]
        }
      },
      {
        "level_3": {
          "description": "Asks one or two relevant clarifying questions but misses important details.",
          "examples": [
            "What format would you like the numbers in?"
          ]
        }
      },
      {
        "level_4": {
          "description": "Asks a set of targeted questions to clarify purpose, scope, and format.",
          "examples": [
            "To make sure I give you something useful, could you tell me: (1) What metrics would be most helpful for the steering meeting? (2) Is a one-page summary enough, or would you prefer a slide deck? (3) When do you need it by?"
          ]
        }
      },
      {
        "level_5": {
          "description": "Clarifies not just what but why, and proposes next steps to align.",
          "examples": [
            "I want to make sure this meets your needs for the steering meeting. Could you help me understand what the key discussion points will be, so I can tailor the numbers accordingly? Also, what's the most helpful format – a slide with key trends, or a more detailed dashboard? I can have a draft by 2pm tomorrow; if you need it earlier, I can prioritise a high-level summary by end of day – which would work better?"
          ]
        }
      }
    ]
  },
  {
    "criterion_ref": "progress-with-info",
    "skill_slug": "ambiguity-navigation",
    "title": "Makes progress with incomplete information",
    "description": "The learner moves forward despite ambiguity, documenting assumptions and iterating.",
    "weight": 1.0,
    "required": true,
    "position": 2,
    "levels": [
      {
        "level_1": {
          "description": "Stops working until ambiguity is resolved.",
          "examples": [
            "I can't start until I get more details."
          ]
        }
      },
      {
        "level_2": {
          "description": "Makes assumptions but does not document or communicate them.",
          "examples": [
            "I'll assume they want last month's figures."
          ]
        }
      },
      {
        "level_3": {
          "description": "Makes assumptions and mentions them in passing.",
          "examples": [
            "I'm going to assume we're looking at Q2 numbers. Let me know if that's not right."
          ]
        }
      },
      {
        "level_4": {
          "description": "Documents assumptions clearly and shares them for alignment.",
          "examples": [
            "To move forward, I've assumed we'll focus on digital sales performance, using Q2 data. I've documented this in the shared folder. If those assumptions are wrong, let me know and I'll adjust."
          ]
        }
      },
      {
        "level_5": {
          "description": "Proactively manages ambiguity by proposing a plan, documenting assumptions, and setting up a review.",
          "examples": [
            "Given the limited brief, I'll start by pulling digital sales numbers for Q2 and create a one-pager with top-line trends. I'll assume we want this for the steering meeting tomorrow. I'll note my assumptions in the document and share a draft by 10am. If you could give it a quick look before I finalise, that'll ensure we're aligned. Does that work for you?"
          ]
        }
      }
    ]
  }
]
```

### 3.5 Rubric for `feedback-receiving`

**Rubric ID:** `feedback-receiving@v1`  
**Content Type:** `scenario_text`  
**Schema Version:** `1.0`  
**Name:** Receiving Feedback Professionally  

```json
[
  {
    "criterion_ref": "response-to-feedback",
    "skill_slug": "feedback-receiving",
    "title": "Responds without defensiveness",
    "description": "The learner acknowledges feedback, regulates emotional reaction, and asks clarifying questions.",
    "weight": 1.0,
    "required": true,
    "position": 1,
    "levels": [
      {
        "level_1": {
          "description": "Defends, justifies, or argues with the feedback.",
          "examples": [
            "But I did what you asked! No one told me that."
          ]
        }
      },
      {
        "level_2": {
          "description": "Shuts down or disengages; says nothing or gives a minimal acknowledgment.",
          "examples": [
            "Okay."
          ]
        }
      },
      {
        "level_3": {
          "description": "Acknowledges the feedback but does not seek clarification or commit to change.",
          "examples": [
            "Thanks, I'll keep that in mind."
          ]
        }
      },
      {
        "level_4": {
          "description": "Thanks the giver, asks a clarifying question, and commits to action.",
          "examples": [
            "Thank you for that feedback. Could you give me an example of where I could have been more proactive? I'll make sure to incorporate that next time."
          ]
        }
      },
      {
        "level_5": {
          "description": "Demonstrates emotional regulation, uses a structured framework (ARCA, 3R), and turns feedback into a concrete plan.",
          "examples": [
            "Thank you – that's helpful. (Acknowledge) Let me reflect on that for a moment. (Pause) So I hear you saying that in the stakeholder meeting, I could have provided more context before jumping into the data. (Reflect) Could you help me understand what level of context would be most useful – a one-line summary, or a few bullet points? (Clarify) I'll prepare a brief context slide for our next meeting and run it by you beforehand. (Act)"
          ]
        }
      }
    ]
  }
]
```

### 3.6 Rubric for `prioritisation`

**Rubric ID:** `prioritisation@v1`  
**Content Type:** `scenario_text`  
**Schema Version:** `1.0`  
**Name:** Prioritising Work Under Pressure  

```json
[
  {
    "criterion_ref": "identify-priorities",
    "skill_slug": "prioritisation",
    "title": "Identifies urgent vs important tasks",
    "description": "The learner distinguishes between what is time‑sensitive and what has high impact, using a framework (e.g., Eisenhower).",
    "weight": 1.0,
    "required": true,
    "position": 1,
    "levels": [
      {
        "level_1": {
          "description": "Treats all tasks as equally urgent; no prioritisation.",
          "examples": [
            "I'll just do whatever comes in first."
          ]
        }
      },
      {
        "level_2": {
          "description": "Prioritises based on urgency only, ignoring importance.",
          "examples": [
            "The one with the earliest deadline goes first."
          ]
        }
      },
      {
        "level_3": {
          "description": "Considers both urgency and importance but applies inconsistently.",
          "examples": [
            "The stakeholder meeting is tomorrow, so that's urgent, but I also need to finish the dashboard."
          ]
        }
      },
      {
        "level_4": {
          "description": "Uses a framework (e.g., Eisenhower) to explicitly categorise tasks and decide order.",
          "examples": [
            "I'm using the Eisenhower matrix. The steering meeting slides are urgent and important – I'll do those now. The data cleanup is important but not urgent – I'll schedule it for after lunch. The optional knowledge share is neither – I'll park it for now."
          ]
        }
      },
      {
        "level_5": {
          "description": "Applies prioritisation with nuance, negotiates with stakeholders, and adjusts as new information arrives.",
          "examples": [
            "I've mapped all tasks to the Eisenhower grid. The urgent/important ones are the steering deck and the risk assessment. I'll start with those. For the less critical tasks, I'll send a quick update to stakeholders to confirm deadlines and see if any can be shifted. If a new urgent request comes in, I'll reassess and escalate if needed."
          ]
        }
      }
    ]
  },
  {
    "criterion_ref": "negotiate-workload",
    "skill_slug": "yes-with-conditions",
    "title": "Negotiates workload using 'yes, with conditions'",
    "description": "The learner commits to work but sets clear boundaries and trade‑offs.",
    "weight": 1.0,
    "required": true,
    "position": 2,
    "levels": [
      {
        "level_1": {
          "description": "Says 'yes' without negotiating, leading to overload or missed deadlines.",
          "examples": [
            "Sure, I'll get that done too."
          ]
        }
      },
      {
        "level_2": {
          "description": "Says 'no' outright without offering alternatives.",
          "examples": [
            "I can't do that."
          ]
        }
      },
      {
        "level_3": {
          "description": "Tries to negotiate but in a vague way.",
          "examples": [
            "I'll try to fit it in."
          ]
        }
      },
      {
        "level_4": {
          "description": "Uses 'yes, with conditions' clearly, specifying trade‑offs.",
          "examples": [
            "I can take that on. To make sure I deliver both, I'd need to push the dashboard deadline to Friday. Would that work for you?"
          ]
        }
      },
      {
        "level_5": {
          "description": "Negotiates proactively, offers options, and aligns on priorities with stakeholders.",
          "examples": [
            "I'm happy to help with the user metrics for the 9am meeting. Currently I have two other tasks due Friday. If I prioritise your request, I can have a high‑level summary by 5pm today, but the detailed dashboard would then slip to Monday. Alternatively, I could deliver a robust dashboard by Friday if you can share the specific metrics you need by 3pm. Which approach would work best for you?"
          ]
        }
      }
    ]
  }
]
```

---

## 4. Seed Data Implementation Notes

When seeding the database, the system should:

1. Insert all skills with `organisation_id = NULL`.
2. Insert all competencies with `organisation_id = NULL`.
3. Insert into `competency_skill_map` the mappings with weights (if weight is not specified, default to 1.0).
4. For each rubric, create a `RubricRecord` with the given rubric ID, skill slug, organisation NULL, content type, schema version, and name. Then create a `RubricVersionRecord` with version "1.0", status "published", and the criteria JSON as defined.

The criteria JSON should be stored exactly as in the examples above. The `levels` objects must have keys exactly `level_1`, `level_2`, etc., and each must contain `description` and `examples` (list of strings).

---

This canonical set provides a solid foundation for the soft‑skills platform. Organisations can override any of these items by creating their own with an `organisation_id`. Overrides completely replace the canonical version for that organisation.