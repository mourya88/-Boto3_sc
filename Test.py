import boto3
import json
import os, sys, time

# --- Config (Replace placeholders) ---
PRODUCT_NAME = "core-vpc"
DESIRED_VERSION = "v20"
ENVNAME = os.getenv("ENVNAME")
AWS_CREDS = os.getenv("AWS_CREDS")
PROVISIONED_NAME = PRODUCT_NAME + "-" + ENVNAME

def create_session():
    # Load credentials from BLZ CLI PATH
    print(f"file_path: {AWS_CREDS}")
    with open(AWS_CREDS) as f:
        credentials = json.load(f)
    session = boto3.Session(
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_access_key_id=credentials["AccessKeyId"],
        aws_session_token=credentials["SessionToken"],
        region_name="eu-west-2"
    )
    return session

def get_provisioning_artifact_id(product_name, desired_version):
    print(f"Fetching Provisioning Artifact ID for: {product_name}, version: {desired_version}")
    session = create_session()
    sc_client = session.client("servicecatalog")

    response = sc_client.search_products(
        Filters={"FullTextSearch": [product_name]}
    )

    product_id = None
    for product_view in response["ProductViewSummaries"]:
        if product_view["Name"] == product_name:
            product_id = product_view["ProductId"]
            print(f"ProductId: {product_id}")
            break

    if not product_id:
        raise ValueError(f"Product with name {product_name} not found!!!")

    artifacts = sc_client.list_provisioning_artifacts(ProductId=product_id)
    for artifact in artifacts["ProvisioningArtifactDetails"]:
        if artifact["Name"] == desired_version:
            print(f"Artifact ID is: {artifact['Id']}, version: {desired_version}")
            return artifact["Id"]

    raise Exception(f"Provisioning artifact version {desired_version} not found.")

def load_parameters(file_path="scripts/core-vpc.json"):
    with open(file_path) as f:
        return json.load(f)

def parameters_changed(existing_params, desired_params):
    # Compare keys/values between current provisioned and desired params
    existing_dict = {p["Key"]: p["Value"] for p in existing_params}
    desired_dict = {p["Key"]: p["Value"] for p in desired_params}
    return existing_dict != desired_dict

def provision_product(product_name, artifact_id, name):
    print(f"Initialize Service Catalog product - {product_name}")
    session = create_session()
    sc_client = session.client("servicecatalog")

    # Load parameters from local json file
    file_path = "scripts/core-vpc.json"
    with open(file_path) as f:
        parameters = json.load(f)

    print("Loaded Provisioned Parameters:")
    for p in parameters:
        print(f" - {p['Key']}: {p['Value']}")

    # Check if product is already provisioned
    try:
        describe_response = sc_client.describe_provisioned_product(Name=name)
        provisioned = True
        existing_artifact_id = describe_response["ProvisionedProductDetail"]["ProvisioningArtifactId"]
        print(f"Existing provisioned product found: {name}")
    except sc_client.exceptions.ResourceNotFoundException:
        provisioned = False
        print(f"No existing product named {name}, provisioning new one.")

    # Compare artifact version and parameters only if already provisioned
    if provisioned:
        artifact_needs_update = (artifact_id != existing_artifact_id)

        describe_outputs = sc_client.describe_provisioning_parameters(
            ProductId=describe_response["ProvisionedProductDetail"]["ProductId"],
            ProvisioningArtifactId=existing_artifact_id
        )
        current_params = describe_outputs.get("ProvisioningArtifactParameters", [])
        params_need_update = parameters_changed(current_params, parameters)

        if artifact_needs_update or params_need_update:
            print("Changes detected, updating provisioned product...")
            response = sc_client.update_provisioned_product(
                ProvisionedProductName=name,
                ProvisioningArtifactId=artifact_id,
                ProvisioningParameters=parameters
            )
        else:
            print("No update needed. Product is up to date.")
            return True
    else:
        # New provision
        response = sc_client.provision_product(
            ProductName=product_name,
            ProvisioningArtifactId=artifact_id,
            ProvisionedProductName=name,
            ProvisioningParameters=parameters
        )

    # Poll until provision or update is done
    record_id = response["RecordDetail"]["RecordId"]
    print(f"Provisioning/Update initiated for RecordID: {record_id}")

    poll_interval = 30
    while True:
        time.sleep(poll_interval)
        describe_response = sc_client.describe_record(Id=record_id)
        status = describe_response["RecordDetail"]["Status"]
        print(f"Current Status: {status}")

        if status == "SUCCEEDED":
            print("Product Successfully Provisioned/Updated")
            return True
        elif status in ("FAILED", "ERROR"):
            print("Product Provisioning Failed")
            print("Failure Reason:", describe_response["RecordDetail"].get("FailureReason", "No reason provided"))
            return False

if __name__ == "__main__":
    ARTIFACT_ID = get_provisioning_artifact_id(PRODUCT_NAME, DESIRED_VERSION)
    provision_product(PRODUCT_NAME, ARTIFACT_ID, PROVISIONED_NAME)
