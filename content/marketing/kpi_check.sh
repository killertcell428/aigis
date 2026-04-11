#!/bin/bash
# AI Guardian KPI Quick Check
# Usage: bash content/marketing/kpi_check.sh

echo "=== AI Guardian KPI Dashboard ==="
echo "Date: $(date +%Y-%m-%d)"
echo ""

echo "--- GitHub ---"
echo "Stars: $(gh api repos/killertcell428/ai-guardian --jq '.stargazers_count')"
echo "Forks: $(gh api repos/killertcell428/ai-guardian --jq '.forks_count')"
echo "Open Issues: $(gh issue list --state open --json number --repo killertcell428/ai-guardian | python -c 'import sys,json;print(len(json.load(sys.stdin)))')"
echo "Open PRs: $(gh pr list --state open --json number --repo killertcell428/ai-guardian | python -c 'import sys,json;print(len(json.load(sys.stdin)))')"
echo ""

echo "--- Traffic (14 days) ---"
gh api repos/killertcell428/ai-guardian/traffic/views --jq '"Views: \(.count) (unique: \(.uniques))"'
gh api repos/killertcell428/ai-guardian/traffic/clones --jq '"Clones: \(.count) (unique: \(.uniques))"'
echo ""

echo "--- Latest Release ---"
gh release list --limit 3 --repo killertcell428/ai-guardian
echo ""

echo "--- PyPI ---"
echo "Check: https://pepy.tech/projects/aig-guardian"
echo ""

echo "--- PH Launch Countdown ---"
LAUNCH=$(date -d "2026-05-13" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "2026-05-13" +%s 2>/dev/null)
NOW=$(date +%s)
DAYS=$(( (LAUNCH - NOW) / 86400 ))
echo "Days until PH launch (5/13): $DAYS days"
