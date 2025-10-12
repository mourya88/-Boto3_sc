import boto3
import os

ec2 = boto3.client("ec2")
ssm = boto3.client("ssm")

def lambda_handler(event, context):
    # Example: look for AMIs with a given pattern (Linux)
    linux_param = os.environ.get("LINUX_PARAM", "/ami-refresh/linux/latest-ami")
    windows_param = os.environ.get("WINDOWS_PARAM", "/ami-refresh/windows/latest-ami")

    # Get latest Linux AMI
    linux_images = ec2.describe_images(
        Owners=["self"],
        Filters=[{"Name": "name", "Values": ["amirefresh-linux-*"]}]
    )["Images"]

    if linux_images:
        latest_linux = sorted(linux_images, key=lambda x: x["CreationDate"], reverse=True)[0]
        ssm.put_parameter(
            Name=linux_param,
            Value=latest_linux["ImageId"],
            Type="String",
            Overwrite=True
        )

    # Get latest Windows AMI
    windows_images = ec2.describe_images(
        Owners=["self"],
        Filters=[{"Name": "name", "Values": ["amirefresh-window-*"]}]
    )["Images"]

    if windows_images:
        latest_windows = sorted(windows_images, key=lambda x: x["CreationDate"], reverse=True)[0]
        ssm.put_parameter(
            Name=windows_param,
            Value=latest_windows["ImageId"],
            Type="String",
            Overwrite=True
        )

    return {
        "statusCode": 200,
        "body": "SSM parameters updated with latest AMIs"
    }
