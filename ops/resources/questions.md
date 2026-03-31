# Canonical Collection: Consultancy Fundamentals

This collection provides a progressive learning path for core consulting skills. It includes quick practice prompts (binary rubrics), an interview prompt (5‑level rubric), and a multi‑step scenario (5‑level rubric). All items target the canonical skills and competencies defined earlier.

---

## Collection Metadata

```json
{
  "title": "Consultancy Fundamentals",
  "description": "A collection of exercises to build core consulting skills: stakeholder management, structured thinking, asking the right questions, navigating ambiguity, client-site professionalism, and effective communication.",
  "content_format": ["quick_practice_prompt", "interview_prompt", "scenario_step"],
  "target_competencies": ["stakeholder-management", "consulting-mindset", "client-site-professionalism", "effective-communication"],
  "difficulty": "intermediate"
}
```

---

## Item 1: Quick Practice Prompt – "Client Asks for Impossible Deadline"

**Type:** `quick_practice_prompt`  
**Rubric:** `quick_practice_reset_timeline@v1` (binary: pass/fail)  
**Target Skills:** `expectation-setting`, `yes-with-conditions`, `professionalism-under-pressure`

### Prompt Text

> **Scenario:**  
> You are a consultant working on a data migration project. A senior stakeholder, Elena (Head of Marketing), sends you an email at 4:30pm on Friday:  
> *“I need a full dashboard of last quarter’s campaign performance by Monday 9am for the board meeting. I know it’s tight, but you can pull it together, right?”*  
>  
> You estimate the task would normally take two days, and you already have planned work for the weekend. You cannot deliver a complete dashboard by Monday without sacrificing quality or your personal commitments.  
>  
> **Your Task:**  
> Write a short reply (3–5 sentences) to Elena. Use the “yes, with conditions” framework to reset expectations while maintaining a professional relationship.

### Rubric Criteria (Binary)

| Level | Description |
|-------|-------------|
| **Fail** | Does not negotiate; either says “yes” unconditionally (risking burnout/delivery) or says “no” without offering alternatives. |
| **Pass** | Uses “yes, with conditions”: acknowledges request, states a realistic deliverable (e.g., high‑level summary or partial dashboard), proposes a timeline, and asks for confirmation. |

**Example Pass Response:**
> “Hi Elena, I’m happy to support the board meeting. To give you something robust, I can prepare a high‑level summary of the top three campaign metrics by Monday 9am. For the full dashboard, I’d need until Wednesday – would that work? If you’d prefer the full version, I could prioritise it if we shift my current tasks; let me know your preference.”

---

## Item 2: Quick Practice Prompt – "Clarifying an Ambiguous Request"

**Type:** `quick_practice_prompt`  
**Rubric:** `quick_practice_text@v1` (binary: pass/fail)  
**Target Skills:** `asking-the-right-questions`, `ambiguity-navigation`

### Prompt Text

> **Scenario:**  
> It’s your second week on client site. Your manager, Sarah, sends you a Teams message:  
> *“Can you pull some numbers on our digital sales performance and send me something before tomorrow’s steering meeting? Just something I can talk to.”*  
>  
> You have no clear brief, and you’re not sure what “digital sales performance” means or what format is expected.  
>  
> **Your Task:**  
> Write a short Teams reply (3–6 sentences) that acknowledges the request and asks specific clarifying questions to reduce ambiguity. Use the 5Ws/1H framework (who, what, when, where, why, how).

### Rubric Criteria (Binary)

| Level | Description |
|-------|-------------|
| **Fail** | Does not ask clarifying questions; either says “yes” without details or asks a vague question like “What exactly do you need?”. |
| **Pass** | Asks at least three targeted questions covering purpose, scope, format, and deadline. Shows proactive thinking. |

**Example Pass Response:**
> “Hi Sarah, happy to help. To give you something useful for the steering meeting, could you clarify:  
> 1) What metrics matter most (e.g., conversion rates, revenue, channel breakdown)?  
> 2) Is a one‑page summary enough, or would you prefer a slide?  
> 3) What time tomorrow would you need it? I’ll prepare a draft and share it by 10am if that works.”

---

## Item 3: Interview Prompt – "Managing a Difficult Stakeholder"

**Type:** `interview_prompt`  
**Rubric:** `interview_text@v1` (5‑level)  
**Target Competency:** `stakeholder-management`  
**Target Skills:** `empathy`, `conflict-facilitation`, `expectation-setting`, `active-listening`

### Prompt Text

> **Competency Interview Question:**  
> “Tell me about a time when you had to manage a difficult stakeholder. What was the situation, what actions did you take, and what was the result?”

**Guidance for the Learner:**  
Use the STARR framework (Situation, Task, Action, Result, Reflection). Focus on your specific behaviours, the challenges you faced, and what you learned.

### Rubric Criteria (5‑level, based on canonical `interview_text@v1`)

The rubric evaluates five dimensions:

1. **Situation & Task Clarity** – Sets context and defines the problem clearly.
2. **Action: Communication & Empathy** – Describes how they listened, empathised, and engaged.
3. **Action: Negotiation & Expectation Setting** – Shows how they set boundaries or found common ground.
4. **Result** – States a measurable or observable outcome.
5. **Reflection** – Demonstrates learning and growth.

Each dimension is scored 1‑5, with overall score averaged.

| Level | Description |
|-------|-------------|
| **1** | Lacks structure; minimal detail; no reflection; outcome unclear. |
| **2** | Basic structure but missing key elements; actions vague; limited reflection. |
| **3** | Clear STARR structure; describes reasonable actions; some reflection; outcome stated. |
| **4** | Strong STARR; specific actions showing empathy and negotiation; clear outcome; good reflection. |
| **5** | Exemplary STARR; demonstrates advanced stakeholder skills; quantifiable outcome; deep reflection connecting to professional growth. |

---

## Item 4: Scenario – "MoneyCraft Data Centralisation"

**Type:** `scenario_step` (multi‑step)  
**Rubric:** `scenario_text@v1` (5‑level)  
**Target Competencies:** `consulting-mindset`, `stakeholder-management`, `client-site-professionalism`  
**Target Skills:** `structured-thinking`, `stakeholder-analysis`, `stakeholder-engagement`, `ambiguity-navigation`, `asking-the-right-questions`, `presentation-facilitation`

### Mock Company

```json
{
  "name": "MoneyCraft Bank",
  "industry": "Fintech / Retail Banking",
  "operating_context": "MoneyCraft is a mid‑sized digital bank in the UK. It has grown rapidly over five years, acquiring several smaller fintechs. As a result, its data function is fragmented: 80 data specialists are spread across eight departments, each using different tools and practices. The CEO wants to centralise these teams into a new Data Hub in Canary Wharf to improve collaboration, retention, and competitive edge."
}
```

### Mock People

**Cristina Yang** (CEO)  
- Goals: Centralise data to accelerate innovation; retain top talent; get board approval for the £10M investment.  
- Communication Style: Visionary, impatient, expects concise summaries.

**Samir Hicks** (Head of Lending)  
- Goals: Keep his dedicated data team to maintain lending model updates; worries centralisation will slow his department.  
- Communication Style: Protective of his team; uses technical jargon; can be defensive.

**Sarah Chen** (Senior Data Specialist)  
- Goals: Wants career growth and modern tools; open to centralisation but worried about relocation (she has young children).  
- Communication Style: Analytical, reserved, values evidence.

**James Okonkwo** (Head of HR)  
- Goals: Ensure smooth transition; manage relocation logistics; avoid union issues.  
- Communication Style: Process‑oriented, collaborative.

### Supporting Artifacts

**Artifact 1: Email from CEO to All Department Heads**  
*Subject: Project Insight 2025 – Data Centralisation*  
> “Dear colleagues, as we discussed in the leadership offsite, we will be centralising our data teams into a new hub in Canary Wharf. This will give us standardised tools, clearer career paths, and a competitive edge. I will appoint a project lead shortly. Please prepare to support this transition. – Cristina”

**Artifact 2: Slack Thread (excerpt)**  
> **Samir Hicks:** “Cristina, my team has built proprietary models that rely on our current setup. Moving them will disrupt our lending pipeline.”  
> **Cristina Yang:** “Samir, I appreciate the concern, but we need to think long‑term. The hub will include all departments – we’ll ensure transition plans are robust.”

**Artifact 3: Internal Document (excerpt)**  
> *Current Data Landscape*  
> - Lending: uses SAS, 20 specialists  
> - Digital Banking: uses Python + Tableau, 15 specialists  
> - Risk: uses R + Power BI, 10 specialists  
> - … (others)

### Scenario Steps

The scenario is delivered as a single `scenario_step` record with a long `prompt_text` that guides the learner through three phases. The rubric assesses the learner’s overall performance across all phases.

#### Step 1: Initial Briefing (Stakeholder Analysis)

> **Your Role:** You are a business analyst assigned to Project Insight 2025. Your first task is to conduct a stakeholder analysis to understand who matters and how to engage them.
>  
> **Task 1:** Based on the mock company, people, and artifacts provided, identify at least six stakeholder groups. For each, map them onto Mendelow’s Power/Interest grid and propose an engagement strategy. Write a brief memo (200‑300 words) to the project manager.

#### Step 2: Interview a Resistant Department Head (Active Listening & Questioning)

> You schedule an interview with Samir Hicks, Head of Lending. He is known to be resistant to the centralisation. Your goal is to understand his concerns, uncover hidden needs, and build rapport.
>  
> **Task 2:** Draft a set of 5‑8 interview questions you would ask Samir. Use a mix of open, probing, and closed questions. Include at least one question that acknowledges his concerns.

#### Step 3: Present a High‑Level Recommendation (Structured Communication)

> After analysing stakeholder feedback, you need to present a recommendation to the steering committee (Cristina, Samir, HR, etc.) on how to manage the transition.
>  
> **Task 3:** Write a 1‑page executive summary that outlines:
> - The As‑Is and To‑Be states
> - The key gaps (people, process, technology)
> - Two options for the transition (e.g., phased vs. big‑bang) with pros/cons
> - A clear recommendation and next steps

### Rubric Criteria (5‑level, based on canonical `scenario_text@v1`)

The rubric assesses the learner’s performance across three dimensions:

1. **Stakeholder Analysis & Engagement** (35%) – Correct identification, power/interest mapping, tailored engagement strategies, evidence of empathy.
2. **Interviewing & Questioning** (35%) – Use of open/probing questions, active listening signals, ability to uncover hidden concerns.
3. **Structured Communication & Recommendation** (30%) – Clear use of As‑Is / Gap / To‑Be framework, logical options, concise executive summary, actionable next steps.

Each dimension is scored 1‑5; final score weighted average.

| Level | Description |
|-------|-------------|
| **1** | Misses key stakeholders; questions are leading or irrelevant; communication lacks structure. |
| **2** | Identifies some stakeholders but mapping is superficial; questions are mostly closed; recommendation is vague. |
| **3** | Adequate stakeholder analysis; reasonable questions; structured recommendation with some gaps. |
| **4** | Good stakeholder analysis with correct grid placement; effective questioning; clear, well‑structured recommendation. |
| **5** | Excellent stakeholder analysis with nuanced mapping; exemplary questions that uncover hidden issues; compelling, business‑focused recommendation. |

---

## Summary of Canonical Rubrics Used

| Rubric ID | Content Type | Scoring |
|-----------|--------------|--------|
| `quick_practice_reset_timeline@v1` | Quick Practice | Binary (pass/fail) |
| `quick_practice_text@v1` | Quick Practice | Binary (pass/fail) |
| `interview_text@v1` | Interview Prompt | 5‑level (1‑5) |
| `scenario_text@v1` | Scenario | 5‑level (1‑5) |

All rubrics have been defined in the canonical set. No new rubrics are needed for this collection.

---

This collection provides a complete, progressive learning path that aligns with the canonical skills and competencies. It can be seeded as a platform‑owned collection (`organisation_id = NULL`) and used across all organisations.
