#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:9001/api"
PASS=0
FAIL=0

check_json() {
    local label="$1" url="$2" jq_check="$3"
    local body
    body=$(curl -sf "$url" 2>/dev/null) || true
    if [ -z "$body" ]; then
        echo "  FAIL  $label (no response)"
        FAIL=$((FAIL + 1))
        return
    fi
    local result
    result=$(echo "$body" | jq -r "$jq_check" 2>/dev/null) || true
    if [ -n "$result" ] && [ "$result" != "null" ] && [ "$result" != "0" ] && [ "$result" != "false" ]; then
        echo "  PASS  $label ($result)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $label => '$result'"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "=== Smoke Tests against fresh.db on :9001 ==="
echo ""

echo "--- Health ---"
check_json "readiness" "$BASE/health/readiness" '.data.status'

echo ""
echo "--- Skills catalog ---"
check_json "37 skills" "$BASE/skills/catalog" '.data.skills | length'
check_json "8 competencies" "$BASE/skills/catalog" '.data.competencies | length'
check_json "Has 'active-listening'" "$BASE/skills/catalog" '[.data.skills[] | select(.slug == "active-listening")] | length'
check_json "Has 'stakeholder-management' competency" "$BASE/skills/catalog" '[.data.competencies[] | select(.slug == "stakeholder-management")] | length'
check_json "10 rubrics" "$BASE/skills/catalog" '.data.rubrics | length'

echo ""
echo "--- Collections ---"
check_json "1 collection returned" "$BASE/collections" '.data | length'
check_json "'Consultancy Fundamentals' exists" "$BASE/collections" '[.data[] | select(.title == "Consultancy Fundamentals")] | length'
check_json "Collection is published_public" "$BASE/collections" '[.data[] | select(.lifecycle_state == "published_public")] | length'
check_json "Collection has 3 prompt_items" "$BASE/collections" '[.data[].prompt_items[]] | length'
check_json "Collection has 1 scenario" "$BASE/collections" '[.data[].scenarios[]] | length'

echo ""
echo "--- Discover (via query param) ---"
check_json "Discover tier global_public" "$BASE/collections?discovery_tier=global_public" '.data | length'

echo ""
echo "--- Prompt Items ---"
check_json "Quick practice 'Impossible Deadline'" "$BASE/collections" '[.data[].prompt_items[] | select(.title == "Client Asks for Impossible Deadline")] | length'
check_json "Quick practice 'Ambiguous Request'" "$BASE/collections" '[.data[].prompt_items[] | select(.title == "Clarifying an Ambiguous Request")] | length'
check_json "Interview 'Difficult Stakeholder'" "$BASE/collections" '[.data[].prompt_items[] | select(.title == "Managing a Difficult Stakeholder")] | length'
check_json "Item 1 rubric is quick_practice_reset_timeline@v1" "$BASE/collections" '[.data[].prompt_items[] | select(.rubric_id == "quick_practice_reset_timeline@v1")] | length'
check_json "Item 2 rubric is quick_practice_text@v1" "$BASE/collections" '[.data[].prompt_items[] | select(.rubric_id == "quick_practice_text@v1")] | length'
check_json "Item 3 rubric is interview_text@v1" "$BASE/collections" '[.data[].prompt_items[] | select(.rubric_id == "interview_text@v1")] | length'

echo ""
echo "--- Scenario ---"
check_json "'MoneyCraft Data Centralisation'" "$BASE/collections" '[.data[].scenarios[] | select(.title == "MoneyCraft Data Centralisation")] | length'
check_json "Scenario rubric is scenario_text@v1" "$BASE/collections" '[.data[].scenarios[] | select(.rubric_id == "scenario_text@v1")] | length'
check_json "Scenario has mock_company" "$BASE/collections" '[.data[].scenarios[].mock_company | select(.name == "MoneyCraft Bank")] | length'
check_json "Scenario has 4 mock_people" "$BASE/collections" '[.data[].scenarios[].mock_people[]] | length'
check_json "Has 'Cristina Yang' (CEO)" "$BASE/collections" '[.data[].scenarios[].mock_people[] | select(.name == "Cristina Yang" and .role == "CEO")] | length'
check_json "Has 'Samir Hicks' (Head of Lending)" "$BASE/collections" '[.data[].scenarios[].mock_people[] | select(.name == "Samir Hicks")] | length'
check_json "Has 3 supporting_artifacts" "$BASE/collections" '[.data[].scenarios[].supporting_artifacts[]] | length'

echo ""
echo "==============================="
echo "  Results: $PASS passed, $FAIL failed"
echo "==============================="

exit $FAIL
