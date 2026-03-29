# =========================
# Configuration
# =========================
GITLAB_BASE_URL="${GITLAB_BASE_URL:-https://app.gitlab.barcapint.com}"
TARGET_PROJECT="${TARGET_PROJECT:-}"
PROJECT_NAME="${PROJECT_NAME:-}"
PER_PAGE="${PER_PAGE:-100}"
OUTPUT_FILE="${OUTPUT_FILE:-branch_report_stale.csv}"
STALE_DAYS="${STALE_DAYS:-90}"



if [[ -z "$TARGET_PROJECT" ]]; then
  echo "ERROR: TARGET_PROJECT is required."
  echo 'Example: export TARGET_PROJECT="barclays/emm-digital-payments/test-bmb-funds-transfer-xapi"'
  exit 1
fi

# If TARGET_PROJECT is numeric, treat it as project ID.
# Otherwise, URL-encode it as project path.
if [[ "$TARGET_PROJECT" =~ ^[0-9]+$ ]]; then
  PROJECT_REF="$TARGET_PROJECT"
else
  PROJECT_REF=$(printf '%s' "$TARGET_PROJECT" | jq -sRr @uri)
fi

# If PROJECT_NAME is not provided, derive it from TARGET_PROJECT
if [[ -z "$PROJECT_NAME" ]]; then
  PROJECT_NAME=$(basename "$TARGET_PROJECT")
fi
