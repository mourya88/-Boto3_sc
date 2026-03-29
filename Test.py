
page=1

while true; do
  echo "Fetching page $page..."

  response=$(curl -s -k -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$GITLAB_BASE_URL/api/v4/projects/$PROJECT_PATH/repository/branches?per_page=$PER_PAGE&page=$page")

  if [[ "$response" == "[]" ]]; then
    echo "No more pages. Stopping."
    break
  fi

  echo "$response" | jq -c '.[]' | while read -r branch; do
    branch_name=$(echo "$branch" | jq -r '.name')
    last_commit_date=$(echo "$branch" | jq -r '.commit.committed_date')
    last_commit_author=$(echo "$branch" | jq -r '.commit.author_name')
    last_commit_author_email=$(echo "$branch" | jq -r '.commit.author_email')
    protected=$(echo "$branch" | jq -r '.protected')
    default_branch=$(echo "$branch" | jq -r '.default')

    encoded_branch_name=$(printf '%s' "$branch_name" | jq -sRr @uri)

    mr_response=$(curl -s -k -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      "$GITLAB_BASE_URL/api/v4/projects/$PROJECT_PATH/merge_requests?state=opened&source_branch=$encoded_branch_name")

    mr_count=$(echo "$mr_response" | jq 'length')

    if [[ "$mr_count" -gt 0 ]]; then
      open_mr="yes"
    else
      open_mr="no"
    fi

    printf '"%s","%s","%s","%s","%s","%s","%s","%s"\n' \
      "$PROJECT_NAME" \
      "$branch_name" \
      "$last_commit_date" \
      "$last_commit_author" \
      "$last_commit_author_email" \
      "$protected" \
      "$default_branch" \
      "$open_mr" \
      >> "$OUTPUT_FILE"
  done

  page=$((page + 1))
done
