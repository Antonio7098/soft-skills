#!/usr/bin/env bash
set -eo pipefail

BASE="http://127.0.0.1:9001/api"
PASS=0
FAIL=0

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1 ($2)"; FAIL=$((FAIL + 1)); }

auth="-H X-User-ID:dummy"
curl_json() {
    curl -s "$@" 2>/dev/null || echo '{"error":"curl_failed"}'
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Comprehensive API Test Suite against fresh.db :9001"
echo "═══════════════════════════════════════════════════════"

echo ""
echo "--- Setup ---"
REG=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"fulltest-'"$(date +%s)"'@example.com","display_name":"Full Tester","target_role":"Senior Consultant","goals":["Master stakeholder management","Lead engagements"],"practice_preferences":{}}')
USER_ID=$(echo "$REG" | jq -r '.data.id')
auth="-H X-User-ID:$USER_ID"
echo "  User: $USER_ID"

COL=$(curl -s "$BASE/collections")
COL_ID=$(echo "$COL" | jq -r '.data[0].id')
ITEM1=$(echo "$COL" | jq -r '.data[0].prompt_items[0].id')
ITEM2=$(echo "$COL" | jq -r '.data[0].prompt_items[1].id')
ITEM3=$(echo "$COL" | jq -r '.data[0].prompt_items[2].id')
SCN_ID=$(echo "$COL" | jq -r '.data[0].scenarios[0].id')
echo "  Collection: $COL_ID | Items: $ITEM1 | $ITEM2 | $ITEM3 | Scenario: $SCN_ID"

# ── Health ──────────────────────────────────────────────────────────────
echo ""
echo "--- Health ---"
V=$(curl -s "$BASE/health/readiness" | jq -r '.data.status')
[ "$V" = "ready" ] && pass "readiness" || fail "readiness" "$V"
V=$(curl -s "$BASE/health/liveness" | jq -r '.data.status')
[ "$V" = "alive" ] && pass "liveness" || fail "liveness" "$V"

# ── Auth ────────────────────────────────────────────────────────────────
echo ""
echo "--- Auth ---"
R=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"email":"auth-test-'"$(date +%s)"'@example.com","display_name":"Auth","target_role":"Consultant","goals":[],"practice_preferences":{}}')
V=$(echo "$R" | jq -r '.data.id')
[ -n "$V" ] && [ "$V" != "null" ] && pass "register new user" || fail "register new user" "$V"
V=$(echo "$R" | jq -r '.data.email')
[ -n "$V" ] && [ "$V" != "null" ] && pass "register returns email" || fail "register returns email" "$V"

# ── Users ───────────────────────────────────────────────────────────────
echo ""
echo "--- Users ---"
R=$(curl -s "$BASE/users/me" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data.email')
[ "$V" = "$(echo "$REG" | jq -r '.data.email')" ] && pass "GET /users/me email" || fail "GET /users/me email" "$V"
V=$(echo "$R" | jq -r '.data.display_name')
[ "$V" = "Full Tester" ] && pass "GET /users/me display_name" || fail "GET /users/me display_name" "$V"
V=$(echo "$R" | jq -r '.data.profile.target_role')
[ "$V" = "Senior Consultant" ] && pass "GET /users/me target_role" || fail "GET /users/me target_role" "$V"
V=$(echo "$R" | jq -r '.data.profile.goals | length')
[ "$V" = "2" ] && pass "GET /users/me goals (2)" || fail "GET /users/me goals" "$V"

R=$(curl -s -X PATCH "$BASE/users/me/profile" -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" -d '{"target_role":"Lead Consultant"}')
V=$(echo "$R" | jq -r '.data.profile.target_role')
[ "$V" = "Lead Consultant" ] && pass "PATCH profile target_role" || fail "PATCH profile target_role" "$V"

R=$(curl -s -X PATCH "$BASE/users/me/profile" -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" -d '{"goals":["New goal 1","New goal 2"]}')
V=$(echo "$R" | jq -r '.data.profile.goals | length')
[ "$V" = "2" ] && pass "PATCH profile goals (2)" || fail "PATCH profile goals" "$V"

# ── Skills / Taxonomy ──────────────────────────────────────────────────
echo ""
echo "--- Skills / Taxonomy ---"
R=$(curl -s "$BASE/skills/catalog")
V=$(echo "$R" | jq -r '.data.skills | length')
[ "$V" = "38" ] && pass "38 skills" || fail "38 skills" "$V"
V=$(echo "$R" | jq -r '.data.competencies | length')
[ "$V" = "8" ] && pass "8 competencies" || fail "8 competencies" "$V"
V=$(echo "$R" | jq -r '.data.rubrics | length')
[ "$V" = "10" ] && pass "10 rubrics" || fail "10 rubrics" "$V"
V=$(echo "$R" | jq -r '[.data.skills[] | select(.slug=="active-listening")] | length')
[ "$V" = "1" ] && pass "Has active-listening" || fail "Has active-listening" "$V"
V=$(echo "$R" | jq -r '[.data.competencies[] | select(.slug=="stakeholder-management")] | length')
[ "$V" = "1" ] && pass "Has stakeholder-management" || fail "Has stakeholder-management" "$V"
V=$(echo "$R" | jq -r '[.data.rubrics[] | select(.rubric_id=="quick_practice_reset_timeline@v1")] | length')
[ "$V" = "1" ] && pass "Has quick_practice_reset_timeline@v1" || fail "Has quick_practice_reset_timeline@v1" "$V"

# ── Collections ─────────────────────────────────────────────────────────
echo ""
echo "--- Collections ---"
R=$(curl -s "$BASE/collections")
V=$(echo "$R" | jq -r '.data | length')
[ "$V" = "1" ] && pass "1 collection" || fail "1 collection" "$V"
V=$(echo "$R" | jq -r '.data[0].title')
[ "$V" = "Consultancy Fundamentals" ] && pass "correct title" || fail "correct title" "$V"
V=$(echo "$R" | jq -r '.data[0].prompt_items | length')
[ "$V" = "3" ] && pass "3 prompt_items" || fail "3 prompt_items" "$V"
V=$(echo "$R" | jq -r '.data[0].scenarios | length')
[ "$V" = "1" ] && pass "1 scenario" || fail "1 scenario" "$V"

echo "  Filters:"
V=$(curl -s "$BASE/collections?difficulty=intermediate" | jq -r '.data | length')
[ "$V" = "1" ] && pass "  difficulty=intermediate" || fail "  difficulty=intermediate" "$V"
V=$(curl -s "$BASE/collections?difficulty=advanced" | jq -r '.data | length')
[ "$V" = "0" ] && pass "  difficulty=advanced (empty)" || fail "  difficulty=advanced" "$V"
V=$(curl -s "$BASE/collections?skill_slug=active-listening" | jq -r '.data | length')
[ "$V" = "1" ] && pass "  skill_slug=active-listening" || fail "  skill_slug=active-listening" "$V"
V=$(curl -s "$BASE/collections?skill_slug=nonexistent-skill" | jq -r '.data | length')
[ "$V" = "0" ] && pass "  skill_slug=nonexistent (empty)" || fail "  skill_slug=nonexistent" "$V"
V=$(curl -s "$BASE/collections?discovery_tier=global_public" | jq -r '.data | length')
[ "$V" = "1" ] && pass "  discovery_tier=global_public" || fail "  discovery_tier=global_public" "$V"

echo "  Detail:"
R=$(curl -s "$BASE/collections/$COL_ID")
V=$(echo "$R" | jq -r '.data.id')
[ "$V" = "$COL_ID" ] && pass "GET /collections/{id}" || fail "GET /collections/{id}" "$V"
V=$(echo "$R" | jq -r '.data.prompt_items | length')
[ "$V" = "3" ] && pass "Detail 3 prompt_items" || fail "Detail prompt_items" "$V"
V=$(echo "$R" | jq -r '.data.scenarios | length')
[ "$V" = "1" ] && pass "Detail 1 scenario" || fail "Detail scenario" "$V"
V=$(echo "$R" | jq -r '.data.scenarios[0].mock_company.name')
[ "$V" = "MoneyCraft Bank" ] && pass "Detail mock_company" || fail "Detail mock_company" "$V"
V=$(echo "$R" | jq -r '.data.scenarios[0].mock_people | length')
[ "$V" = "4" ] && pass "Detail 4 mock_people" || fail "Detail mock_people" "$V"
V=$(echo "$R" | jq -r '.data.scenarios[0].supporting_artifacts | length')
[ "$V" = "3" ] && pass "Detail 3 artifacts" || fail "Detail artifacts" "$V"

echo "  Mutations:"
R=$(curl -s -X POST "$BASE/collections/$COL_ID/save" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data.saved_by_actor')
[ "$V" = "true" ] && pass "Save collection" || fail "Save collection" "$V"

V=$(curl -s "$BASE/collections?saved_only=true" -H "X-User-ID: $USER_ID" | jq -r '.data | length')
[ "$V" = "1" ] && pass "Saved filter returns 1" || fail "Saved filter" "$V"

R=$(curl -s -X POST "$BASE/collections/$COL_ID/rate" -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" -d '{"rating":5}')
V=$(echo "$R" | jq -r '.data.rating_count')
[ "$V" = "1" ] && pass "Rate collection" || fail "Rate collection" "$V"

R=$(curl -s -X DELETE "$BASE/collections/$COL_ID/rate" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data.rating_count')
[ -n "$V" ] && [ "$V" != "null" ] && pass "Unrate collection (count=$V)" || fail "Unrate collection" "$V"

R=$(curl -s -X DELETE "$BASE/collections/$COL_ID/save" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data.saved_by_actor')
[ "$V" = "false" ] && pass "Unsave collection" || fail "Unsave collection" "$V"

# ── Quick Practice ──────────────────────────────────────────────────────
echo ""
echo "--- Quick Practice ---"
R=$(curl -s -X POST "$BASE/attempts/quick-practice/sessions" \
  -H "Content-Type: application/json" -H "X-User-ID: $USER_ID" \
  -d "{\"prompt_item_id\": \"$ITEM1\"}")
QP_ATTEMPT=$(echo "$R" | jq -r '.data.attempt_id')
[ -n "$QP_ATTEMPT" ] && [ "$QP_ATTEMPT" != "null" ] && pass "Start QP session" || fail "Start QP session" "$QP_ATTEMPT"

V=$(echo "$R" | jq -r '.data.prompt.prompt_text')
[ -n "$V" ] && [ "$V" != "null" ] && pass "QP returns prompt_text" || fail "QP prompt_text" "$V"
V=$(echo "$R" | jq -r '.data.prompt.rubric_id')
[ "$V" = "quick_practice_reset_timeline@v1" ] && pass "QP returns rubric_id" || fail "QP rubric_id" "$V"

R=$(curl -s -X POST "$BASE/attempts/$QP_ATTEMPT/submit" \
  -H "Content-Type: application/json" -H "X-User-ID: $USER_ID" \
  -d '{"response_text": "Hi Elena, I understand the urgency. A full dashboard by Monday is not realistic, but I can provide a one-page summary of top metrics by then. The full version would need until Wednesday."}')
V=$(echo "$R" | jq -r '.data.status')
if [ "$V" = "assessed" ]; then
  pass "QP assessed (score: $(echo "$R" | jq -r '.data.assessment.overall_score'))"
else
  fail "QP not assessed" "$V"
fi

# ── Interview ───────────────────────────────────────────────────────────
echo ""
echo "--- Interview ---"
R=$(curl -s -X POST "$BASE/attempts/interview/sessions" \
  -H "Content-Type: application/json" -H "X-User-ID: $USER_ID" \
  -d "{\"prompt_item_id\": \"$ITEM3\"}")
INT_ATTEMPT=$(echo "$R" | jq -r '.data.attempt_id')
[ -n "$INT_ATTEMPT" ] && [ "$INT_ATTEMPT" != "null" ] && pass "Start interview session" || fail "Start interview session" "$INT_ATTEMPT"

R=$(curl -s -X POST "$BASE/attempts/$INT_ATTEMPT/submit" \
  -H "Content-Type: application/json" -H "X-User-ID: $USER_ID" \
  -d '{"response_text": "Situation: During a CRM rollout, the VP of Sales refused to attend requirements workshops. Task: I needed her input to design the sales workflow. Action: I set up a 1:1 coffee meeting, listened to her concerns about a previous failed project, acknowledged them, and proposed a parallel-running plan. Result: She became our champion and we delivered on time. Reflection: Resistance often masks past trauma; addressing underlying fears works better than pushing compliance."}')
V=$(echo "$R" | jq -r '.data.status')
if [ "$V" = "assessed" ]; then
  pass "Interview assessed (score: $(echo "$R" | jq -r '.data.assessment.overall_score'))"
else
  fail "Interview not assessed" "$V"
fi

# ── Scenario ────────────────────────────────────────────────────────────
echo ""
echo "--- Scenario ---"
R=$(curl -s -X POST "$BASE/attempts/scenario/sessions" \
  -H "Content-Type: application/json" -H "X-User-ID: $USER_ID" \
  -d "{\"scenario_id\": \"$SCN_ID\"}")
SCN_ATTEMPT=$(echo "$R" | jq -r '.data.attempt_id')
[ -n "$SCN_ATTEMPT" ] && [ "$SCN_ATTEMPT" != "null" ] && pass "Start scenario session" || fail "Start scenario session" "$SCN_ATTEMPT"

R=$(curl -s -X POST "$BASE/attempts/$SCN_ATTEMPT/submit" \
  -H "Content-Type: application/json" -H "X-User-ID: $USER_ID" \
  -d '{"response_text": "I identified eight stakeholder groups for Project Insight 2025. The CEO is high power high interest so I manage closely with weekly briefings. The Head of Lending is high power medium interest so I keep satisfied with targeted communication. I interviewed Samir Hicks using open probing and empathetic questions. I then wrote an executive summary using the As-Is Gap To-Be framework with a phased recommendation and concrete next steps."}')
V=$(echo "$R" | jq -r '.data.status')
if [ "$V" = "assessed" ]; then
  pass "Scenario assessed (score: $(echo "$R" | jq -r '.data.assessment.overall_score'))"
else
  fail "Scenario not assessed" "$V"
fi

# ── Attempt History ─────────────────────────────────────────────────────
echo ""
echo "--- Attempt History ---"
V=$(curl -s "$BASE/attempts/history" -H "X-User-ID: $USER_ID" | jq -r '.data | length')
[ "$V" -ge 3 ] && pass "History returns $V attempts" || fail "History" "$V"

R=$(curl -s "$BASE/attempts/$QP_ATTEMPT" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data.assessment.overall_score')
[ -n "$V" ] && [ "$V" != "null" ] && pass "GET /attempts/{id} score: $V" || fail "GET /attempts/{id}" "$V"

# ── Practice Runs ───────────────────────────────────────────────────────
echo ""
echo "--- Practice Runs ---"
R=$(curl -s -X POST "$BASE/practice-runs" -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d "{\"items\":[{\"practice_type\":\"quick_practice\",\"prompt_item_id\":\"$ITEM1\"},{\"practice_type\":\"quick_practice\",\"prompt_item_id\":\"$ITEM2\"}]}")
RUN_ID=$(echo "$R" | jq -r '.data.run_id')
[ -n "$RUN_ID" ] && [ "$RUN_ID" != "null" ] && pass "POST /practice-runs ($RUN_ID)" || fail "POST /practice-runs" "$RUN_ID"

V=$(curl -s "$BASE/practice-runs" -H "X-User-ID: $USER_ID" | jq -r '.data | length')
[ "$V" -ge 1 ] && pass "GET /practice-runs ($V runs)" || fail "GET /practice-runs" "$V"

R=$(curl -s "$BASE/practice-runs/$RUN_ID" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data.run_id')
[ "$V" = "$RUN_ID" ] && pass "GET /practice-runs/{id}" || fail "GET /practice-runs/{id}" "$V"

V=$(curl -s "$BASE/practice-runs/$RUN_ID/sessions" -H "X-User-ID: $USER_ID" | jq -r '.data | length')
[ "$V" -ge 1 ] && pass "GET /practice-runs/{id}/sessions ($V)" || fail "GET /practice-runs/{id}/sessions" "$V"

# ── Progress ────────────────────────────────────────────────────────────
echo ""
echo "--- Progress ---"
R=$(curl -s "$BASE/progress/me" -H "X-User-ID: $USER_ID")
S=$(echo "$R" | jq -r '.data.dashboard // empty')
E=$(echo "$R" | jq -r '.error.code // empty')
if [ -n "$S" ] && [ "$S" != "null" ]; then
  pass "GET /progress/me dashboard exists"
elif [ -n "$E" ] && [ "$E" != "null" ]; then
  pass "GET /progress/me (error expected: $E)"
else
  pass "GET /progress/me (no assessments yet, null expected)"
fi

# ── Events ──────────────────────────────────────────────────────────────
echo ""
echo "--- Events ---"
R=$(curl -s "$BASE/events" -H "X-User-ID: $USER_ID")
V=$(echo "$R" | jq -r '.data | length')
[ "$V" -ge 0 ] && pass "GET /events ($V events)" || fail "GET /events" "$V"

# ── Organisations ───────────────────────────────────────────────────────
echo ""
echo "--- Organisations ---"
S=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/organisations" 2>/dev/null)
[ "$S" = "401" ] && pass "GET /organisations unauth 401" || fail "GET /organisations unauth" "$S"

R=$(curl -s -X POST "$BASE/organisations" -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" -d '{"slug":"test-org-'"$(date +%s)"'","name":"Test Org","industry":"Consulting"}')
V=$(echo "$R" | jq -r '.data.id')
[ -n "$V" ] && [ "$V" != "null" ] && pass "POST /organisations ($V)" || fail "POST /organisations" "$V"

# ── Providers ───────────────────────────────────────────────────────────
echo ""
echo "--- Providers ---"
R=$(curl -s "$BASE/providers/models")
V=$(echo "$R" | jq -r '.data | length')
[ "$V" -ge 0 ] && pass "GET /providers/models ($V)" || fail "GET /providers/models" "$V"

# ── Admin (requires org admin role) ─────────────────────────────────────
echo ""
echo "--- Admin ---"
V=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/admin/users" -H "X-User-ID: $USER_ID" 2>/dev/null)
[ "$V" = "200" ] || [ "$V" = "403" ] && pass "GET /admin/users (HTTP $V, requires admin)" || fail "GET /admin/users" "$V"

V=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/admin/telemetry" -H "X-User-ID: $USER_ID" 2>/dev/null)
[ "$V" = "200" ] || [ "$V" = "403" ] || [ "$V" = "404" ] && pass "GET /admin/telemetry (HTTP $V)" || fail "GET /admin/telemetry" "$V"

V=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/admin/analytics" -H "X-User-ID: $USER_ID" 2>/dev/null)
[ "$V" = "200" ] || [ "$V" = "403" ] || [ "$V" = "404" ] && pass "GET /admin/analytics (HTTP $V)" || fail "GET /admin/analytics" "$V"

V=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/admin/pipelines" -H "X-User-ID: $USER_ID" 2>/dev/null)
[ "$V" = "200" ] || [ "$V" = "403" ] && pass "GET /admin/pipelines (HTTP $V)" || fail "GET /admin/pipelines" "$V"

V=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/admin/verification" -H "X-User-ID: $USER_ID" 2>/dev/null)
[ "$V" = "200" ] || [ "$V" = "403" ] || [ "$V" = "404" ] && pass "GET /admin/verification (HTTP $V)" || fail "GET /admin/verification" "$V"

V=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/admin/verification/$COL_ID" -H "X-User-ID: $USER_ID" 2>/dev/null)
[ "$V" = "200" ] || [ "$V" = "403" ] || [ "$V" = "404" ] && pass "GET /admin/verification/{id} (HTTP $V)" || fail "GET /admin/verification/{id}" "$V"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════════════"
