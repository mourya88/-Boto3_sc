import boto3
import os

def lambda_handler(event, context):
    ssm = boto3.client("ssm")
    ec2 = boto3.client("ec2")
    asg = boto3.client("autoscaling")

    asg_name = os.environ["ASG_NAME"]
    lt_id = os.environ["LT_ID"]

    # Event contains updated parameter name
    param_name = event["detail"]["name"]

    # Get latest AMI from SSM
    latest_ami = ssm.get_parameter(Name=param_name)["Parameter"]["Value"]
    print(f"Parameter {param_name} updated → AMI {latest_ami}")

    # Create new Launch Template version with updated AMI
    lt_version = ec2.create_launch_template_version(
        LaunchTemplateId=lt_id,
        SourceVersion="$Latest",
        LaunchTemplateData={
            "ImageId": latest_ami
        }
    )
    new_version = lt_version["LaunchTemplateVersion"]["VersionNumber"]
    print(f"Created new LT version {new_version} with AMI {latest_ami}")

    # Set new version as default
    ec2.modify_launch_template(
        LaunchTemplateId=lt_id,
        DefaultVersion=str(new_version)
    )
    print(f"Updated LT {lt_id} default version to {new_version}")

    # Trigger ASG Instance Refresh
    response = asg.start_instance_refresh(
        AutoScalingGroupName=asg_name,
        Preferences={
            "MinHealthyPercentage": 50,   # ensures zero downtime
            "InstanceWarmup": 60
        }
    )
    print(f"Started Instance Refresh {response['InstanceRefreshId']} for {asg_name}")
    return response
