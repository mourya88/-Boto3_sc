#!/bin/bash

set -euo pipefail

# =========================
# Configuration
# =========================
GITLAB_BASE_URL="https://app.gitlab.barcapint.com"
PROJECT_NAME="test-bmb-funds-transfer-xapi"
PROJECT_PATH="barclays%2Femm-digital-payments%2Ftest-bmb-funds-transfer-xapi"
PER_PAGE=20
TOTAL_PAGES=9
OUTPUT_FILE="branch_report.csv"

# =========================
# Token check
# =========================
if [[ -z "${GITLAB_TOKEN:-}" ]]; then
  echo "ERROR: GITLAB_TOKEN environment variable is not set."
  echo "Please run:"
  echo 'export GITLAB_TOKEN="your_new_token_here"'
  exit 1
fi

# =========================
# Create CSV header
# =========================
echo 'project,branch_name,last_commit_date,last_commit_author,last_commit_author_email,protected,default' > "$OUTPUT_FILE"

# =========================
# Fetch branch data page by page
# =========================
for page in $(seq 1 "$TOTAL_PAGES"); do
  echo "Fetching page $page of $TOTAL_PAGES..."

  response=$(curl -s -k -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$GITLAB_BASE_URL/api/v4/projects/$PROJECT_PATH/repository/branches?per_page=$PER_PAGE&page=$page")

  echo "$response" | jq -r --arg project "$PROJECT_NAME" '
    .[] | [
      $project,
      .name,
      .commit.committed_date,
      .commit.author_name,
      .commit.author_email,
      .protected,
      .default
    ] | @csv
  ' >> "$OUTPUT_FILE"
done

echo "Branch report created successfully: $OUTPUT_FILE"
