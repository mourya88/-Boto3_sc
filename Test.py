]{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<source-account-id>:role/<source-role-name>"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
