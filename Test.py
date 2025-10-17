import boto3
import os
import json

def lambda_handler(event, context):
    # Print the full event payload for debugging
    print("=== Incoming Event ===")
    print(json.dumps(event, indent=2))

    # Initialize boto3 clients
    ssm = boto3.client("ssm")
    ec2 = boto3.client("ec2")
    asg = boto3.client("autoscaling")

    try:
        # Extract parameter name from event
        param_name = event["detail"]["name"]
        print(f"[INFO] Parameter updated: {param_name}")

        # Get latest AMI from SSM parameter
        response = ssm.get_parameter(Name=param_name)
        latest_ami = response["Parameter"]["Value"]
        print(f"[INFO] Latest AMI value fetched: {latest_ami}")

        # Get ASG + Launch Template from environment variables
        asg_name = os.environ["ASG_NAME"]
        lt_id = os.environ["LT_ID"]
        print(f"[INFO] Target ASG: {asg_name}, Launch Template: {lt_id}")

        # Create new Launch Template version with updated AMI
        lt_version = ec2.create_launch_template_version(
            LaunchTemplateId=lt_id,
            SourceVersion="$Latest",
            LaunchTemplateData={
                "ImageId": latest_ami
            }
        )
        new_version = lt_version["LaunchTemplateVersion"]["VersionNumber"]
        print(f"[SUCCESS] Created new LT version {new_version} with AMI {latest_ami}")

        # Set new version as default
        ec2.modify_launch_template(
            LaunchTemplateId=lt_id,
            DefaultVersion=str(new_version)
        )
        print(f"[SUCCESS] Set LT {lt_id} default version to {new_version}")

        # Start ASG Instance Refresh
        refresh = asg.start_instance_refresh(
            AutoScalingGroupName=asg_name,
            Preferences={
                "MinHealthyPercentage": 90,
                "InstanceWarmup": 300
            }
        )
        print(f"[SUCCESS] Triggered ASG Instance Refresh: {refresh['InstanceRefreshId']}")

        return {
            "statusCode": 200,
            "body": f"ASG {asg_name} refreshed with AMI {latest_ami}"
        }

    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
