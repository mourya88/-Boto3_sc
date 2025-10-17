resource "aws_cloudwatch_event_rule" "ssm_change_linux" {
  name        = "ssm-linux-ami-change"
  description = "Trigger Lambda when Linux SSM Parameter is updated"
  event_pattern = <<EOF
{
  "source": ["aws.ssm"],
  "detail-type": ["Parameter Store Change"],
  "detail": {
    "name": ["/ami-refresh/linux/latest-ami"],
    "operation": ["Update"]
  }
}
EOF
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.ssm_change_linux.name
  target_id = "asg-refresh"
  arn       = aws_lambda_function.asg_refresh.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeLinux"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.asg_refresh.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ssm_change_linux.arn
}

import boto3
import os

def lambda_handler(event, context):
    ssm = boto3.client("ssm")
    ec2 = boto3.client("ec2")
    asg = boto3.client("autoscaling")

    # Event carries parameter name
    param_name = event["detail"]["name"]

    # Get latest AMI from SSM parameter
    response = ssm.get_parameter(Name=param_name)
    latest_ami = response["Parameter"]["Value"]
    print(f"Updated AMI from {param_name}: {latest_ami}")

    # Get ASG and Launch Template from environment variables
    asg_name = os.environ["ASG_NAME"]
    lt_id = os.environ["LT_ID"]

    # Create new LT version with updated AMI
    lt_version = ec2.create_launch_template_version(
        LaunchTemplateId=lt_id,
        SourceVersion="$Latest",
        LaunchTemplateData={
            "ImageId": latest_ami
        }
    )
    new_version = lt_version["LaunchTemplateVersion"]["VersionNumber"]
    print(f"Created new Launch Template version: {new_version}")

    # Set new version as default
    ec2.modify_launch_template(
        LaunchTemplateId=lt_id,
        DefaultVersion=str(new_version)
    )
    print(f"Set LT {lt_id} default version to {new_version}")

    # Start ASG Instance Refresh
    refresh = asg.start_instance_refresh(
        AutoScalingGroupName=asg_name,
        Preferences={
            "MinHealthyPercentage": 90,
            "InstanceWarmup": 300
        }
    )
    print(f"Triggered ASG Instance Refresh: {refresh['InstanceRefreshId']}")

    return {
        "statusCode": 200,
        "body": f"ASG {asg_name} refreshed with AMI {latest_ami}"
    }
