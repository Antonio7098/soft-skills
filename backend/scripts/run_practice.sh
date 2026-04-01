#!/usr/bin/env bash
set -uo pipefail

BASE="http://127.0.0.1:9001/api"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

api() {
    local method="$1" path="$2"
    shift 2
    curl -s -X "$method" "$BASE$path" \
        -H "Content-Type: application/json" \
        "$@" 2>&1
}

# ── Register user ──────────────────────────────────────────────────────
echo ""
echo "━━━ Registering test user ━━━"
REG=$(api POST /auth/register -d '{
  "email": "learner-'$(date +%s)'@example.com",
  "display_name": "Practice Learner",
  "target_role": "Junior Consultant",
  "goals": ["Improve stakeholder management", "Build structured thinking"],
  "practice_preferences": {}
}')
USER_ID=$(echo "$REG" | jq -r '.data.id')
echo "  User: $USER_ID"

# ── Get IDs ────────────────────────────────────────────────────────────
COL=$(api GET /collections)
COLLECTION_ID=$(echo "$COL" | jq -r '.data[0].id')
ITEM1=$(echo "$COL" | jq -r '.data[0].prompt_items[0].id')  # Impossible Deadline
ITEM2=$(echo "$COL" | jq -r '.data[0].prompt_items[1].id')  # Ambiguous Request
ITEM3=$(echo "$COL" | jq -r '.data[0].prompt_items[2].id')  # Difficult Stakeholder
SCENARIO_ID=$(echo "$COL" | jq -r '.data[0].scenarios[0].id')  # MoneyCraft

echo "  Items: $ITEM1 / $ITEM2 / $ITEM3 / scenario=$SCENARIO_ID"

# ── Practice responses ─────────────────────────────────────────────────
RESPONSE1='Hi Elena, I appreciate you reaching out and I want to make sure the board has what they need. A full dashboard by Monday 9am would compromise data quality, which I know is important for this meeting. What I can deliver by then is a concise one-page summary of the top three campaign metrics — open rate, conversion rate, and ROI — with clear trend arrows. For the full interactive dashboard, I would need until Wednesday end of day. Would the summary be sufficient for Monday, or should we discuss reprioritising my current tasks to accelerate the full version?'

RESPONSE2='Hi Sarah, happy to help with the steering meeting prep. To make sure I give you something useful, could you clarify a few things?
1) What specific metrics matter most — conversion rates, revenue by channel, or customer acquisition cost?
2) Is a one-page summary with top-line trends enough, or do you need a more detailed breakdown with charts?
3) What time tomorrow do you need it by? I can have a draft ready by 10am for your review.
I will assume we are looking at Q2 digital performance unless you tell me otherwise — just flagging that assumption so we stay aligned.'

RESPONSE3='Situation: In my previous role as a business analyst on a CRM implementation project, I encountered a difficult stakeholder — the VP of Sales, who was blocking our requirements workshops.

Task: My job was to gather sales workflow requirements, but she refused to attend sessions, claiming her team was too busy with quarter-end targets.

Action: I requested a 1:1 coffee meeting outside the formal workshop setting. I started by listening — I asked her to tell me about her biggest pain points with the current system. It turned out she had been burned by a previous IT project that promised minimal disruption but caused a 3-week reporting gap that cost her team deals. I acknowledged that concern as completely valid. I then proposed a solution: I would create a parallel-running plan so her team could fall back to the old system during transition. I also restructured the workshops to 30-minute slot-based sessions that fit around her team schedule.

Result: She became our biggest champion. She attended the next workshop and brought two of her team leads. We completed the requirements phase on time with full stakeholder sign-off.

Reflection: I learned that resistance often masks a past negative experience. The key insight was that pushing for compliance through formal channels was less effective than addressing the underlying fear. Since then, I always try to understand the emotional drivers behind stakeholder resistance before trying to solve the logistical problem.'

RESPONSE4='STAKEHOLDER ANALYSIS

I identified eight stakeholder groups for Project Insight 2025:

1. CEO (Cristina Yang) — High Power / High Interest → Manage Closely. Strategy: Weekly executive briefings with concise summaries focused on ROI and risk mitigation.

2. Head of Lending (Samir Hicks) — High Power / Medium Interest → Keep Satisfied. Strategy: Dedicated 1:1 sessions to address concerns about model continuity; position his team as "migration champions."

3. Head of HR (James Okonkwo) — Medium Power / High Interest → Keep Informed. Strategy: Joint planning sessions on relocation logistics and union engagement.

4. Senior Data Specialists — Low Power / High Interest → Keep Informed. Strategy: Town halls, career path transparency, and anonymous feedback channels.

5. Board of Directors — High Power / Low Interest → Keep Satisfied. Strategy: Quarterly progress reports with risk register updates.

6. Department Heads (non-lending) — Medium Power / Medium Interest → Monitor. Strategy: Monthly cross-functional sync meetings.

7. Union Representatives — Medium Power / Medium Interest → Monitor. Strategy: Early engagement through HR to prevent escalation.

8. External Fintech Integration Teams — Low Power / Low Interest → Monitor. Strategy: Technical documentation and API migration guides.

INTERVIEW PLAN FOR SAMIR HICKS

I would schedule a 45-minute meeting in his office to reduce defensiveness. My question sequence:

1. "Tell me about how your data team currently supports the lending pipeline — what does a typical sprint look like?" (Open, builds rapport)

2. "You mentioned in the Slack thread that the current setup supports proprietary models. Can you walk me through what makes those models dependent on your current tooling?" (Probing)

3. "If centralisation were to happen, what would be the minimum conditions for your team to feel confident that lending operations would not be disrupted?" (Empathetic, solution-oriented)

4. "What career opportunities would you want for your team members in the new hub?" (Open, reframes threat as opportunity)

5. "Who on your team would be best placed to help design the transition plan for lending models?" (Closed, invites participation)

6. "If we could guarantee zero disruption to your pipeline during migration, would that change your view on centralisation?" (Closed, tests underlying assumption)

EXECUTIVE SUMMARY

As-Is: 80 data specialists across 8 departments, fragmented tools (SAS, Python, R, Excel), no standardisation, no common career paths, retention challenges.

To-Be: Centralised Data Hub in Canary Wharf with standardised tools, clear career ladders, improved collaboration, and competitive talent proposition.

Gap Analysis:
- People: Relocation logistics, cultural change, potential 12-18% attrition
- Process: Tool migration, workflow redesign, knowledge transfer
- Technology: Platform standardisation, data pipeline consolidation

Options:
A) Phased Approach (12 months): Pilot with 2 departments first, iterate, then full rollout. Lower risk, slower ROI, builds internal advocacy.
B) Big-Bang (6 months): All departments migrate simultaneously. Higher risk, faster ROI, requires heavy change management budget.

Recommendation: Option A (Phased) with a 3-month pilot in Lending and Digital Banking. Lending because engaging Samir early converts resistance to advocacy. Digital Banking because they already use Python and can serve as a technical reference model.

Next Steps:
1. Approve pilot budget and appoint change lead by Friday
2. Samir Hicks nominated as Lending migration champion
3. Pilot kickoff in 2 weeks with fortnightly steering reviews
4. Full business case for Phase 2 presented to board at T+3 months'

# ── Run practice sessions ──────────────────────────────────────────────
run_session() {
    local label="$1" practice_type="$2" start_path="$3" start_body="$4" response="$5"
    echo ""
    echo "━━━ $label ━━━"

    # Start session
    local session_resp
    session_resp=$(api POST "$start_path" -H "X-User-ID: $USER_ID" -d "$start_body")
    local attempt_id prompt_text rubric_id
    attempt_id=$(echo "$session_resp" | jq -r '.data.attempt_id // empty')
    prompt_text=$(echo "$session_resp" | jq -r '.data.prompt.prompt_text // "N/A"' | head -c 120)
    rubric_id=$(echo "$session_resp" | jq -r '.data.prompt.rubric_id // "N/A"')

    if [ -z "$attempt_id" ] || [ "$attempt_id" = "null" ]; then
        echo "  FAIL: Could not start session"
        echo "  Response: $session_resp" | head -5
        return 1
    fi

    echo "  Prompt: ${prompt_text}..."
    echo "  Rubric: $rubric_id"
    echo "  Attempt: $attempt_id"
    echo "  Submitting response ($(echo "$response" | wc -c) chars)..."

    # Submit response (triggers real LLM marking)
    local submit_resp
    submit_resp=$(api POST "/attempts/$attempt_id/submit" \
        -H "X-User-ID: $USER_ID" \
        -d "$(jq -n --arg r "$response" '{"response_text": $r}')")

    local status
    status=$(echo "$submit_resp" | jq -r '.data.status // "unknown"')
    echo "  Status: $status"

    if [ "$status" = "assessed" ]; then
        local overall_score validation_status
        overall_score=$(echo "$submit_resp" | jq -r '.data.assessment.overall_score // "N/A"')
        validation_status=$(echo "$submit_resp" | jq -r '.data.assessment.validation_status // "N/A"')
        echo "  Overall Score: $overall_score"
        echo "  Validation: $validation_status"

        echo "  ── Per-Skill Scores ──"
        echo "$submit_resp" | jq -r '
          (.data.assessment.skill_scores // .data.assessment.per_skill_assessments // [])[] |
          "    \(.skill_slug): \(.score)/5 — \(.rationale // "no rationale" | .[0:120])"
        ' 2>/dev/null

        echo "  ── Strengths ──"
        echo "$submit_resp" | jq -r '
          (.data.assessment.strengths // [])[] | "    + \(.[0:140])"
        ' 2>/dev/null

        echo "  ── Weaknesses ──"
        echo "$submit_resp" | jq -r '
          (.data.assessment.weaknesses // [])[] | "    − \(.[0:140])"
        ' 2>/dev/null

        echo "  ── Next Actions ──"
        echo "$submit_resp" | jq -r '
          (.data.assessment.next_actions // [])[] | "    → \(.[0:140])"
        ' 2>/dev/null

        echo "  ── Evidence ──"
        echo "$submit_resp" | jq -r '
          (.data.assessment.evidence // [])[] |
          "    [\( .skill_slug // "?")] \"\( .quote // "?" | .[0:80])\" → \( .explanation // "?" | .[0:100])"
        ' 2>/dev/null
    elif [ "$status" = "assessment_rejected" ]; then
        echo "  REJECTED: $(echo "$submit_resp" | jq -r '.data.last_error_code // "unknown"')"
    else
        echo "  Full response:"
        echo "$submit_resp" | jq '.' | head -40
    fi
}

# Item 1: Quick Practice — Impossible Deadline
run_session \
    "1/4 — Client Asks for Impossible Deadline (quick_practice)" \
    "quick_practice" \
    "/attempts/quick-practice/sessions" \
    "{\"prompt_item_id\": \"$ITEM1\"}" \
    "$RESPONSE1"

# Item 2: Quick Practice — Clarifying Ambiguous Request
run_session \
    "2/4 — Clarifying an Ambiguous Request (quick_practice)" \
    "quick_practice" \
    "/attempts/quick-practice/sessions" \
    "{\"prompt_item_id\": \"$ITEM2\"}" \
    "$RESPONSE2"

# Item 3: Interview — Managing a Difficult Stakeholder
run_session \
    "3/4 — Managing a Difficult Stakeholder (interview)" \
    "interview" \
    "/attempts/interview/sessions" \
    "{\"prompt_item_id\": \"$ITEM3\"}" \
    "$RESPONSE3"

# Item 4: Scenario — MoneyCraft Data Centralisation
run_session \
    "4/4 — MoneyCraft Data Centralisation (scenario)" \
    "scenario" \
    "/attempts/scenario/sessions" \
    "{\"scenario_id\": \"$SCENARIO_ID\"}" \
    "$RESPONSE4"

echo ""
echo "━━━ All practice sessions complete ━━━"
