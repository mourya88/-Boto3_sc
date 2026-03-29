stages:
  - report

stale-branch-report:
  stage: report
  image: alpine:3.20

  variables:
    GITLAB_BASE_URL: "https://app.gitlab.barcapint.com"
    PER_PAGE: "100"
    STALE_DAYS: "90"
    OUTPUT_FILE: "branch_report_stale.csv"

  before_script:
    - apk add --no-cache bash curl jq coreutils

  script:
    - echo "Running stale branch report"
    - echo "TARGET_PROJECT=$TARGET_PROJECT"
    - echo "PROJECT_NAME=$PROJECT_NAME"
    - echo "STALE_DAYS=$STALE_DAYS"
    - echo "PER_PAGE=$PER_PAGE"
    - chmod +x scripts/branchreporststalepara.sh
    - ./scripts/branchreporststalepara.sh

  artifacts:
    when: always
    expire_in: 7 days
    paths:
      - branch_report_stale.csv

  rules:
    - if: '$CI_PIPELINE_SOURCE == "web"'
      when: manual
    - when: never
