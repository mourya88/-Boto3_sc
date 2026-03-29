    protected_lower=$(echo "$protected" | tr '[:upper:]' '[:lower:]')
    default_lower=$(echo "$default_branch" | tr '[:upper:]' '[:lower:]')

    if [[ "$default_lower" == "true" ]]; then
      stale_status="active"
      skip_reason="default_branch"
    elif [[ "$protected_lower" == "true" ]]; then
      stale_status="active"
      skip_reason="protected_branch"
    elif [[ "$open_mr" == "yes" ]]; then
      stale_status="active"
      skip_reason="open_merge_request"
    else
      commit_epoch=$(date -d "$last_commit_date" +%s 2>/dev/null || echo 0)
      current_epoch=$(date +%s)
      age_days=$(( (current_epoch - commit_epoch) / 86400 ))

      if [[ "$commit_epoch" -eq 0 ]]; then
        stale_status="unknown"
        skip_reason="invalid_commit_date"
      elif [[ "$age_days" -ge "$STALE_DAYS" ]]; then
        stale_status="stale"
        skip_reason=""
      else
        stale_status="active"
        skip_reason="recent_commit"
      fi
    fi


printf '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' \
  "$PROJECT_NAME" \
  "$branch_name" \
  "$last_commit_date" \
  "$last_commit_author" \
  "$last_commit_author_email" \
  "$protected" \
  "$default_branch" \
  "$open_mr" \
  "$stale_status" \
  "$skip_reason" \
  >> "$OUTPUT_FILE"

