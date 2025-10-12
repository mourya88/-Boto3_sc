import os
import boto3


def lambda_handler(event, context):
    """
    Trigger an Auto Scaling Group instance refresh whenever an SSM Parameter changes.
    Env vars:
      - ASG_NAME       : target ASG name (e.g., demo-asg)
      - LINUX_PARAM    : /ami-refresh/linux/latest-ami
      - WINDOWS_PARAM  : /ami-refresh/windows/latest-ami
    EventBridge will pass the parameter name in event['detail']['name'].
    """
    ssm = boto3.client("ssm")
    asg = boto3.client("autoscaling")

    asg_name = os.environ["ASG_NAME"]
    linux_param = os.environ.get("LINUX_PARAM")
    windows_param = os.environ.get("WINDOWS_PARAM")

    # EventBridge Parameter Store change event
    detail = event.get("detail", {})
    param_name = detail.get("name")

    if not param_name:
        print("No parameter change detected in event; nothing to do.")
        return {"statusCode": 200, "body": "No parameter change detected"}

    if linux_param and param_name != linux_param and windows_param and param_name != windows_param:
        # If you only want to react to the two specific params, keep this guard:
        print(f"Ignoring change to unrelated parameter: {param_name}")
        return {"statusCode": 200, "body": "Irrelevant parameter change"}

    # Read the new AMI ID from SSM
    latest_ami = ssm.get_parameter(Name=param_name)["Parameter"]["Value"]
    print(f"SSM parameter '{param_name}' updated to AMI '{latest_ami}'")

    # Start a rolling refresh (keeps at least 50% healthy, 60s warmup)
    resp = asg.start_instance_refresh(
        AutoScalingGroupName=asg_name,
        Preferences={
            "MinHealthyPercentage": 50,
            "InstanceWarmup": 60
        }
    )

    refresh_id = resp.get("InstanceRefreshId")
    print(f"Triggered ASG refresh '{refresh_id}' for '{asg_name}'")
    return {"statusCode": 200, "body": f"ASG refresh started: {refresh_id}"}
