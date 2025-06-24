import boto3
import json
import os, sys

# --- Config ---
PRODUCT_NAME = "core-vpc"
DESIRED_VERSION = "v1.0.0"  # Replace with your actual version
ENVNAME = os.getenv("ENVNAME")
PROFILE = os.getenv("PROFILE")
AWS_CREDS = os.getenv("AWS_CREDS")
PROVISIONED_NAME = PRODUCT_NAME + "-" + ENVNAME

def load_credentials(file_path=f".blz/cache/{PROFILE}.json"):
    with open(file_path) as f:
        return json.load(f)

def create_session():
    credentials = load_credentials()
    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name="eu-west-2"
    )
    return session

def load_parameters(file_path="scripts/core-vpc.json"):
    with open(file_path) as f:
        return json.load(f)

def get_provisioning_artifact_id(product_name, desired_version):
    print(f"Fetching Provisioning Artifact ID for: {product_name}, version: {desired_version}")
    session = create_session()
    sc_client = session.client("servicecatalog")

    response = sc_client.search_products_as_admin(
        Filters={"FullTextSearch": [product_name]},
        SortBy='Title',
        SortOrder='ASCENDING'
    )

    for product_view in response["ProductViewDetails"]:
        if product_view["ProductViewSummary"]["Name"] == product_name:
            product_id = product_view["ProductViewSummary"]["ProductId"]
            artifacts = sc_client.list_provisioning_artifacts(ProductId=product_id)
            for artifact in artifacts["ProvisioningArtifactDetails"]:
                if artifact["Name"] == desired_version:
                    return artifact["Id"]
            raise Exception(f"Provisioning artifact version '{desired_version}' not found.")
    
    raise Exception(f"Product '{product_name}' not found.")

def provision_product(product_name, artifact_id, name):
    print(f"Initialize Service Catalog product: {product_name}")
    session = create_session()
    sc_client = session.client("servicecatalog")
    parameters = load_parameters()

    print("Loaded Provisioned Parameters:")
    for p in parameters:
        print(f"  - {p['Key']}: {p['Value']}")

    response = sc_client.provision_product(
        ProductName=product_name,
        ProvisioningArtifactId=artifact_id,
        ProvisionedProductName=name,
        ProvisioningParameters=parameters
    )

    print("Provisioning started. Response:")
    print(response)

# Run logic
if __name__ == "__main__":
    artifact_id = get_provisioning_artifact_id(PRODUCT_NAME, DESIRED_VERSION)
    provision_product(PRODUCT_NAME, artifact_id, PROVISIONED_NAME)
